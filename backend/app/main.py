"""
GuidelineTransform AI - Main FastAPI Application

Production-ready MVP for PDF table extraction and AI-assisted annotation pipeline.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Import new refactored routes
from app.api.v1 import (
    routes_projects_simple,  # Using simple routes to bypass ORM issues
    routes_files,
    routes_parse_azure,
    routes_tasks_new,
    routes_export_new,
    routes_dev  # Development-only routes
)
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import engine

# Initialize settings and logging
settings = get_settings()
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info("Starting GuidelineTransform AI application", extra={"event": "startup"})
    
    # Test database connection
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down GuidelineTransform AI application", extra={"event": "shutdown"})
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="GuidelineTransform AI",
    description="PDF table extraction and AI-assisted annotation pipeline",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS for Frontend Integration
# Allows React frontend (localhost:3000) to access backend API (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,  # Configured in .env: ["http://localhost:3000", "http://localhost:8000"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all custom headers
)


# Development-only: Bypass JWT Authentication
# ⚠️ WARNING: This middleware bypasses ALL authentication in development mode!
# It should NEVER be enabled in production.
if settings.APP_ENV in ["local", "development", "dev"]:
    from app.security.auth_stub import JWTPayload
    from datetime import datetime, timedelta

    @app.middleware("http")
    async def bypass_auth_middleware(request: Request, call_next):
        """
        Development middleware to bypass JWT authentication.

        This creates a fake authenticated user for all requests,
        allowing testing without authentication.

        ⚠️ ONLY ENABLED IN DEVELOPMENT MODE ⚠️
        """
        # Create a fake admin user for all requests
        fake_user = JWTPayload(
            user_id=1,
            email="dev@grandscale.com",
            org_id=1,
            organization_role="admin",
            project_id=1,
            project_role="admin",
            exp=datetime.utcnow() + timedelta(hours=24),
            iat=datetime.utcnow()
        )

        # Attach the fake user to request state
        # This makes it available to dependencies via request.state
        request.state.user = fake_user

        response = await call_next(request)
        return response

    logger.warning("⚠️ Authentication bypass enabled for development - ALL requests will use admin credentials!")


# Global exception handlers
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    logger.error(f"Database error: {exc}", extra={"url": str(request.url)})
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred", "error": "internal_server_error"}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}", extra={"url": str(request.url)})
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error": "validation_error"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {exc}", extra={"url": str(request.url)}, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": "internal_server_error"}
    )


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "guideline-transform-ai"}


@app.get("/health/ready")
async def readiness_check():
    """Readiness check with database connectivity."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "disconnected", "error": str(e)}
        )


# Register API routes (refactored)
app.include_router(
    routes_projects_simple.router,
    prefix="/api/v1",
    tags=["Projects"]
)

app.include_router(
    routes_files.router,
    prefix="/api/v1",
    tags=["Files"]
)

app.include_router(
    routes_parse_azure.router,
    prefix="/api/v1",
    tags=["Parse"]
)

app.include_router(
    routes_tasks_new.router,
    prefix="/api/v1",
    tags=["Tasks"]
)

app.include_router(
    routes_export_new.router,
    prefix="/api/v1",
    tags=["Export"]
)

# Development-only routes (should be disabled in production)
if settings.APP_ENV in ["local", "development", "dev"]:
    app.include_router(
        routes_dev.router,
        prefix="/api",
        tags=["Development"]
    )
    logger.warning("⚠️ Development routes enabled - disable in production!")


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint with basic information."""
    return {
        "message": "GuidelineTransform AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_ENV == "local",
        log_level=settings.LOG_LEVEL.lower(),
    ) 