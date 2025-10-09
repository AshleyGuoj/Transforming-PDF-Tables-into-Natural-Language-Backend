"""
JWT token creation and validation utilities.
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from jose import jwt, JWTError

from app.core.config import get_settings

# Get settings
settings = get_settings()
JWT_SECRET = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM


def create_access_token(payload: Dict[str, Any], expires_minutes: int = 120) -> str:
    """
    Create a JWT access token.
    
    Args:
        payload: Dictionary containing token claims (sub, email, roles, etc.)
        expires_minutes: Token expiration time in minutes (default 120)
    
    Returns:
        Encoded JWT token string
    """
    to_encode = payload.copy()
    
    # Add expiration time
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode["exp"] = int(expire.timestamp())
    
    # Encode the token
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token, returning the payload.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload dictionary
    
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")

