from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .database import engine
from .models import Base
from .routers import auth, profile, courses, recommendations, chat, selection

app = FastAPI(title="SelectClass API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth, prefix="/api")
app.include_router(profile, prefix="/api")
app.include_router(courses, prefix="/api")
app.include_router(recommendations, prefix="/api")
app.include_router(chat, prefix="/api")
app.include_router(selection, prefix="/api")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "backend": "python", "timestamp": __import__("time").time()}
