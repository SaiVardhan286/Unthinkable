"""
Voice Command Shopping Assistant – FastAPI Backend
Run: uvicorn main:app --reload
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config import get_settings
from database import engine, get_db, init_db
from models import ShoppingItem, UserHistory
from nlp_parser import parse_voice_command
from recommendation import RecommendationService, build_suggestions
from schemas import (
    Filters,
    ModifyItemRequest,
    SearchRequest,
    SearchResponse,
    ShoppingItemOut,
    VoiceRequest,
)

settings = get_settings()

# Basic logging configuration; in production you would adapt this to your log stack.
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(message)s",
)
logger = logging.getLogger("api")


class AppValidationError(HTTPException):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=message)


def _standard_error_response(message: str, error_code: str = "VALIDATION_ERROR") -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error_code": error_code,
            "message": message,
        },
    )


class LoggingRoute(APIRoute):
    """
    Route subclass that adds per-request structured logging.
    """

    def get_route_handler(self):
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request):
            request_id = str(uuid4())
            start = time.perf_counter()
            try:
                response = await original_route_handler(request)
                status_code = getattr(response, "status_code", 500)
            except Exception as exc:  # pragma: no cover - defensive
                status_code = 500
                logger.exception("Unhandled error", extra={"request_id": request_id})
                raise exc
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.info(
                    json.dumps(
                        {
                            "type": "request",
                            "request_id": request_id,
                            "path": request.url.path,
                            "method": request.method,
                            "status_code": status_code,
                            "latency_ms": round(elapsed_ms, 2),
                        }
                    )
                )

            response.headers["X-Request-ID"] = request_id
            return response

        return custom_route_handler


app = FastAPI(
    title="Unthinkable API",
    description="Voice Command Shopping Assistant backend",
    version="1.0.0",
    default_route_class=LoggingRoute,
)

# ── CORS (allow Flutter / web client) ────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.exception_handler(AppValidationError)
async def app_validation_exception_handler(request: Request, exc: AppValidationError) -> JSONResponse:
    return _standard_error_response(str(exc.detail))


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Collapse Pydantic's detailed error structure into a simple, user-facing message.
    return _standard_error_response("Invalid request payload")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # pragma: no cover - safety net
    logger.exception("Unhandled exception", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred.",
        },
    )


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "Voice Command Shopping Assistant API"}


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
def ready() -> dict[str, str]:
    # Basic readiness: DB connectivity.
    try:
        with engine.connect() as conn:
            conn.execute(select(ShoppingItem).limit(1))
    except Exception:
        raise HTTPException(status_code=503, detail="Database not ready")
    return {"status": "ready"}


def _load_products() -> list[dict[str, Any]]:
    path = Path(__file__).parent / "mock_products.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


_PRODUCTS_CACHE: list[dict[str, Any]] | None = None


def _products() -> list[dict[str, Any]]:
    global _PRODUCTS_CACHE
    if _PRODUCTS_CACHE is None:
        _PRODUCTS_CACHE = _load_products()
    return _PRODUCTS_CACHE


def _search_products(query: str, filters: Filters) -> list[dict[str, Any]]:
    """
    Search products with support for fuzzy matching and all filters (brand, size, price).
    Uses SearchService for advanced matching.
    """
    from search_service import SearchService
    
    service = SearchService()
    return service.search(query, filters)


def _get_items(db: Session) -> list[ShoppingItem]:
    return db.execute(select(ShoppingItem).order_by(ShoppingItem.id.asc())).scalars().all()


def _touch_history(db: Session, item_name: str, action_type: str = "purchase") -> None:
    """
    Update user history with interaction counts.
    action_type can be "purchase" or "search"
    """
    name = item_name.strip().lower()
    if not name:
        return
    row = db.execute(select(UserHistory).where(UserHistory.item_name == name)).scalar_one_or_none()
    if row is None:
        if action_type == "purchase":
            row = UserHistory(item_name=name, purchase_count=1, search_count=0)
        else:
            row = UserHistory(item_name=name, purchase_count=0, search_count=1)
        db.add(row)
    else:
        if action_type == "purchase":
            row.purchase_count += 1
        else:
            row.search_count += 1
    db.commit()


class AppValidationError(Exception):
    pass

def _upsert_item(db: Session, name: str, quantity: int, category: str) -> None:
    if quantity <= 0 or quantity > 100:
        raise AppValidationError("Quantity must be between 1 and 100")
    norm = name.strip().lower()
    if not norm:
        raise HTTPException(status_code=400, detail="No item detected in voice command.")

    existing = db.execute(select(ShoppingItem).where(ShoppingItem.name == norm)).scalar_one_or_none()
    if existing:
        existing.quantity += max(1, quantity)
        existing.category = category or existing.category or "other"
        db.commit()
        return

    # Lookup product details from mock data (exact or partial match)
    brand = ""
    price = 0.0
    size = ""
    best_match = None
    for p in _products():
        p_name = p["name"].lower()
        if p_name == norm:
            best_match = p
            break
        elif norm in p_name or p_name in norm:
            # save partial match, but keep looking for exact match
            if not best_match:
                best_match = p
                
    if best_match:
        brand = best_match.get("brand", "")
        price = float(best_match.get("price", 0.0))
        size = best_match.get("size", "")

    db.add(ShoppingItem(
        name=norm,
        quantity=max(1, quantity),
        category=category or "other",
        brand=brand,
        price=price,
        size=size
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.execute(select(ShoppingItem).where(ShoppingItem.name == norm)).scalar_one()
        existing.quantity += max(1, quantity)
        # We don't overwrite brand/price if it already existed unless we want to, but standard upsert just adds quantity
        db.commit()


def _modify_item(db: Session, name: str, quantity: int, category: str = "") -> None:
    if quantity < 0 or quantity > 100:
        raise HTTPException(status_code=400, detail="Quantity must be between 0 and 100")
    norm = name.strip().lower()
    if not norm:
        raise HTTPException(status_code=400, detail="No item detected to modify.")
    existing = db.execute(select(ShoppingItem).where(ShoppingItem.name == norm)).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail=f"Item '{norm}' not found.")
    
    if quantity == 0:
        db.delete(existing)
    else:
        existing.quantity = quantity
        if category:
            existing.category = category
    db.commit()


def _remove_item(db: Session, name: str, quantity: int) -> None:
    norm = name.strip().lower()
    if not norm:
        return {
            "success": False,
            "error": {"error_code": "ITEM_NOT_FOUND", "message": "Item not in list"}
        }
    existing = db.execute(select(ShoppingItem).where(ShoppingItem.name == norm)).scalar_one_or_none()
    if not existing:
        return {
            "success": False,
            "error": {"error_code": "ITEM_NOT_FOUND", "message": "Item not in list"}
        }
    if quantity > 0 and existing.quantity > quantity:
        existing.quantity -= quantity
        db.commit()
        return {"success": True, "removed": quantity, "remaining": existing.quantity}
    else:
        db.delete(existing)
        db.commit()
        return {"success": True, "removed": existing.quantity, "remaining": 0}


@app.get("/items", response_model=list[ShoppingItemOut], tags=["shopping-list"])
def get_items(db: Session = Depends(get_db)):
    return _get_items(db)


@app.delete("/items/{id}", tags=["shopping-list"])
def delete_item(id: int, db: Session = Depends(get_db)):
    item = db.get(ShoppingItem, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    db.delete(item)
    db.commit()
    return {"status": "deleted", "id": id}


@app.post("/modify-item", response_model=list[ShoppingItemOut], tags=["shopping-list"])
def modify_item(req: ModifyItemRequest, db: Session = Depends(get_db)):
    """
    Modify quantity of an existing shopping list item.
    If quantity is 0 or negative, the item is deleted.
    Returns the updated shopping list.
    """
    norm_name = (req.item or "").strip().lower()
    if not norm_name:
        raise HTTPException(status_code=400, detail="Item name is required.")
    
    if req.quantity < 0 or req.quantity > 100:
        raise HTTPException(status_code=400, detail="Quantity must be between 0 and 100.")
    
    existing = db.execute(select(ShoppingItem).where(ShoppingItem.name == norm_name)).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail=f"Item '{norm_name}' not found.")
    
    if req.quantity == 0:
        db.delete(existing)
    else:
        existing.quantity = req.quantity
    
    db.commit()
    return _get_items(db)


@app.get("/recommendations", tags=["recommendations"])
def get_recommendations(db: Session = Depends(get_db)):
    items = _get_items(db)
    return build_suggestions(db, items)


@app.post("/search", response_model=SearchResponse, tags=["search"])
def search(req: SearchRequest, db: Session = Depends(get_db)):
    query = (req.query_text or "").strip()
    filters = Filters(brand=req.brand or "", price_max=req.price_max or 0)

    if req.voice_text.strip():
        parsed = parse_voice_command(req.voice_text)
        if parsed.action == "search":
            query = parsed.item or query
            filters = parsed.filters

    results = _search_products(query, filters)

    # If nothing matched, fall back to substitutes based on the query term.
    if not results and query:
        svc = RecommendationService.from_session(db)
        subs = svc.get_substitutes_for_query(query, limit=5)
        results = [{"name": s, "brand": "", "price": 0.0} for s in subs]

    return SearchResponse(query=query, filters=filters, results=results)


@app.post("/process-voice", tags=["voice"])
def process_voice(req: VoiceRequest, db: Session = Depends(get_db)):
    print("[PROCESS-VOICE] Incoming request:", req)
    try:
        parsed = parse_voice_command(req.text, language_hint=req.language)
        search_results: list[dict[str, Any]] = []
        suggestions = []
        error = None
        success = True

        # Check for invalid intent first
        if parsed.action == "invalid":
            return {
                "success": False,
                "error": {"error_code": "INVALID_COMMAND", "message": "Could not understand command"},
                "parsed": parsed.model_dump(),
                "items": [],
                "suggestions": {"previous": [], "seasonal": [], "substitutes": [], "all": []},
                "search_results": [],
            }

        if parsed.action == "add":
            # Validate item - allow if it's in categories or mock_products, otherwise add with suggestion
            from nlp.categories import CATEGORY_KEYWORDS
            import json
            import os
            # Load mock products
            mock_path = os.path.join(os.path.dirname(__file__), "mock_products.json")
            with open(mock_path, encoding="utf-8") as f:
                mock_products = [item["name"].lower() for item in json.load(f)]
            item_l = (parsed.item or "").lower().strip()
            
            # Check if item is in categories or mock_products (optional fuzzy match suggestion)
            valid = False
            for words in CATEGORY_KEYWORDS.values():
                if any(w in item_l for w in words):
                    valid = True
                    break
            if not valid and item_l in mock_products:
                valid = True
            
            # Always add the item (even if not in recognized list)
            try:
                _upsert_item(db, parsed.item, parsed.quantity, parsed.category)
            except AppValidationError as e:
                success = False
                error = {"error_code": "VALIDATION_ERROR", "message": str(e)}
            
            _touch_history(db, parsed.item, action_type="purchase")
        elif parsed.action == "modify":
            try:
                _modify_item(db, parsed.item, parsed.quantity, parsed.category)
            except HTTPException as e:
                success = False
                error = {"error_code": "VALIDATION_ERROR", "message": str(e.detail)}
        elif parsed.action == "remove":
            remove_result = _remove_item(db, parsed.item, parsed.quantity)
            if remove_result and not remove_result.get("success", True):
                success = False
                error = remove_result.get("error")
        elif parsed.action == "search":
            search_results = _search_products(parsed.item, parsed.filters)
            _touch_history(db, parsed.item, action_type="search")
        else:
            return {
                "success": False,
                "error": {"error_code": "INVALID_COMMAND", "message": "Could not understand command"},
                "parsed": parsed.model_dump(),
                "items": [],
                "suggestions": {"previous": [], "seasonal": [], "substitutes": [], "all": []},
                "search_results": [],
            }

        items = _get_items(db)
        items_out = [ShoppingItemOut.from_orm(item) for item in items]
        suggestions = build_suggestions(db, items)
        
        # Build response in the format expected by frontend
        return {
            "success": success,
            "error": error,
            "parsed": parsed.model_dump(),
            "items": [item.model_dump() for item in items_out],
            "suggestions": suggestions.model_dump(),
            "search_results": search_results or [],
        }
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("/process-voice error:", tb)
        return {
            "success": False,
            "error": {"error_code": "INTERNAL_ERROR", "message": str(e)},
            "parsed": None,
            "items": [],
            "suggestions": {"previous": [], "seasonal": [], "substitutes": [], "all": []},
            "search_results": [],
        }
