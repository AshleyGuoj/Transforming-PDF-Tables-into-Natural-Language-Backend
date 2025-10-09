"""
CRUD operations for Project model.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.models import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate


# ============================================================
# Async CRUD Operations (for FastAPI)
# ============================================================

async def get_project(db: AsyncSession, project_id: int) -> Optional[Project]:
    """Get a single project by ID."""
    result = await db.execute(select(Project).where(Project.project_id == project_id))
    return result.scalar_one_or_none()


async def get_projects(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    org_id: Optional[int] = None,
    status: Optional[str] = None,
    is_active: bool = True,
) -> List[Project]:
    """Get a list of projects with optional filtering."""
    query = select(Project).where(Project.is_active == is_active)
    
    if org_id:
        query = query.where(Project.org_id == org_id)
    if status:
        query = query.where(Project.status == status)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_project(db: AsyncSession, project_data: ProjectCreate) -> Project:
    """Create a new project."""
    project = Project(
        org_id=project_data.org_id,
        name=project_data.name,
        description=project_data.description,
        requirements_text=project_data.requirements_text,
        status=project_data.status,
        is_active=project_data.is_active,
        client_pm_id=project_data.client_pm_id,
        our_pm_id=project_data.our_pm_id,
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def update_project(
    db: AsyncSession,
    project_id: int,
    project_data: ProjectUpdate,
) -> Optional[Project]:
    """Update an existing project."""
    project = await get_project(db, project_id)
    if not project:
        return None
    
    # Update only provided fields
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project_id: int) -> bool:
    """Soft delete a project."""
    project = await get_project(db, project_id)
    if not project:
        return False
    
    project.is_active = False
    from datetime import datetime
    project.deleted_at = datetime.utcnow()
    
    await db.commit()
    return True


# ============================================================
# Sync CRUD Operations (for Celery workers)
# ============================================================

def get_project_sync(db: Session, project_id: int) -> Optional[Project]:
    """Get a single project by ID (sync)."""
    return db.query(Project).filter(Project.project_id == project_id).first()


def get_projects_sync(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    org_id: Optional[int] = None,
) -> List[Project]:
    """Get a list of projects (sync)."""
    query = db.query(Project).filter(Project.is_active == True)
    
    if org_id:
        query = query.filter(Project.org_id == org_id)
    
    return query.offset(skip).limit(limit).all()

