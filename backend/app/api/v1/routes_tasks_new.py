"""
Annotation Task Management API Routes
Handles task creation, assignment, and draft generation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user
from app.core.logging import get_logger
from app.db.models import (
    AnnotationJob, FileTable, Project, User, Assignment,
    AnnotationJobStatus, AssignmentRole
)
from app.security.auth_stub import JWTPayload

logger = get_logger(__name__)
router = APIRouter()


# Request/Response DTOs
class TaskCreateRequest(BaseModel):
    """Request to create a new annotation task."""
    file_id: int
    table_ids: List[int]
    assigned_to: Optional[int] = None
    instructions: Optional[str] = None


class BulkTaskCreateRequest(BaseModel):
    """Request to bulk create tasks for all tables in a file."""
    file_id: int
    assigned_to: Optional[int] = None


class TaskResponse(BaseModel):
    """Response for a single task."""
    job_id: int
    project_id: int
    file_id: int
    table_id: Optional[int] = None
    status: str
    assigned_to: Optional[int] = None
    created_at: str
    updated_at: Optional[str] = None


class TaskListResponse(BaseModel):
    """Response for list of tasks."""
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int


class DraftGenerateRequest(BaseModel):
    """Request to generate AI draft for a task."""
    model_name: Optional[str] = "gpt-4"
    force_regenerate: bool = False


class DraftResponse(BaseModel):
    """Response for draft generation."""
    job_id: int
    message: str
    status: str


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_annotation_task(
    request: TaskCreateRequest,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new annotation task for specific tables.
    
    Args:
        request: Task creation request
        current_user: Authenticated user
        db: Database session
    
    Returns:
        TaskResponse with created task details
    """
    logger.info(f"Creating annotation task for file {request.file_id}")
    
    # TODO: Validate file and tables exist
    # TODO: Create AnnotationJob records
    # TODO: Create Assignment if assigned_to is provided
    
    # Placeholder implementation
    new_job = AnnotationJob(
        project_id=1,  # TODO: Get from file
        status=AnnotationJobStatus.not_started,
        created_by=current_user.user_id
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    
    return TaskResponse(
        job_id=new_job.job_id,
        project_id=new_job.project_id,
        file_id=request.file_id,
        table_id=request.table_ids[0] if request.table_ids else None,
        status=new_job.status.value,
        assigned_to=request.assigned_to,
        created_at=new_job.created_at.isoformat() if new_job.created_at else "",
        updated_at=new_job.updated_at.isoformat() if new_job.updated_at else None
    )


@router.post("/tasks/bulk-create", response_model=TaskListResponse)
async def bulk_create_tasks(
    request: BulkTaskCreateRequest,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk create annotation tasks for all tables in a file.
    
    This endpoint:
    1. Gets all tables from the specified file
    2. Creates one AnnotationJob per table
    3. Optionally assigns to a user
    
    Args:
        request: Bulk creation request
        current_user: Authenticated user
        db: Database session
    
    Returns:
        TaskListResponse with all created tasks
    """
    logger.info(f"Bulk creating tasks for file {request.file_id}")

    # Get all tables for the file and verify file exists
    tables_query = select(FileTable).where(FileTable.file_id == request.file_id)
    result = await db.execute(tables_query)
    tables = result.scalars().all()

    if not tables:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tables found for this file"
        )

    # Get file to obtain project_id
    from GrandscaleDB.models import File
    file_query = select(File).where(File.file_id == request.file_id)
    file_result = await db.execute(file_query)
    file_obj = file_result.scalar_one_or_none()

    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    project_id = file_obj.project_id
    logger.info(f"Creating tasks for file {request.file_id} in project {project_id}")

    # Create tasks
    created_tasks = []
    for table in tables:
        job = AnnotationJob(
            project_id=project_id,
            table_id=table.table_id,
            status=AnnotationJobStatus.not_started
        )
        db.add(job)
        await db.flush()
        
        # Create assignment if needed
        if request.assigned_to:
            assignment = Assignment(
                job_id=job.job_id,
                user_id=request.assigned_to,
                role=AssignmentRole.annotator
            )
            db.add(assignment)
        
        created_tasks.append(
            TaskResponse(
                job_id=job.job_id,
                project_id=job.project_id,
                file_id=request.file_id,
                table_id=table.table_id,
                status=job.status.value,
                assigned_to=request.assigned_to,
                created_at=job.created_at.isoformat() if job.created_at else "",
                updated_at=None
            )
        )
    
    await db.commit()
    
    logger.info(f"Created {len(created_tasks)} tasks for file {request.file_id}")
    
    return TaskListResponse(
        tasks=created_tasks,
        total=len(created_tasks),
        page=1,
        page_size=len(created_tasks)
    )


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    assigned_to: Optional[int] = None,
    page: int = 1,
    page_size: int = 50,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List annotation tasks with optional filters.
    
    Args:
        project_id: Filter by project
        status: Filter by status
        assigned_to: Filter by assignee
        page: Page number
        page_size: Items per page
        current_user: Authenticated user
        db: Database session
    
    Returns:
        TaskListResponse with filtered tasks
    """
    # Build query
    query = select(AnnotationJob).join(Project).where(
        Project.org_id == current_user.org_id
    )
    
    if project_id:
        query = query.where(AnnotationJob.project_id == project_id)
    
    if status:
        query = query.where(AnnotationJob.status == status)
    
    # Execute query
    query = query.order_by(AnnotationJob.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(AnnotationJob.job_id)).join(Project).where(
        Project.org_id == current_user.org_id
    )
    if project_id:
        count_query = count_query.where(AnnotationJob.project_id == project_id)
    if status:
        count_query = count_query.where(AnnotationJob.status == status)
    
    result = await db.execute(count_query)
    total = result.scalar()
    
    tasks = [
        TaskResponse(
            job_id=job.job_id,
            project_id=job.project_id,
            file_id=0,  # TODO: Link to file
            table_id=None,
            status=job.status.value,
            assigned_to=None,  # TODO: Get from Assignment
            created_at=job.created_at.isoformat() if job.created_at else "",
            updated_at=job.updated_at.isoformat() if job.updated_at else None
        )
        for job in jobs
    ]
    
    return TaskListResponse(
        tasks=tasks,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/tasks/{job_id}", response_model=TaskResponse)
async def get_task(
    job_id: int,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific task.
    
    Args:
        job_id: Job ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        TaskResponse with task details
    """
    query = select(AnnotationJob).join(Project).where(
        AnnotationJob.job_id == job_id,
        Project.org_id == current_user.org_id
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return TaskResponse(
        job_id=job.job_id,
        project_id=job.project_id,
        file_id=0,  # TODO
        table_id=None,
        status=job.status.value,
        assigned_to=None,
        created_at=job.created_at.isoformat() if job.created_at else "",
        updated_at=job.updated_at.isoformat() if job.updated_at else None
    )


@router.post("/tasks/{job_id}/generate-draft", response_model=DraftResponse)
async def generate_draft(
    job_id: int,
    request: DraftGenerateRequest,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Generate AI draft for an annotation task.
    
    This endpoint:
    1. Validates task exists and is in correct status
    2. Queues background task to call AI model
    3. Updates task status to 'in_progress'
    4. Returns immediately
    
    Args:
        job_id: Job ID
        request: Draft generation request
        current_user: Authenticated user
        db: Database session
        background_tasks: Background task queue
    
    Returns:
        DraftResponse with status
    """
    logger.info(f"Generating draft for job {job_id}")
    
    # Get job
    query = select(AnnotationJob).join(Project).where(
        AnnotationJob.job_id == job_id,
        Project.org_id == current_user.org_id
    )
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Update status
    job.status = AnnotationJobStatus.in_progress
    await db.commit()
    
    # TODO: Queue background task to generate draft
    # background_tasks.add_task(generate_ai_draft, job_id, request.model_name)
    
    logger.info(f"Draft generation queued for job {job_id}")
    
    return DraftResponse(
        job_id=job_id,
        message="Draft generation started",
        status="in_progress"
    )

