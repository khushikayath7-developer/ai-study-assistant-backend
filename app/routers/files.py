from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import models, schemas
from app.utils.security import get_current_user
from app.services.file_service import save_upload, extract_text
from app.services.ai_service import ask_ai

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=schemas.FileOut)
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    filepath = save_upload(file, current_user.id)
    text = extract_text(filepath)

    record = models.UploadedFile(
        user_id=current_user.id,
        filename=file.filename,
        filepath=filepath,
        extracted_text=text,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/{file_id}/ask", response_model=schemas.ChatResponse)
def ask_about_file(
    file_id: int,
    question: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Ask a question using an uploaded file's extracted text as context."""
    record = (
        db.query(models.UploadedFile)
        .filter(models.UploadedFile.id == file_id, models.UploadedFile.user_id == current_user.id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Uploaded file not found.")
    if not record.extracted_text or not record.extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail=(
                "No readable text was found in this file. Please upload a text-based PDF; "
                "scanned PDFs and images require OCR, which is not supported yet."
            ),
        )

    answer = ask_ai(question, context_text=record.extracted_text)

    chat = models.ChatHistory(user_id=current_user.id, question=question, answer=answer)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/", response_model=List[schemas.FileOut])
def list_files(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.UploadedFile)
        .filter(models.UploadedFile.user_id == current_user.id)
        .order_by(models.UploadedFile.uploaded_at.desc())
        .all()
    )
