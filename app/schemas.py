from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional


# ---------- Auth ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Chat ----------
class ChatRequest(BaseModel):
    question: str
    history: Optional[list] = None
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    id: int
    conversation_id: Optional[int] = None
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    title: str
    file_id: Optional[int] = None
    file_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[ChatResponse]

    class Config:
        from_attributes = True


# ---------- File ----------
class FileOut(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime

    class Config:
        from_attributes = True
