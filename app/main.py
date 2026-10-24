from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import Base, engine, SessionLocal
from app import models
from app.routers import auth, chat, files

# Creates all tables in Postgres if they don't already exist
Base.metadata.create_all(bind=engine)


def ensure_conversation_schema():
    """Add the conversation link for databases created by older app versions."""
    with engine.begin() as connection:
        connection.execute(text(
            "ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS conversation_id INTEGER"
        ))

    db = SessionLocal()
    try:
        legacy_messages = (
            db.query(models.ChatHistory)
            .filter(models.ChatHistory.conversation_id.is_(None))
            .all()
        )
        for message in legacy_messages:
            conversation = models.Conversation(
                user_id=message.user_id,
                title=message.question.strip()[:200] or "Previous chat",
                created_at=message.created_at,
                updated_at=message.created_at,
            )
            db.add(conversation)
            db.flush()
            message.conversation_id = conversation.id
        db.commit()
    finally:
        db.close()


ensure_conversation_schema()

app = FastAPI(title="AI Study Assistant API")

# Allow the React Native app to call this API from any origin (fine for a college project)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(files.router)


@app.get("/")
def root():
    return {"message": "AI Study Assistant API is running 🚀"}
