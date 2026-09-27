# Backend Setup (FastAPI + PostgreSQL + Gemini AI)

## Step 1 — PostgreSQL install & DB banao
1. PostgreSQL install karo (agar nahi hai): https://www.postgresql.org/download/
2. pgAdmin ya terminal se ek naya database banao:
   ```sql
   CREATE DATABASE study_assistant_db;
   ```

## Step 2 — Gemini API key lo (FREE)
1. https://aistudio.google.com/app/apikey pe jao
2. Google account se login karke "Create API Key" click karo
3. Key copy karo

## Step 3 — Python environment setup
```bash
cd backend
python -m venv venv

# Activate:
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt
```

## Step 4 — .env file banao
`.env.example` ko copy karke `.env` banao:
```bash
cp .env.example .env
```
Ab `.env` file open karke apna real Postgres password aur Gemini API key daalo:
```
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/study_assistant_db
SECRET_KEY=koi-bhi-random-lambi-string-daal-do
GEMINI_API_KEY=tumhari-gemini-key
```

## Step 5 — Server run karo
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ab browser me kholo: **http://localhost:8000/docs**
Yahan Swagger UI me tum saare API endpoints test kar sakte ho (register, login, chat/ask, files/upload).

## Important — Mobile se connect karne ke liye
Agar React Native app **real phone** ya **emulator** se backend ko call karega, to `localhost` kaam nahi karega:
- **Android Emulator**: use `http://10.0.2.2:8000`
- **Real phone (same WiFi)**: apne laptop ka local IP nikalo (`ipconfig` / `ifconfig`) aur `http://192.168.x.x:8000` use karo

## API Endpoints Summary
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Naya user banao |
| POST | /auth/login | Login karo, JWT token milega |
| POST | /chat/ask | AI se question pucho |
| GET  | /chat/history | Purani chats dekho |
| POST | /files/upload | PDF/image upload karo |
| POST | /files/{id}/ask | Uploaded file ke context se sawal pucho |
| GET  | /files/ | Apni uploaded files ki list dekho |
