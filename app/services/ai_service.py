import requests
from fastapi import HTTPException
from app.config import settings

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def _model_url(model: str) -> str:
    return f"{GEMINI_BASE_URL}/{model}:generateContent?key={settings.GEMINI_API_KEY}"


def ask_ai(question: str, context_text: str = "") -> str:
    """
    Sends the student's question (optionally with extracted file context)
    to Google Gemini and returns the answer text.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set in .env")

    prompt = question
    if context_text:
        prompt = (
            "You are a helpful study assistant. Use the following notes as context "
            "if relevant, then answer the student's question clearly and simply.\n\n"
            f"NOTES:\n{context_text[:6000]}\n\n"
            f"QUESTION:\n{question}"
        )

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    models = list(dict.fromkeys([settings.GEMINI_MODEL, settings.GEMINI_FALLBACK_MODEL]))
    last_error = None

    for model in models:
        try:
            response = requests.post(_model_url(model), json=payload, timeout=45)
        except requests.RequestException:
            last_error = "Unable to connect to the AI service."
            continue

        if response.status_code == 200:
            data = response.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                last_error = "The AI returned an empty response."
                continue

        try:
            last_error = response.json().get("error", {}).get("message")
        except ValueError:
            last_error = None

        # Try the fallback for unavailable, overloaded, or rate-limited models.
        if response.status_code not in (404, 429, 503):
            break

    raise HTTPException(
        status_code=502,
        detail=last_error or "The AI service is temporarily unavailable. Please try again."
    )
