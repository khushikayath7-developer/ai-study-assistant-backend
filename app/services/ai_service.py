import time
import requests
from fastapi import HTTPException
from app.config import settings

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
)


def ask_ai(question: str, context_text: str = "", history: list = None) -> str:
    """
    Sends the student's question to Google Gemini.
    - context_text: extracted notes/document text (supports large documents, ~200 pages)
    - history: recent conversation turns [{"role": "user"|"ai", "text": "..."}] so the AI
      remembers what was just discussed, instead of treating every message as brand new.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set in .env")

    parts = ["You are a friendly, helpful study assistant for a student. "
             "Reply naturally and conversationally, like a real tutor chatting with a student."]

    if context_text:
        parts.append(
            "\nIMPORTANT: The student has already uploaded a document, and its full text content "
            "is provided below as STUDY NOTES. This text IS the document — treat it exactly as if "
            "you are reading the student's PDF directly. NEVER say the PDF/document is missing, "
            "not attached, or not received — it is right here in the STUDY NOTES section. "
            "Always answer using this content when the student refers to 'the file', 'the PDF', "
            "'the document', or 'what I sent'."
        )
        parts.append(f"\nSTUDY NOTES (this is the uploaded document's content):\n{context_text[:300000]}")

    if history:
        convo = "\n".join(
            f"{'Student' if h.get('role') == 'user' else 'Assistant'}: {h.get('text', '')}"
            for h in history[-8:]  # last 8 turns is enough context, keeps it fast
        )
        parts.append(f"\nRECENT CONVERSATION:\n{convo}")

    parts.append(f"\nStudent's new message:\n{question}")
    prompt = "\n".join(parts)

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    response = requests.post(GEMINI_URL, json=payload, timeout=30)

    # Free-tier rate limit hit -> wait a moment and try once more automatically
    if response.status_code == 429:
        time.sleep(3)
        response = requests.post(GEMINI_URL, json=payload, timeout=30)

    if response.status_code == 429:
        raise HTTPException(
            status_code=429,
            detail="AI thoda busy hai (free tier limit). Kripya 10-15 second baad dobara try karein."
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {response.text}"
        )

    data = response.json()
    try:
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        answer = "Sorry, I couldn't generate an answer right now."

    return answer
