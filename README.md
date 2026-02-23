# 🎙️ Voice Command Shopping Assistant

Welcome to the **Voice Command Shopping Assistant**! This project is a production-ready application that lets you manage your shopping list using simple voice commands in both **English** and **Spanish**. 

Whether you're saying *"Add 2 bottles of water"* or *"Busca leche hasta 5"*, this assistant understands your intent, manages your list, and even suggests items based on your shopping habits.

---

## 🚀 Getting Started

The project is split into a **FastAPI backend** and a **Flutter mobile frontend**.

### 1. Backend (FastAPI + SQLite)
The backend handles the "brains" of the operation—parsing your voice, managing the database, and generating smart recommendations.

**Quick Local Setup:**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
*The server will start at `http://127.0.0.1:8000`. You can view the API documentation at `/docs`.*

### 2. Frontend (Flutter)
The mobile app provides a clean interface to listen to your voice and display your interactive shopping list.

**Setting up the Mobile App:**
1. Create a fresh Flutter project: `flutter create my_shopping_app`
2. Replace the `lib` folder and `pubspec.yaml` with the ones provided in `frontend/flutter_app/`.
3. Add the **Microphone Permission**:
   - **Android**: Add `RECORD_AUDIO` to `AndroidManifest.xml`.
   - **iOS**: Add `NSMicrophoneUsageDescription` to `Info.plist`.
4. Run the app: `flutter run`

---

## ✨ Key Features

- **Smart Voice Parsing**: A rule-based NLP engine that extracts items, quantities, brands, and price limits without needing external APIs (unless you want to use OpenAI).
- **Multilingual Support**: Switch seamlessly between English and Spanish.
- **Intelligent Recommendations**: 
  - **History-based**: Suggests items you buy frequently.
  - **Seasonal**: Recommends products based on the current month.
  - **Substitutes**: Suggests alternatives when an item isn't in stock.
- **Advanced Search**: Filter your search results by brand or maximum price using just your voice.

---

## 🛠️ How it Works

When you send a voice command:
1. **NLP Pipeline**: The text is analyzed to detect the **Action** (Add, Remove, Search, Modify), the **Item**, and any specific **Filters** (like "under $5").
2. **Database Tracking**: Items are stored in a local SQLite database using SQLAlchemy.
3. **Smart Logic**: The system updates your user history with every interaction to make better suggestions next time you open the app.

---

## 🧪 Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic, Pytest.
- **Frontend**: Flutter, Provider (State Management), Speech-to-Text.
- **Database**: SQLite (Small, fast, and zero-config).

---

> [!TIP]
> **Optional Power-Up**: You can enable high-accuracy OpenAI parsing by setting the `OPENAI_API_KEY` in your environment variables. If not set, the built-in rule-based engine handles everything locally!

