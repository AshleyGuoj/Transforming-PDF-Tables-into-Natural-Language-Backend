"""
CRUD operations package.
Provides database access functions for all models.
"""

from .project import (
    get_project,
    get_projects,
    create_project,
    update_project,
    delete_project,
)

from .file import (
    get_file,
    get_files,
    create_file,
    update_file,
    delete_file,
)

from .annotation import (
    get_annotation_job,
    get_annotation_jobs,
    create_annotation_job,
    update_annotation_job,
    delete_annotation_job,
)

from .organization import (
    get_organization,
    get_organizations,
    create_organization,
    update_organization,
    delete_organization,
)

from .user import (
    get_user,
    get_user_by_email,
    get_users,
    create_user,
    update_user,
    delete_user,
)

__all__ = [
    # Project CRUD
    "get_project",
    "get_projects",
    "create_project",
    "update_project",
    "delete_project",
    # File CRUD
    "get_file",
    "get_files",
    "create_file",
    "update_file",
    "delete_file",
    # Annotation CRUD
    "get_annotation_job",
    "get_annotation_jobs",
    "create_annotation_job",
    "update_annotation_job",
    "delete_annotation_job",
    # Organization CRUD
    "get_organization",
    "get_organizations",
    "create_organization",
    "update_organization",
    "delete_organization",
    # User CRUD
    "get_user",
    "get_user_by_email",
    "get_users",
    "create_user",
    "update_user",
    "delete_user",
]

