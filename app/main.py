"""
Main FastAPI application for StudyFlow backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import progress_router, analytics_router

# Create FastAPI app
app = FastAPI(
    title="StudyFlow API",
    description="Backend API for StudyFlow learning platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
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
        "message": "StudyFlow API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers
app.include_router(progress_router)
app.include_router(analytics_router)
