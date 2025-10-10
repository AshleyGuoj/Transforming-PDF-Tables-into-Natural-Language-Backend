"""
Simple Project API routes using raw SQL to bypass ORM relationship issues.
This is a temporary workaround until GrandscaleDB models are fixed.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


# --- Pydantic Models ---
class ProjectCreate(BaseModel):
    org_id: int
    name: str
    description: Optional[str] = None
    client_pm_id: int
    our_pm_id: Optional[int] = None


class ProjectResponse(BaseModel):
    project_id: int
    org_id: int
    name: str
    description: Optional[str] = None
    status: str
    is_active: bool
    client_pm_id: int
    our_pm_id: Optional[int] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# --- API Routes ---
@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    org_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get list of projects using raw SQL."""
    if org_id:
        query = text("""
            SELECT project_id, org_id, name, description, status, is_active,
                   client_pm_id, our_pm_id, created_at, updated_at
            FROM project
            WHERE is_active = true AND org_id = :org_id
            ORDER BY created_at DESC
        """)
        result = await db.execute(query, {"org_id": org_id})
    else:
        query = text("""
            SELECT project_id, org_id, name, description, status, is_active,
                   client_pm_id, our_pm_id, created_at, updated_at
            FROM project
            WHERE is_active = true
            ORDER BY created_at DESC
        """)
        result = await db.execute(query)

    projects = []
    for row in result:
        projects.append(ProjectResponse(
            project_id=row[0],
            org_id=row[1],
            name=row[2],
            description=row[3],
            status=row[4],
            is_active=row[5],
            client_pm_id=row[6],
            our_pm_id=row[7],
            created_at=str(row[8]),
            updated_at=str(row[9]) if row[9] else None,
        ))

    return projects


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new project using raw SQL."""
    query = text("""
        INSERT INTO project (org_id, name, description, client_pm_id, our_pm_id, status, is_active)
        VALUES (:org_id, :name, :description, :client_pm_id, :our_pm_id, 'draft', true)
        RETURNING project_id, org_id, name, description, status, is_active,
                  client_pm_id, our_pm_id, created_at, updated_at
    """)

    result = await db.execute(query, {
        "org_id": project.org_id,
        "name": project.name,
        "description": project.description,
        "client_pm_id": project.client_pm_id,
        "our_pm_id": project.our_pm_id,
    })

    await db.commit()

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create project")

    return ProjectResponse(
        project_id=row[0],
        org_id=row[1],
        name=row[2],
        description=row[3],
        status=row[4],
        is_active=row[5],
        client_pm_id=row[6],
        our_pm_id=row[7],
        created_at=str(row[8]),
        updated_at=str(row[9]) if row[9] else None,
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a project by ID using raw SQL."""
    query = text("""
        SELECT project_id, org_id, name, description, status, is_active,
               client_pm_id, our_pm_id, created_at, updated_at
        FROM project
        WHERE project_id = :project_id AND is_active = true
    """)

    result = await db.execute(query, {"project_id": project_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(
        project_id=row[0],
        org_id=row[1],
        name=row[2],
        description=row[3],
        status=row[4],
        is_active=row[5],
        client_pm_id=row[6],
        our_pm_id=row[7],
        created_at=str(row[8]),
        updated_at=str(row[9]) if row[9] else None,
    )
