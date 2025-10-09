"""
SQLAlchemy base class and model imports.
Integrates GrandscaleDB models with FastAPI backend.
"""

# Import Base from GrandscaleDB models
import sys
from pathlib import Path

# Add GrandscaleDB to Python path
grandscale_db_path = Path(__file__).parent.parent.parent / "GrandscaleDB"
sys.path.insert(0, str(grandscale_db_path))

# Import Base from GrandscaleDB - using consolidated models.py
from models import Base  # noqa: E402

# Import all models to ensure they are registered with SQLAlchemy
# This is critical for Alembic migrations to detect all tables
from models import (  # noqa: E402, F401
    # Core tables
    Organization,
    Project,
    File,
    FileVersion,
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

# Try to import FileTable if it exists
try:
    from models import FileTable  # noqa: E402, F401
except ImportError:
    FileTable = None

# Export Base for use in other modules
__all__ = [
    "Base",
    # Core models
    "Organization",
    "Project",
    "File",
    "FileVersion",
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
]

if FileTable is not None:
    __all__.append("FileTable")
