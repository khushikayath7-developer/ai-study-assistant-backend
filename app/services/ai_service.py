import logging
import requests
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger(__name__)
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _model_names() -> list[str]:
    """Return unique models in fast-fallback order."""
    models = [
        # Prefer the verified low-latency model instead of waiting on an
        # overloaded "latest" alias before trying a fallback.
        "gemini-3.1-flash-lite",
        settings.GEMINI_MODEL,
        settings.GEMINI_FALLBACK_MODEL,
        "gemini-3.6-flash",
    ]
    return list(dict.fromkeys(model for model in models if model))


def ask_ai(question: str, context_text: str = "", history: list = None) -> str:
    """
    Sends the student's question to Google Gemini.
    - context_text: extracted notes/document text (supports large documents, ~200 pages)
    - history: recent conversation turns [{"role": "user"|"ai", "text": "..."}] so the AI
      remembers what was just discussed, instead of treating every message as brand new.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set in .env")

    parts = [
        "You are a friendly, helpful study assistant for a student. "
        "Reply naturally and conversationally, like a real tutor chatting with a student. "
        "Reply in the same language style the student uses (English, Hindi or Hinglish).\n\n"
        "SCOPE RULES: You help with studies, learning, explaining concepts, notes and documents, "
        "homework, exam preparation, and general knowledge questions. If the student asks for "
        "something outside this, such as song lyrics, copyrighted text, or anything you cannot or "
        "should not provide, do NOT show any error. Instead reply with a short, kind message saying "
        "this feature is not available in this study assistant right now, and offer 1-2 study-related "
        "things you can help with instead."
    ]

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

    # Switch models immediately on transient failures. Repeating the same overloaded
    # model several times made every chat request unnecessarily take minutes.
    retry_statuses = {429, 500, 502, 503, 504}
    response = None
    saw_rate_limit = False

    for model in _model_names():
        url = f"{GEMINI_API_BASE}/{model}:generateContent"
        try:
            response = requests.post(
                url,
                headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                json=payload,
                timeout=(8, 30),
            )
        except requests.exceptions.RequestException as exc:
            logger.warning("Gemini model %s request failed: %s", model, type(exc).__name__)
            response = None
            continue

        if response.status_code == 200:
            break

        logger.warning("Gemini model %s returned HTTP %s", model, response.status_code)
        if response.status_code == 429:
            saw_rate_limit = True

        if response.status_code in {400, 404}:
            # A model can be listed for the key but unavailable on this endpoint.
            # Skip it and continue with the next configured model.
            continue

        if response.status_code not in retry_statuses:
            # Authentication, invalid request, or another permanent configuration error.
            raise HTTPException(
                status_code=502,
                detail="The AI service is not configured correctly. Please contact support."
            )
    else:
        if saw_rate_limit:
            raise HTTPException(
                status_code=429,
                detail="The AI request limit has been reached. Please try again later."
            )
        raise HTTPException(
            status_code=503,
            detail="All available AI models are temporarily unavailable. Please try again later."
        )

    data = response.json()
    try:
        answer = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        answer = "Sorry, I couldn't generate an answer right now."

    return answer
