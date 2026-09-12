from fastapi import APIRouter
from app.api.v1.endpoints import auth, chat, sessions, documents, health

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Users"])
api_router.include_router(chat.router, prefix="/chat", tags=["Conversational RAG"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Session History"])
api_router.include_router(documents.router, prefix="/documents", tags=["Knowledge Base"])
api_router.include_router(health.router, prefix="/health", tags=["Health & Monitoring"])
