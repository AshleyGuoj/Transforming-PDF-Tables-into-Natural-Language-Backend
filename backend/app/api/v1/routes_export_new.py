"""
Export API Routes
Handles project and file export functionality.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import json
import io

from app.core.deps import get_db, get_current_user
from app.core.logging import get_logger
from app.db.models import (
    Project, File as FileModel, FileTable, AnnotationJob, ExportLog,
    User, Organization
)
from app.security.auth_stub import JWTPayload

logger = get_logger(__name__)
router = APIRouter()


# Request/Response DTOs
class ExportRequest(BaseModel):
    """Request to export project data."""
    format: str = "json"  # json, csv, excel
    include_files: bool = True
    include_tables: bool = True
    include_annotations: bool = True


class ExportResponse(BaseModel):
    """Response for export request."""
    export_id: int
    project_id: int
    format: str
    status: str
    message: str
    download_url: Optional[str] = None


class ExportListResponse(BaseModel):
    """Response for list of exports."""
    exports: List[ExportResponse]
    total: int


@router.post("/projects/{project_id}/export", response_model=ExportResponse)
async def export_project(
    project_id: int,
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export project data in specified format.
    
    This endpoint:
    1. Validates project exists and user has access
    2. Creates ExportLog record
    3. Queues background task to generate export file
    4. Returns export ID for status tracking
    
    Supported formats:
    - json: Complete project data in JSON
    - csv: Tables as CSV files (zipped)
    - excel: Multi-sheet Excel workbook
    
    Args:
        project_id: Project ID to export
        request: Export configuration
        current_user: Authenticated user
        db: Database session
        background_tasks: Background task queue
    
    Returns:
        ExportResponse with export status
    """
    logger.info(f"User {current_user.user_id} exporting project {project_id}")
    
    # 1. Validate project exists and access
    project_query = select(Project).where(
        Project.project_id == project_id,
        Project.org_id == current_user.org_id,
        Project.is_active == True
    )
    result = await db.execute(project_query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # 2. Validate format
    allowed_formats = ["json", "csv", "excel"]
    if request.format not in allowed_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format. Allowed: {', '.join(allowed_formats)}"
        )
    
    # 3. Create export log
    export_log = ExportLog(
        project_id=project_id,
        exported_by=current_user.user_id,
        export_format=request.format,
        export_status="pending"
    )
    db.add(export_log)
    await db.commit()
    await db.refresh(export_log)
    
    # 4. TODO: Queue background task
    # background_tasks.add_task(
    #     generate_export_file,
    #     export_log.export_id,
    #     project_id,
    #     request
    # )
    
    logger.info(f"Export {export_log.export_id} queued for project {project_id}")
    
    return ExportResponse(
        export_id=export_log.export_id,
        project_id=project_id,
        format=request.format,
        status="pending",
        message="Export queued successfully"
    )


@router.get("/projects/{project_id}/export", response_model=ExportListResponse)
async def list_project_exports(
    project_id: int,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all exports for a project.
    
    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        ExportListResponse with list of exports
    """
    # Validate project access
    project_query = select(Project).where(
        Project.project_id == project_id,
        Project.org_id == current_user.org_id
    )
    result = await db.execute(project_query)
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get exports
    exports_query = select(ExportLog).where(
        ExportLog.project_id == project_id
    ).order_by(ExportLog.exported_at.desc())
    
    result = await db.execute(exports_query)
    exports = result.scalars().all()
    
    export_responses = [
        ExportResponse(
            export_id=exp.export_id,
            project_id=exp.project_id,
            format=exp.export_format or "json",
            status=exp.export_status or "completed",
            message="Export completed",
            download_url=f"/api/v1/exports/{exp.export_id}/download" if exp.export_status == "completed" else None
        )
        for exp in exports
    ]
    
    return ExportListResponse(
        exports=export_responses,
        total=len(export_responses)
    )


@router.get("/exports/{export_id}/status", response_model=ExportResponse)
async def get_export_status(
    export_id: int,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get status of an export.
    
    Args:
        export_id: Export ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        ExportResponse with current status
    """
    # Get export with project access check
    export_query = select(ExportLog).join(Project).where(
        ExportLog.export_id == export_id,
        Project.org_id == current_user.org_id
    )
    result = await db.execute(export_query)
    export_log = result.scalar_one_or_none()
    
    if not export_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    return ExportResponse(
        export_id=export_log.export_id,
        project_id=export_log.project_id,
        format=export_log.export_format or "json",
        status=export_log.export_status or "pending",
        message=f"Export is {export_log.export_status}",
        download_url=f"/api/v1/exports/{export_id}/download" if export_log.export_status == "completed" else None
    )


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: int,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download exported file.
    
    Args:
        export_id: Export ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        StreamingResponse with file content
    """
    # Get export with access check
    export_query = select(ExportLog).join(Project).where(
        ExportLog.export_id == export_id,
        Project.org_id == current_user.org_id
    )
    result = await db.execute(export_query)
    export_log = result.scalar_one_or_none()
    
    if not export_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    if export_log.export_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export is not ready. Current status: {export_log.export_status}"
        )
    
    # TODO: Download file from S3/MinIO
    # For now, return placeholder JSON
    project_query = select(Project).where(Project.project_id == export_log.project_id)
    result = await db.execute(project_query)
    project = result.scalar_one()
    
    export_data = {
        "export_id": export_log.export_id,
        "project": {
            "project_id": project.project_id,
            "name": project.name,
            "description": project.description,
            "status": project.status.value if hasattr(project.status, 'value') else str(project.status)
        },
        "exported_at": export_log.exported_at.isoformat() if export_log.exported_at else datetime.utcnow().isoformat(),
        "exported_by": export_log.exported_by,
        "format": export_log.export_format
    }
    
    # Create file stream
    json_str = json.dumps(export_data, indent=2)
    file_stream = io.BytesIO(json_str.encode())
    
    filename = f"project_{export_log.project_id}_export_{export_id}.json"
    
    return StreamingResponse(
        file_stream,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.delete("/exports/{export_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_export(
    export_id: int,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an export record and associated file.
    
    Args:
        export_id: Export ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        204 No Content
    """
    # Get export with access check
    export_query = select(ExportLog).join(Project).where(
        ExportLog.export_id == export_id,
        Project.org_id == current_user.org_id
    )
    result = await db.execute(export_query)
    export_log = result.scalar_one_or_none()
    
    if not export_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found"
        )
    
    # TODO: Delete file from S3/MinIO
    
    # Delete record
    await db.delete(export_log)
    await db.commit()
    
    logger.info(f"Export {export_id} deleted by user {current_user.user_id}")
    
    return None

