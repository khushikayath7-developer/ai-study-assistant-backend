import os
import shutil
from fastapi import UploadFile
from app.config import settings

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def save_upload(file: UploadFile, user_id: int) -> str:
    """Saves uploaded file to disk and returns its path."""
    user_folder = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_folder, exist_ok=True)

    filepath = os.path.join(user_folder, file.filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return filepath


def extract_text(filepath: str) -> str:
    """Extracts text from a PDF file. Returns empty string for images/others."""
    if filepath.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
        except Exception:
            return ""
    # For images, OCR could be added later (e.g. pytesseract).
    return ""
