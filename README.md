# Voice Command Shopping Assistant

Production-quality technical assessment project.

## Backend (FastAPI + SQLite)

### Folder
- `backend/`

### Setup + run locally (Windows PowerShell)

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Environment variables (optional)
- **`CORS_ALLOW_ORIGINS`**: comma-separated list. Default `*`.
- **`DATABASE_URL`**: default `sqlite:///./unthinkable.db`
- **`OPENAI_API_KEY`**: enable OpenAI parsing
- **`ENABLE_OPENAI_PARSER`**: set `true` to enable OpenAI parsing
- **`OPENAI_MODEL`**: default `gpt-4o-mini`

### Endpoints
- `POST /process-voice`
- `POST /search`
- `GET /recommendations`
- `GET /items`
- `DELETE /items/{id}`

### Example requests

```bash
curl -X POST "http://127.0.0.1:8000/process-voice" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Buy 2 bottles of water\"}"
```

```bash
curl -X POST "http://127.0.0.1:8000/process-voice" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"Busca leche hasta 5\"}"
```

## Frontend (Flutter Mobile)

### Folder
- `frontend/flutter_app/` (core app files)

### Create a runnable Flutter project
From the repo root:

```bash
flutter create frontend_app
```

Then copy/replace:
- `frontend/flutter_app/pubspec.yaml` → `frontend_app/pubspec.yaml`
- `frontend/flutter_app/analysis_options.yaml` → `frontend_app/analysis_options.yaml`
- `frontend/flutter_app/lib/*` → `frontend_app/lib/*`

### Microphone permissions (required)
In the generated project:
- **Android**: add `<uses-permission android:name="android.permission.RECORD_AUDIO" />`
  in `android/app/src/main/AndroidManifest.xml`
- **iOS**: add `NSMicrophoneUsageDescription` to `ios/Runner/Info.plist`

### Run (emulator)
Ensure backend is running on port 8000.

- **Android emulator** uses `http://10.0.2.2:8000` (already default in `lib/main.dart`)
- **iOS simulator** uses `http://127.0.0.1:8000`

```bash
cd frontend_app
flutter pub get
flutter run
```

### Build APK

```bash
cd frontend_app
flutter build apk --release
```

## Deployment

### Deploy backend to Render
- Create a new **Web Service**
- Root directory: `backend`
- Build command:

```bash
pip install -r requirements.txt
```

- Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

- Set env:
  - `CORS_ALLOW_ORIGINS` to your app origins (or `*` for demo)
  - Optional `DATABASE_URL` (SQLite works, but a persistent disk is recommended)

### Deploy backend to Railway
- New project → Deploy from repo
- Service root: `backend`
- Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Connect Flutter to deployed backend
In `frontend/flutter_app/lib/main.dart`, change `baseUrl` (or pass via `--dart-define`):

```bash
flutter run --dart-define=API_BASE_URL=https://YOUR-DEPLOYED-BACKEND
```

## Submission explanation (≈200 words)

This project implements a Voice Command Shopping Assistant with a hosting-ready FastAPI backend and a minimalist Flutter mobile UI. The backend exposes endpoints for voice processing, search, shopping list CRUD, and recommendations. Voice commands are parsed into a strict JSON schema (`action`, `item`, `quantity`, `category`, and `filters`) using a rule-based multilingual NLP pipeline (English + Spanish). It supports varied phrasing, quantity extraction (digits and basic number words), brand filters (e.g., “brand X” / “marca X”), and price ceilings (e.g., “under 5” / “hasta 5”). For higher accuracy, an optional OpenAI parser can be enabled via environment variables; if disabled or unavailable the rule-based parser remains fully functional.

Shopping list persistence uses SQLite with SQLAlchemy models and a small, clean module layout (`database.py`, `models.py`, `schemas.py`, `nlp_parser.py`, `recommendation.py`, `main.py`). Smart suggestions are returned with each voice response and include frequency-based items from shopping history, seasonal recommendations based on month, and substitutes via a lightweight mapping dictionary. Voice search uses a mock product dataset (`mock_products.json`) and applies filters server-side. The Flutter client uses `speech_to_text` for live speech recognition and `provider` for state management, showing real-time transcript, loading/error states, the current shopping list, and suggestion chips, providing a simple assessment-ready UX.
