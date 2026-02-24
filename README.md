🎙️ Voice Command Shopping Assistant

A production-ready full-stack application that allows users to manage their shopping list using natural voice commands in English and Spanish.

Users can say:

“Add 2 bottles of water”
“Remove one milk”
“Find toothpaste under 50”
“Busca leche hasta 5”

The system intelligently parses the command, updates the shopping list, applies filters, and provides smart recommendations.

🌐 Live Demo

Frontend (Main Application):
👉https://unthinkable-frontend.onrender.com

Backend API Docs:
👉 https://unthinkable-xaut.onrender.com/docs

⚠️ Note: The backend is hosted on Render Free Tier.
If inactive for ~15 minutes, the first request may take 20–40 seconds (cold start).
Subsequent requests are fast.

🏗️ Project Structure

Unthinkable/
│
├── backend/              # FastAPI backend
├── frontend/flutter_app  # Flutter source code
├── frontend_build/       # Production Flutter Web build (deployed)
└── README.md

🚀 Features

🧠 Smart Voice Parsing (Rule-Based NLP)

The built-in NLP engine extracts:
- Intent (Add / Remove / Search / Modify)
- Quantity
- Item name
- Brand (if mentioned)
- Price filters (e.g., “under 50”)

No external APIs are required.

🛒 Shopping List Management

- Add items using voice
- Remove items using voice
- Modify quantity
- Manual + / − quantity buttons
- Automatic item categorization
- Persistent smart suggestions

🔎 Advanced Voice Search

Supports filtering by:
- Brand
- Price range
- Keywords

Examples:
Find organic apples
Search milk under 30
Find Colgate toothpaste under 50

💡 Intelligent Recommendations

- History-based suggestions
- Seasonal suggestions
- Substitute suggestions
- Persist across sessions

🛠️ Backend (FastAPI)

Handles:
- NLP parsing
- Database operations
- Search filtering
- Recommendation logic

Run Locally:

cd backend
python -m venv .venv
.\.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload

API runs at:
http://127.0.0.1:8000

Swagger Docs available at:
/docs

📱 Frontend (Flutter)

Located at:
frontend/flutter_app

Run Locally:
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000

Production Build (Web):
flutter build web --release \
--dart-define=API_BASE_URL=https://unthinkable-xaut.onrender.com

The generated output is copied into:
frontend_build/

This folder is deployed as a Render Static Site.

📦 Deployment Architecture

User Browser
      ↓
Flutter Web (Render Static Site)
      ↓
FastAPI Backend (Render Web Service)
      ↓
SQLite Database

🧪 Tech Stack

Backend:
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- Pytest

Frontend:
- Flutter
- Provider (State Management)
- Speech-to-Text

⚠️ Render Free Tier Behavior

- Server sleeps after ~15 minutes of inactivity
- First request may take 20–40 seconds
- This is expected and does not affect functionality