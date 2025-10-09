"""
Pydantic schemas package for API request/response validation.
All schemas are defined here for use with FastAPI endpoints.
"""

from .project import (
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)

from .file import (
    FileBase,
    FileCreate,
    FileUpdate,
    FileResponse,
    FileVersionResponse,
)

from .annotation import (
    AnnotationJobBase,
    AnnotationJobCreate,
    AnnotationJobUpdate,
    AnnotationJobResponse,
    AssignmentResponse,
    ReviewResponse,
)

from .organization import (
    OrganizationBase,
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
)

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
)

__all__ = [
    # Project schemas
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectListResponse",
    # File schemas
    "FileBase",
    "FileCreate",
    "FileUpdate",
    "FileResponse",
    "FileVersionResponse",
    # Annotation schemas
    "AnnotationJobBase",
    "AnnotationJobCreate",
    "AnnotationJobUpdate",
    "AnnotationJobResponse",
    "AssignmentResponse",
    "ReviewResponse",
    # Organization schemas
    "OrganizationBase",
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
]

