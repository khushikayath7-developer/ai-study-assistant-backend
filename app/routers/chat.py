from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
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
    conversation = None
    if request.conversation_id is not None:
        conversation = (
            db.query(models.Conversation)
            .filter(
                models.Conversation.id == request.conversation_id,
                models.Conversation.user_id == current_user.id,
            )
            .first()
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Chat not found")

    answer = ask_ai(request.question, history=request.history)

    if conversation is None:
        conversation = models.Conversation(
            user_id=current_user.id,
            title=request.question.strip()[:200] or "New chat",
        )
        db.add(conversation)
        db.flush()
    conversation.updated_at = datetime.utcnow()

    chat = models.ChatHistory(
        user_id=current_user.id,
        conversation_id=conversation.id,
        question=request.question,
        answer=answer,
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.get("/history", response_model=List[schemas.ConversationOut])
def get_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == current_user.id)
        .order_by(models.Conversation.updated_at.desc())
        .all()
    )
