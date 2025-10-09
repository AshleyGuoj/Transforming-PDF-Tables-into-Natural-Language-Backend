"""
Authentication API endpoints.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.security.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Request/Response models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    roles: List[str]
    org_ids: List[int]
    project_ids: List[int]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    home: str
    user: UserResponse


# Demo users for testing (hardcoded)
DEMO_USERS = {
    "admin@example.com": {
        "id": 1,
        "email": "admin@example.com",
        "password": "admin123",
        "display_name": "System Admin",
        "roles": ["SYSTEM_ADMIN"],
        "org_ids": [1, 2, 3],
        "project_ids": [11, 12, 13]
    },
    "orgadmin@example.com": {
        "id": 2,
        "email": "orgadmin@example.com",
        "password": "org123",
        "display_name": "Org Admin",
        "roles": ["ORG_ADMIN"],
        "org_ids": [1],
        "project_ids": [11, 12]
    },
    "pm@example.com": {
        "id": 3,
        "email": "pm@example.com",
        "password": "pm123",
        "display_name": "Project Manager",
        "roles": ["PM"],
        "org_ids": [1],
        "project_ids": [11]
    },
    "annotator@example.com": {
        "id": 4,
        "email": "annotator@example.com",
        "password": "annotator123",
        "display_name": "Annotator User",
        "roles": ["ANNOTATOR"],
        "org_ids": [1],
        "project_ids": [11]
    },
    "qa@example.com": {
        "id": 5,
        "email": "qa@example.com",
        "password": "qa123",
        "display_name": "QA User",
        "roles": ["QA"],
        "org_ids": [1],
        "project_ids": [11]
    }
}


def verify_credentials(email: str, password: str) -> Optional[Dict]:
    """
    Stub function to verify user credentials.
    Returns user data if valid, None otherwise.
    """
    user = DEMO_USERS.get(email)
    if user and user["password"] == password:
        return user
    return None


def determine_home(roles: List[str]) -> str:
    """
    Determine home page based on user roles.
    Priority order: ANNOTATOR > QA > SYSTEM_ADMIN > ORG_ADMIN > PM
    """
    if "ANNOTATOR" in roles:
        return "/annotator"
    elif "QA" in roles:
        return "/qa"
    elif "SYSTEM_ADMIN" in roles:
        return "/console/system"
    elif "ORG_ADMIN" in roles:
        return "/console/org"
    elif "PM" in roles:
        return "/console/project"
    else:
        return "/login"


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token with user information.
    """
    # Verify credentials
    user = verify_credentials(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create JWT payload
    jwt_payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "roles": user["roles"],
        "org_ids": user["org_ids"],
        "project_ids": user["project_ids"]
    }
    
    # Generate access token
    access_token = create_access_token(jwt_payload, expires_minutes=120)
    
    # Determine home page
    home = determine_home(user["roles"])
    
    # Build response
    user_response = UserResponse(
        id=user["id"],
        email=user["email"],
        display_name=user["display_name"],
        roles=user["roles"],
        org_ids=user["org_ids"],
        project_ids=user["project_ids"]
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        home=home,
        user=user_response
    )


