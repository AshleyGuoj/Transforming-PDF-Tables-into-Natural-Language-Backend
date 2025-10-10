"""
Authentication stub for development with JWT support.
Ready to be replaced with Cognito/Clerk in production.
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTPayload(BaseModel):
    """JWT token payload structure."""
    user_id: int  # Changed to int to match database
    email: str
    org_id: int  # Renamed from organization_id and changed to int
    organization_role: str
    project_id: Optional[int] = None  # Changed to int
    project_role: Optional[str] = None
    exp: datetime
    iat: datetime

    # Backwards compatibility
    @property
    def organization_id(self) -> int:
        """Alias for org_id for backwards compatibility."""
        return self.org_id


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    user_id: int,
    email: str,
    org_id: int,
    organization_role: str,
    project_id: Optional[int] = None,
    project_role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User ID (integer)
        email: User email
        org_id: Organization ID (integer)
        organization_role: User role in organization
        project_id: Optional project ID (integer)
        project_role: Optional user role in project
        expires_delta: Optional token expiration time

    Returns:
        str: Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    issued_at = datetime.utcnow()

    payload = {
        "user_id": user_id,
        "email": email,
        "org_id": org_id,
        "organization_role": organization_role,
        "project_id": project_id,
        "project_role": project_role,
        "exp": expire,
        "iat": issued_at,
    }

    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}

    encoded_jwt = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    logger.info(
        "JWT token created",
        user_id=user_id,
        org_id=org_id,
        expires_at=expire.isoformat()
    )

    return encoded_jwt


def decode_jwt_token(token: str) -> Optional[JWTPayload]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        JWTPayload: Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Validate required fields
        required_fields = ["user_id", "email", "org_id", "organization_role", "exp", "iat"]
        for field in required_fields:
            if field not in payload:
                logger.warning(f"Missing required field in JWT: {field}")
                return None

        # Convert timestamps
        exp = datetime.fromtimestamp(payload["exp"])
        iat = datetime.fromtimestamp(payload["iat"])

        # Check expiration
        if datetime.utcnow() > exp:
            logger.warning("JWT token expired")
            return None

        return JWTPayload(
            user_id=payload["user_id"],
            email=payload["email"],
            org_id=payload["org_id"],
            organization_role=payload["organization_role"],
            project_id=payload.get("project_id"),
            project_role=payload.get("project_role"),
            exp=exp,
            iat=iat
        )

    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error decoding JWT: {e}")
        return None


def create_dev_token(
    user_id: int = 1,
    email: str = "dev@example.com",
    org_id: int = 1,
    organization_role: str = "admin",
    project_id: Optional[int] = 1,
    project_role: Optional[str] = "admin"
) -> str:
    """
    Create a development JWT token for testing.

    This is a convenience function for development and testing.
    In production, tokens should be created through proper authentication flow.
    """
    return create_access_token(
        user_id=user_id,
        email=email,
        org_id=org_id,
        organization_role=organization_role,
        project_id=project_id,
        project_role=project_role
    )


# Development helper functions
def get_dev_admin_token() -> str:
    """Get a development admin token with 24h expiration."""
    from datetime import timedelta
    return create_access_token(
        user_id=1,
        email="admin@guideline-transform.com",
        org_id=1,
        organization_role="admin",
        project_id=1,
        project_role="admin",
        expires_delta=timedelta(hours=24)  # 24 hour expiration for dev
    )


def get_dev_annotator_token() -> str:
    """Get a development annotator token."""
    return create_dev_token(
        user_id=2,
        email="annotator@guideline-transform.com",
        org_id=1,
        organization_role="annotator"
    )


def get_dev_qa_token() -> str:
    """Get a development QA token."""
    return create_dev_token(
        user_id=3,
        email="qa@guideline-transform.com",
        org_id=1,
        organization_role="qa"
    ) 