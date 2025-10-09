"""
Database models package.
All models are imported from GrandscaleDB.
This module re-exports them for convenience.
"""

from app.db.base import (
    Base,
    # Core models
    Organization,
    Project,
    File,
    FileVersion,
    FileTable,
    User,
    AnnotationJob,
    # Event and audit
    EventLog,
    Review,
    Assignment,
    # RBAC
    Role,
    Permission,
    # Export
    ExportedFile,
    ExportLog,
    # Enums
    ProjectStatus,
    FileStatus,
    FileType,
    AnnotationJobStatus,
    ReviewStatus,
    EntityType,
    EventType,
    AssignmentRole,
    Language,
    JobPriority,
    # Mixins
    TimestampMixin,
)

# Aliases for backward compatibility with old code
PDFFile = File  # Old name -> new name
ParsedTable = FileTable  # Old name -> new name

__all__ = [
    "Base",
    # Core models
    "Organization",
    "Project",
    "File",
    "FileVersion",
    "FileTable",
    "User",
    "AnnotationJob",
    # Event and audit
    "EventLog",
    "Review",
    "Assignment",
    # RBAC
    "Role",
    "Permission",
    # Export
    "ExportedFile",
    "ExportLog",
    # Enums
    "ProjectStatus",
    "FileStatus",
    "FileType",
    "AnnotationJobStatus",
    "ReviewStatus",
    "EntityType",
    "EventType",
    "AssignmentRole",
    "Language",
    "JobPriority",
    # Mixins
    "TimestampMixin",
    # Backward compatibility aliases
    "PDFFile",
    "ParsedTable",
]

