"""
API routes for Project management.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)
from app.crud import project as project_crud

router = APIRouter()


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    org_id: int = Query(None, description="Filter by organization ID"),
    status: str = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a list of projects with optional filtering.
    
    - **skip**: Pagination offset
    - **limit**: Number of results per page
    - **org_id**: Filter by organization
    - **status**: Filter by project status
    """
    projects = await project_crud.get_projects(
        db=db,
        skip=skip,
        limit=limit,
        org_id=org_id,
        status=status,
    )
    
    # Get total count (simplified - in production use a count query)
    total = len(projects)
    
    return ProjectListResponse(
        items=projects,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific project by ID.
    """
    project = await project_crud.get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new project.
    
    - **org_id**: Organization ID (required)
    - **name**: Project name (required)
    - **description**: Project description
    - **client_pm_id**: Client PM user ID (required)
    - **our_pm_id**: Our PM user ID
    """
    project = await project_crud.create_project(db=db, project_data=project_data)
    return project


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing project.
    
    Only provided fields will be updated.
    """
    project = await project_crud.update_project(
        db=db,
        project_id=project_id,
        project_data=project_data,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a project (sets is_active=False).
    """
    success = await project_crud.delete_project(db=db, project_id=project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return None

