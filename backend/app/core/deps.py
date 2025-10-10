"""
FastAPI dependency injection helpers.
Provides common dependencies like database sessions, authentication, etc.
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_async_session
from app.security.auth_stub import decode_jwt_token, JWTPayload

settings = get_settings()
security = HTTPBearer(auto_error=False)  # Don't auto error in dev mode


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    Automatically handles session cleanup.
    """
    async with get_async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> JWTPayload:
    """
    Dependency to get current authenticated user from JWT token.

    In development mode, uses the fake user from request.state set by bypass_auth_middleware.
    In production, validates JWT token from Authorization header.

    Args:
        request: FastAPI request object
        credentials: JWT token from Authorization header (optional in dev mode)
        db: Database session

    Returns:
        JWTPayload: Decoded JWT payload with user information

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Development mode: Use fake user from request.state (set by middleware)
    if settings.APP_ENV in ["local", "development", "dev"]:
        # Try to get user from request state (set by bypass_auth_middleware)
        if hasattr(request.state, 'user'):
            return request.state.user

    # Production mode: Validate JWT token
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Extract token from credentials
        token_str = credentials.credentials

        # Decode JWT token
        payload = decode_jwt_token(token_str)

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(required_role: str, scope: str = "organization"):
    """
    Create a dependency that requires a specific role.
    
    Args:
        required_role: Required role (admin, annotator, qa, viewer)
        scope: Scope of the role check (organization, project)
        
    Returns:
        Dependency function that checks role requirements
    """
    async def check_role(
        current_user: JWTPayload = Depends(get_current_user)
    ) -> JWTPayload:
        """Check if user has required role."""
        
        # Check organization role
        if scope == "organization":
            user_role = current_user.organization_role
        elif scope == "project":
            user_role = current_user.project_role or current_user.organization_role
        else:
            raise ValueError(f"Invalid scope: {scope}")
            
        # Role hierarchy: admin > qa > annotator > viewer
        role_hierarchy = {
            "viewer": 1,
            "annotator": 2,
            "qa": 3,
            "admin": 4
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
            
        return current_user
        
    return check_role


def require_organization_access(organization_id: Optional[str] = None):
    """
    Create a dependency that checks organization access.
    
    Args:
        organization_id: Optional organization ID to check against
        
    Returns:
        Dependency function that checks organization access
    """
    async def check_organization_access(
        current_user: JWTPayload = Depends(get_current_user)
    ) -> JWTPayload:
        """Check if user has access to organization."""
        
        if organization_id and current_user.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
            
        return current_user
        
    return check_organization_access


def require_project_access(project_id: Optional[str] = None):
    """
    Create a dependency that checks project access.
    
    Args:
        project_id: Optional project ID to check against
        
    Returns:
        Dependency function that checks project access
    """
    async def check_project_access(
        current_user: JWTPayload = Depends(get_current_user)
    ) -> JWTPayload:
        """Check if user has access to project."""
        
        # If user has project-specific role, check project ID
        if current_user.project_id and project_id:
            if current_user.project_id != project_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this project"
                )
        # If no project-specific role, check organization access
        elif project_id:
            # TODO: Verify project belongs to user's organization
            # This would require a database query
            pass
            
        return current_user
        
    return check_project_access


# Common role-based dependencies
require_admin = require_role("admin")
require_qa = require_role("qa")
require_annotator = require_role("annotator")
require_viewer = require_role("viewer")

# Project-scoped role dependencies
require_project_admin = require_role("admin", "project")
require_project_qa = require_role("qa", "project")
require_project_annotator = require_role("annotator", "project")


class RateLimiter:
    """
    Simple in-memory rate limiter for API endpoints.
    In production, this should be replaced with Redis-based implementation.
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
        
    async def __call__(self, 
                      current_user: JWTPayload = Depends(get_current_user)) -> None:
        """Rate limit dependency."""
        if not settings.RATE_LIMIT_ENABLED:
            return
            
        import time
        from collections import defaultdict, deque
        
        user_id = current_user.user_id
        current_time = time.time()
        
        # Initialize user request history
        if user_id not in self.requests:
            self.requests[user_id] = deque()
            
        # Remove old requests (older than 1 minute)
        user_requests = self.requests[user_id]
        while user_requests and user_requests[0] < current_time - 60:
            user_requests.popleft()
            
        # Check rate limit
        if len(user_requests) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
            
        # Add current request
        user_requests.append(current_time)


# Rate limiter instance
rate_limiter = RateLimiter(settings.RATE_LIMIT_REQUESTS_PER_MINUTE) 