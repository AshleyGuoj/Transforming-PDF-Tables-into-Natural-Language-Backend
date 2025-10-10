"""
Development-only API routes
These routes should NOT be available in production
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import get_logger
from app.security.auth_stub import get_dev_admin_token

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter()


class DevTokenResponse(BaseModel):
    """Development token response"""
    token: str
    message: str
    expires_in_hours: int


@router.post("/dev-token", response_model=DevTokenResponse)
async def get_development_token():
    """
    Get a development JWT token for testing.

    ⚠️ WARNING: This endpoint should ONLY be available in development!
    It bypasses all authentication and returns a valid admin token.

    Returns:
        DevTokenResponse: JWT token with 24h expiration
    """
    # Only allow in development/local environment
    if settings.APP_ENV not in ["local", "development", "dev"]:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available in development mode"
        )

    logger.warning("⚠️ Development token requested - this should only happen in dev!")

    # Generate admin token with 24h expiration
    token = get_dev_admin_token()

    return DevTokenResponse(
        token=token,
        message="Development token generated. Valid for 24 hours.",
        expires_in_hours=24
    )
