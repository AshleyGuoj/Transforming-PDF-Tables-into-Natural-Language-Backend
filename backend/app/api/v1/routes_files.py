"""
File Management API Routes
Handles file upload, replacement, and deletion for projects.
"""

from typing import List
import os
from pathlib import Path
from fastapi import APIRouter, Depends, File as FastAPIFile, UploadFile, HTTPException, BackgroundTasks, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user
from app.core.logging import get_logger
from app.db.models import File as FileModel, FileVersion, Project, User
from app.security.auth_stub import JWTPayload

logger = get_logger(__name__)
router = APIRouter()


# Response DTOs
class FileUploadResponse(BaseModel):
    """Response for file upload."""
    file_id: int
    file_name: str
    file_size: int
    version: int
    message: str


class FileResponse(BaseModel):
    """Response for file details."""
    file_id: int
    project_id: int
    file_name: str  # Mapped from name for API compatibility
    file_size: int  # Mapped from size_bytes for API compatibility
    mime_type: str
    created_at: str
    updated_at: str


class FileListResponse(BaseModel):
    """Response for file list."""
    files: List[FileResponse]
    total: int


@router.post("/projects/{project_id}/files", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file_to_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = FastAPIFile(..., description="File to upload"),
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file to a specific project.

    This endpoint:
    1. Validates the project exists and user has access
    2. Checks if a file with the same name already exists in this project
    3. Stores the file in storage (S3/MinIO)
    4. Creates File and FileVersion records
    5. Returns file metadata

    Note: File names must be unique within a project. If a file with the same name
    already exists, a 409 Conflict error will be returned. Different projects can
    have files with the same name.

    Args:
        project_id: Project ID to upload file to
        file: The uploaded file
        current_user: Authenticated user
        db: Database session
        background_tasks: Background task queue

    Returns:
        FileUploadResponse with file metadata

    Raises:
        HTTPException 404: Project not found or access denied
        HTTPException 409: File with same name already exists in this project
        HTTPException 413: File size exceeds maximum allowed size
    """
    try:
        logger.info(f"🚀 Upload started - User {current_user.user_id} uploading file to project {project_id}")
        logger.info(f"📄 File info: {file.filename}, content_type: {file.content_type}")

        # 1. Validate project exists and user has access
        project_query = select(Project).where(
            Project.project_id == project_id,
            Project.org_id == current_user.org_id,  # Multi-tenant check
            Project.is_active == True
        )
        result = await db.execute(project_query)
        project = result.scalar_one_or_none()

        if not project:
            logger.warning(f"Project {project_id} not found for org {current_user.org_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )

        # 2. Check if file with same name already exists in this project
        existing_file_query = select(FileModel).where(
            FileModel.project_id == project_id,
            FileModel.name == file.filename,
            FileModel.deleted_at.is_(None)
        )
        existing_file_result = await db.execute(existing_file_query)
        existing_file = existing_file_result.scalar_one_or_none()

        if existing_file:
            logger.warning(f"File with name '{file.filename}' already exists in project {project_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A file with the name '{file.filename}' already exists in this project. Please rename the file or delete the existing one first."
            )

        # 3. Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Validate file size (e.g., max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {max_size / (1024*1024)}MB"
            )

        # 4. Save file to local storage (for development)
        # In production, this should upload to S3/MinIO
        upload_dir = Path(f"uploads/projects/{project_id}/files")
        upload_dir.mkdir(parents=True, exist_ok=True)

        storage_path = upload_dir / file.filename
        with open(storage_path, "wb") as f:
            f.write(file_content)

        # Convert to string for database storage
        storage_path_str = str(storage_path)

        logger.info(f"File saved to {storage_path_str}")

        # 5. Create File record
        new_file = FileModel(
            project_id=project_id,
            name=file.filename,  # Fixed: file_name -> name
            size_bytes=file_size,  # Fixed: file_size -> size_bytes
            mime_type=file.content_type or "application/octet-stream",
            uploaded_by=current_user.user_id
        )
        db.add(new_file)
        await db.flush()  # Get file_id

        # 6. Create FileVersion record
        file_version = FileVersion(
            file_id=new_file.file_id,
            version_number=1,
            size_bytes=file_size,  # Fixed: file_size -> size_bytes
            storage_path=storage_path_str,  # Use string path
            uploaded_by=current_user.user_id
        )
        db.add(file_version)
        await db.flush()  # Get version_id

        # 7. Set active_version_id on File record
        new_file.active_version_id = file_version.version_id

        await db.commit()
        await db.refresh(new_file)

        logger.info(f"✅ File {new_file.file_id} uploaded successfully to project {project_id}")

        return FileUploadResponse(
            file_id=new_file.file_id,
            file_name=new_file.name,  # Fixed: file_name -> name
            file_size=file_size,
            version=1,
            message="File uploaded successfully"
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {type(e).__name__}: {str(e)}")
        logger.error(f"Stack trace:", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@router.get("/projects/{project_id}/files", response_model=FileListResponse)
async def list_project_files(
    project_id: int,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all files in a project.
    
    Args:
        project_id: Project ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        FileListResponse with list of files
    """
    # Validate project access
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
    
    # Get files
    files_query = select(FileModel).where(
        FileModel.project_id == project_id,
        FileModel.deleted_at.is_(None)
    ).order_by(FileModel.created_at.desc())
    
    result = await db.execute(files_query)
    files = result.scalars().all()
    
    file_responses = [
        FileResponse(
            file_id=f.file_id,
            project_id=f.project_id,
            file_name=f.name,  # Fixed: file_name -> name
            file_size=f.size_bytes or 0,  # Fixed: file_size -> size_bytes
            mime_type=f.mime_type or "application/octet-stream",
            created_at=f.created_at.isoformat() if f.created_at else "",
            updated_at=f.updated_at.isoformat() if f.updated_at else ""
        )
        for f in files
    ]
    
    return FileListResponse(
        files=file_responses,
        total=len(file_responses)
    )


@router.put("/files/{file_id}/replace", response_model=FileUploadResponse)
async def replace_file(
    file_id: int,
    file: UploadFile = FastAPIFile(..., description="Replacement file"),
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Replace an existing file with a new version.
    
    This endpoint:
    1. Validates file exists and user has access
    2. Uploads new version to storage
    3. Creates new FileVersion record
    4. Updates File record
    
    Args:
        file_id: File ID to replace
        file: New file content
        current_user: Authenticated user
        db: Database session
    
    Returns:
        FileUploadResponse with new version info
    """
    # 1. Get existing file
    file_query = select(FileModel).join(Project).where(
        FileModel.file_id == file_id,
        Project.org_id == current_user.org_id,
        FileModel.deleted_at.is_(None)
    )
    result = await db.execute(file_query)
    existing_file = result.scalar_one_or_none()
    
    if not existing_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # 2. Read new file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # 3. TODO: Upload to storage
    # Get current version number from versions relationship
    current_versions = await db.execute(
        select(FileVersion).where(FileVersion.file_id == file_id).order_by(FileVersion.version_number.desc())
    )
    latest_version = current_versions.scalars().first()
    new_version = (latest_version.version_number if latest_version else 0) + 1
    storage_path = f"projects/{existing_file.project_id}/files/v{new_version}_{file.filename}"

    # 4. Create new FileVersion
    file_version = FileVersion(
        file_id=file_id,
        version_number=new_version,
        size_bytes=file_size,  # Fixed: file_size -> size_bytes
        storage_path=storage_path,  # Fixed: file_path -> storage_path
        uploaded_by=current_user.user_id
    )
    db.add(file_version)

    # 5. Update File record
    existing_file.name = file.filename  # Fixed: file_name -> name
    existing_file.size_bytes = file_size  # Fixed: file_size -> size_bytes
    # Note: active_version_id should be updated to point to new version
    await db.flush()
    existing_file.active_version_id = file_version.version_id
    
    await db.commit()
    
    logger.info(f"File {file_id} replaced with version {new_version}")
    
    return FileUploadResponse(
        file_id=file_id,
        file_name=file.filename,
        file_size=file_size,
        version=new_version,
        message=f"File replaced successfully (version {new_version})"
    )


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a file.
    
    Args:
        file_id: File ID to delete
        current_user: Authenticated user
        db: Database session
    
    Returns:
        204 No Content on success
    """
    # Get file with access check
    file_query = select(FileModel).join(Project).where(
        FileModel.file_id == file_id,
        Project.org_id == current_user.org_id,
        FileModel.deleted_at.is_(None)
    )
    result = await db.execute(file_query)
    file_obj = result.scalar_one_or_none()
    
    if not file_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Soft delete
    from datetime import datetime
    file_obj.deleted_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"File {file_id} deleted by user {current_user.user_id}")
    
    return None

