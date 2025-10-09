"""
Pydantic schemas for File and FileVersion models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FileBase(BaseModel):
    """Base schema for File with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="File name")
    description: Optional[str] = Field(None, description="File description")
    file_type: str = Field("dataset", description="File type")
    status: str = Field("pending", description="File status")
    is_active: bool = Field(True, description="Whether file is active")


class FileCreate(FileBase):
    """Schema for creating a new file."""
    project_id: int = Field(..., description="Project ID")
    uploaded_by: int = Field(..., description="Uploader user ID")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")


class FileUpdate(BaseModel):
    """Schema for updating a file."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class FileVersionResponse(BaseModel):
    """Schema for file version responses."""
    version_id: int = Field(..., description="Version ID")
    file_id: int = Field(..., description="File ID")
    version_number: int = Field(..., description="Version number")
    storage_path: str = Field(..., description="Storage path")
    checksum: Optional[str] = Field(None, description="File checksum")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    uploaded_by: Optional[int] = Field(None, description="Uploader user ID")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    is_active: bool = Field(True, description="Whether version is active")
    generation_method: str = Field("upload", description="Generation method")
    llm_model: Optional[str] = Field(None, description="LLM model used if generated")
    
    model_config = ConfigDict(from_attributes=True)


class FileResponse(FileBase):
    """Schema for file responses."""
    file_id: int = Field(..., description="File ID")
    project_id: int = Field(..., description="Project ID")
    uploaded_by: int = Field(..., description="Uploader user ID")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    date_created: datetime
    date_updated: datetime
    deleted_at: Optional[datetime] = None
    active_version_id: Optional[int] = Field(None, description="Active version ID")
    
    model_config = ConfigDict(from_attributes=True)

