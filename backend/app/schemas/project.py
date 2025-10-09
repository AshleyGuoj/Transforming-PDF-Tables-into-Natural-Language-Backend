"""
Pydantic schemas for Project model.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ProjectBase(BaseModel):
    """Base schema for Project with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    requirements_text: Optional[str] = Field(None, description="Project requirements")
    status: str = Field("draft", description="Project status")
    is_active: bool = Field(True, description="Whether project is active")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    org_id: int = Field(..., description="Organization ID")
    client_pm_id: int = Field(..., description="Client PM user ID")
    our_pm_id: Optional[int] = Field(None, description="Our PM user ID")


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    requirements_text: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    our_pm_id: Optional[int] = None


class ProjectResponse(ProjectBase):
    """Schema for project responses."""
    project_id: int = Field(..., description="Project ID")
    org_id: int = Field(..., description="Organization ID")
    client_pm_id: int = Field(..., description="Client PM user ID")
    our_pm_id: Optional[int] = Field(None, description="Our PM user ID")
    date_created: datetime
    date_updated: datetime
    completed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """Schema for paginated project list responses."""
    items: List[ProjectResponse]
    total: int = Field(..., description="Total number of projects")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(50, description="Items per page")
    
    model_config = ConfigDict(from_attributes=True)

