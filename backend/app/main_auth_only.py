"""
Simplified FastAPI Application - Auth Only
For testing authentication without database dependencies
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth
from app.core.config import get_settings

# Initialize settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="GuidelineTransform AI - Auth Only",
    description="Authentication service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "auth-only"}

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint with basic information."""
    return {
        "message": "GuidelineTransform AI Auth API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main_auth_only:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

