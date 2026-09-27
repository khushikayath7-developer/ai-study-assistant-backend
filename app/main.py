from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import auth, chat, files

# Creates all tables in Postgres if they don't already exist
Base.metadata.create_all(bind=engine)

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
