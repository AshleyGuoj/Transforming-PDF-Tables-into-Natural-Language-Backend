"""
Pydantic schemas for User model.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserBase(BaseModel):
    """Base schema for User with common fields."""
    email: EmailStr = Field(..., description="User email address")
    org_id: Optional[int] = Field(None, description="Organization ID")
    availability: Optional[Dict[str, Any]] = Field(None, description="User availability schedule")
    language_expertise: Optional[List[str]] = Field(None, description="Languages the user can work with")
    skill_level: Optional[str] = Field(None, description="User skill level")
    is_active: bool = Field(True, description="Whether user is active")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    org_id: Optional[int] = None
    availability: Optional[Dict[str, Any]] = None
    language_expertise: Optional[List[str]] = None
    skill_level: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user responses."""
    user_id: int = Field(..., description="User ID")
    skill_score: Optional[float] = Field(None, description="Calculated skill score")
    qa_approval_rate: Optional[float] = Field(None, description="QA approval rate")
    completed_task_count: int = Field(0, description="Number of completed tasks")
    
    model_config = ConfigDict(from_attributes=True)

