from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings

settings = get_settings()

DATABASE_URL = settings.database_url
# Render persistent disk support for SQLite
if settings.env.lower() == "prod" and "sqlite" in DATABASE_URL and "./unthinkable.db" in DATABASE_URL:
    DATABASE_URL = "sqlite:////var/data/unthinkable.db"

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database on startup:
    1. Create all tables
    2. Clear shopping_items table (temporary session data)
    3. Keep user_history table (persistent)
    """
    Base.metadata.create_all(bind=engine)
    
    # Clear shopping_items table on startup
    db = SessionLocal()
    try:
        from models import ShoppingItem
        db.execute(delete(ShoppingItem))
        db.commit()
    finally:
        db.close()
