"""
API v1 routes package.
Exports all API route modules for easy importing.
"""

from app.api.v1 import (
    routes_projects,
    routes_files,
    routes_parse_azure,
    routes_tasks_new,
    routes_export_new
)

__all__ = [
    "routes_projects",
    "routes_files",
    "routes_parse_azure",
    "routes_tasks_new",
    "routes_export_new"
]

