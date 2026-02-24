# 🎙️ Unthinkable: Voice Command Shopping Assistant

Welcome to **Unthinkable**, a production-ready, full-stack shopping assistant that simplifies your grocery runs with natural voice commands. Whether you're speaking English or Spanish, Unthinkable understands your intent, manages your list, and offers smart recommendations based on your habits.

---

## 🌐 Live Application

- **Frontend (Web App):** [👉 PASTE YOUR RENDER URL HERE]
- **Backend API Docs:** [👉 https://unthinkable-xaut.onrender.com/docs](https://unthinkable-xaut.onrender.com/docs)

> [!IMPORTANT]
> **Render Free Tier Behavior:** The backend is hosted on a Render Free Tier service. If the app has been inactive for ~15 minutes, the first request may experience a "cold start" delay of 20–40 seconds. Subsequent interactions will be fast.

---

## ✨ Key Features

### 🧠 Smart Voice Parsing
Our rule-based NLP engine extracts meaningful data from your voice without the need for external APIs:
- **Intents:** Add, Remove, Search, or Modify items.
- **Details:** Automatically detects quantities, item names, and brands.
- **Filters:** Understands price constraints like *"under 50"* or *"hasta 5"*.

### 🛒 Seamless List Management
- **Voice-First:** Add or remove items hands-free.
- **Manual Control:** Adjust quantities with simple `+` / `−` buttons.
- **Categorization:** Automatically organizes items into logical groups.

### 🔎 Advanced Search
Filter results using natural language:
- *"Find organic apples"*
- *"Search milk under 30"*
- *"Busca Colgate hasta 50"*

### 💡 Intelligent Recommendations
Stay ahead of your needs with three types of smart suggestions:
- **History-Based:** Suggests items you buy frequently.
- **Seasonal:** Recommends products based on the current month.
- **Substitutes:** Offers alternatives when an item is out of stock.

---

## 🏗️ Project Structure

```text
Unthinkable/
├── backend/              # FastAPI Python backend
├── frontend/flutter_app  # Flutter source code (dart)
├── frontend_build/       # Compiled Production Web Build
└── README.md             # Project documentation
```

---

## 🚀 Local Development

### 1. Backend (FastAPI + SQLite)
The backend handles the NLP "brains," database persistence, and recommendation logic.

```bash
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\activate | Unix: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
*API will be available at `http://127.0.0.1:8000`. Documentation at `/docs`.*

### 2. Frontend (Flutter)
The frontend provides the interface for voice recording and list interaction.

```bash
cd frontend/flutter_app
# Pass the local backend URL via dart-define
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

---

## 📦 Deployment Architecture

- **Frontend:** Flutter Web (Render Static Site)
- **Backend:** FastAPI Web Service (Render)
- **Database:** SQLite (Embedded DB)

### Production Build
To prepare the app for the web, we build it locally and copy the artifacts:

```bash
flutter build web --release --dart-define=API_BASE_URL=https://unthinkable-xaut.onrender.com
```

The output is located in `frontend_build/`, which serves as the root directory for the Render Static Site.

---

## 🧪 Tech Stack

- **Backend:** FastAPI, SQLAlchemy, Pydantic, SQLite, Pytest.
- **Frontend:** Flutter (Web), Provider (State Management), Speech-to-Text.
- **Infrastructure:** Render (Web Service + Static Site).

---

> [!TIP]
> **Optional Power-Up:** You can enable high-accuracy OpenAI parsing by setting the `OPENAI_API_KEY` in your environment variables. If not set, the built-in rule-based engine handles everything locally with zero cost!