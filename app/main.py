"""
Main FastAPI application for StudyFlow.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import students, chat, progress, analytics
from app.services.chat_service import chat_service

# Create FastAPI app
app = FastAPI(
    title="StudyFlow API",
    description="Backend API for StudyFlow learning platform (using GLM-4.7)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup."""
    init_db()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "StudyFlow API (GLM-4.7)",
        "version": "1.0.0",
        "status": "running",
        "ai_model": "GLM-4.7 (Zhipu AI)"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "ai_model": "GLM-4.7",
        "database": "connected"
    }


# Include routers
app.include_router(students.router, prefix="/api/v1/students", tags=["students"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(progress.router, prefix="/api/v1/progress", tags=["progress"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
