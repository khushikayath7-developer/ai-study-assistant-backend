from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.utils.security import get_current_user
from app.services.ai_service import ask_ai

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/ask", response_model=schemas.ChatResponse)
def ask_question(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    answer = ask_ai(request.question)

    chat = models.ChatHistory(
        user_id=current_user.id,
        question=request.question,
        answer=answer,
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/history", response_model=List[schemas.ChatResponse])
def get_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.ChatHistory)
        .filter(models.ChatHistory.user_id == current_user.id)
        .order_by(models.ChatHistory.created_at.desc())
        .all()
    )
