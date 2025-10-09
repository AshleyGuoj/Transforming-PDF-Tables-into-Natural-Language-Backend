"""
Pydantic schemas for Annotation, Assignment, and Review models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AnnotationJobBase(BaseModel):
    """Base schema for AnnotationJob with common fields."""
    file_id: int = Field(..., description="File ID")
    project_id: int = Field(..., description="Project ID")
    language: Optional[str] = Field(None, description="Annotation language")
    priority: str = Field("medium", description="Job priority")
    status: str = Field("not_started", description="Job status")
    review_status: str = Field("pending", description="Review status")
    is_active: bool = Field(True, description="Whether job is active")


class AnnotationJobCreate(AnnotationJobBase):
    """Schema for creating a new annotation job."""
    due_date: Optional[datetime] = Field(None, description="Job due date")


class AnnotationJobUpdate(BaseModel):
    """Schema for updating an annotation job."""
    language: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    review_status: Optional[str] = None
    is_active: Optional[bool] = None
    due_date: Optional[datetime] = None


class AnnotationJobResponse(AnnotationJobBase):
    """Schema for annotation job responses."""
    job_id: int = Field(..., description="Job ID")
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class AssignmentResponse(BaseModel):
    """Schema for assignment responses."""
    assignment_id: int = Field(..., description="Assignment ID")
    job_id: int = Field(..., description="Job ID")
    user_id: int = Field(..., description="User ID")
    role: str = Field(..., description="Assignment role")
    status: str = Field("assigned", description="Assignment status")
    is_active: bool = Field(True, description="Whether assignment is active")
    assigned_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ReviewResponse(BaseModel):
    """Schema for review responses."""
    review_id: int = Field(..., description="Review ID")
    job_id: int = Field(..., description="Job ID")
    reviewer_id: Optional[int] = Field(None, description="Reviewer user ID")
    status: str = Field("pending", description="Review status")
    feedback: Optional[str] = Field(None, description="Review feedback")
    is_active: bool = Field(True, description="Whether review is active")
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

