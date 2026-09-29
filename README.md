# Backend Setup (FastAPI + PostgreSQL + Gemini AI)

## Step 1 — Install PostgreSQL and create the database

1. Install [PostgreSQL](https://www.postgresql.org/download/) if it is not already installed.
2. Create a new database using pgAdmin or the terminal:

   ```sql
   CREATE DATABASE study_assistant_db;
   ```

## Step 2 — Create a Gemini API key

1. Open [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in with your Google account and click **Create API Key**.
3. Copy the generated key.

## Step 3 — Set up the Python environment

```bash
cd backend
python -m venv venv

# Activate the environment on Windows:
venv\Scripts\activate

# Activate the environment on macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

## Step 4 — Create the environment file

Copy `.env.example` to a new file named `.env`:

```bash
cp .env.example .env
```

Open `.env` and provide your PostgreSQL password, a secure JWT secret, and your Gemini API key:

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/study_assistant_db
SECRET_KEY=replace-with-a-long-random-secret
GEMINI_API_KEY=your-gemini-api-key
```

Never commit the `.env` file or expose its values publicly.

## Step 5 — Run the server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000/docs** in a browser. The Swagger UI can be used to test the registration, login, chat, and file-upload endpoints.

## Connecting from a mobile device

`localhost` does not point to the development computer when the React Native app runs on a phone or Android emulator.

- **Android Emulator:** use `http://10.0.2.2:8000`.
- **Physical phone on the same Wi-Fi network:** find the computer's local IP address with `ipconfig` or `ifconfig`, then use an address such as `http://192.168.x.x:8000`.

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create a new user account |
| POST | `/auth/login` | Log in and receive a JWT access token |
| POST | `/chat/ask` | Ask the AI a question |
| GET | `/chat/history` | Retrieve previous conversations |
| POST | `/files/upload` | Upload a PDF or image |
| POST | `/files/{id}/ask` | Ask a question using an uploaded file as context |
| GET | `/files/` | List the current user's uploaded files |
