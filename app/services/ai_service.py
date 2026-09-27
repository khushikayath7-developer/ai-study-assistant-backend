import requests
from fastapi import HTTPException
from app.config import settings

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
)


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

    response = requests.post(GEMINI_URL, json=payload, timeout=30)

    if response.status_code != 200:
        try:
            error_message = response.json().get("error", {}).get("message")
        except ValueError:
            error_message = None
        raise HTTPException(
            status_code=502,
            detail=error_message or "The AI service is temporarily unavailable."
        )

    data = response.json()
    try:
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        answer = "Sorry, I couldn't generate an answer right now."

    return answer
