import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
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
    history: str = Form(None),  # JSON string of recent conversation, sent from the app
    conversation_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Ask a question using an uploaded file's extracted text as context."""
    record = (
        db.query(models.UploadedFile)
        .filter(models.UploadedFile.id == file_id, models.UploadedFile.user_id == current_user.id)
        .first()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="File not found")

    conversation = None
    if conversation_id is not None:
        conversation = (
            db.query(models.Conversation)
            .filter(
                models.Conversation.id == conversation_id,
                models.Conversation.user_id == current_user.id,
            )
            .first()
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Chat not found")

    context = record.extracted_text or ""
    parsed_history = json.loads(history) if history else None
    answer = ask_ai(question, context_text=context, history=parsed_history)

    if conversation is None:
        conversation = models.Conversation(
            user_id=current_user.id,
            title=question.strip()[:200] or record.filename,
            file_id=record.id,
        )
        db.add(conversation)
        db.flush()
    else:
        conversation.file_id = record.id
    conversation.updated_at = datetime.utcnow()

    chat = models.ChatHistory(
        user_id=current_user.id,
        conversation_id=conversation.id,
        question=question,
        answer=answer,
    )
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
