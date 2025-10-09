"""
PDF Parsing API Routes (Azure Document Intelligence)
Handles PDF table extraction using Azure Document Intelligence API.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user
from app.core.logging import get_logger
from app.db.models import File as FileModel, FileTable, Project, FileStatus
from app.security.auth_stub import JWTPayload

logger = get_logger(__name__)
router = APIRouter()


# Response DTOs
class ParseResponse(BaseModel):
    """Response for parse request."""
    file_id: int
    message: str
    status: str


class ParseStatusResponse(BaseModel):
    """Response for parse status."""
    file_id: int
    file_name: str
    status: str
    tables_found: int
    processing_error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class TableBoundingBox(BaseModel):
    """Bounding box coordinates."""
    x: float
    y: float
    width: float
    height: float


class TableResponse(BaseModel):
    """Response for a single parsed table."""
    table_id: int
    file_id: int
    page_number: int
    bbox: Optional[TableBoundingBox] = None
    headers: List[List[str]]
    rows: List[List[str]]
    confidence: Optional[float] = None
    table_json: Optional[Dict[str, Any]] = None


class TablesListResponse(BaseModel):
    """Response for list of tables."""
    file_id: int
    tables: List[TableResponse]
    total: int


@router.post("/files/{file_id}/parse", response_model=ParseResponse)
async def trigger_file_parse(
    file_id: int,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Trigger PDF parsing using Azure Document Intelligence API.
    
    This endpoint:
    1. Validates file exists and is a PDF
    2. Starts background task to call Azure Document Intelligence
    3. Updates file status to 'processing'
    4. Returns immediately with task ID
    
    Args:
        file_id: File ID to parse
        current_user: Authenticated user
        db: Database session
        background_tasks: Background task queue
    
    Returns:
        ParseResponse with status
    """
    logger.info(f"User {current_user.user_id} triggering parse for file {file_id}")
    
    # 1. Validate file exists and user has access
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
    
    # 2. Validate file type
    if file_obj.mime_type and "pdf" not in file_obj.mime_type.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files can be parsed"
        )
    
    # 3. Check if already processing
    if file_obj.parse_status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File is already being processed"
        )
    
    # 4. Update status to processing
    file_obj.parse_status = "processing"
    await db.commit()
    
    # 5. TODO: Start background task to call Azure Document Intelligence
    # background_tasks.add_task(parse_with_azure, file_id, file_obj.file_path)
    logger.info(f"Parse task queued for file {file_id}")
    
    return ParseResponse(
        file_id=file_id,
        message="Parsing started successfully",
        status="processing"
    )


async def parse_with_azure(file_id: int, file_path: str, db: AsyncSession):
    """
    Background task to parse PDF with Azure Document Intelligence.
    
    This function:
    1. Downloads file from storage
    2. Calls Azure Document Intelligence API
    3. Extracts tables and structure
    4. Saves results to FileTable
    5. Updates file status
    
    Args:
        file_id: File ID
        file_path: Path to file in storage
        db: Database session
    """
    try:
        logger.info(f"Starting Azure parsing for file {file_id}")
        
        # TODO: Implement Azure Document Intelligence API call
        # This should:
        # 1. Download file from S3/MinIO
        # 2. Upload to Azure Document Intelligence
        # 3. Poll for results
        # 4. Extract tables
        # 5. Save to database
        
        # Placeholder: Mock parsing result
        mock_tables = [
            {
                "page_number": 1,
                "bbox": {"x": 0, "y": 0, "width": 200, "height": 100},
                "headers": [["Column A", "Column B"]],
                "rows": [["Value 1", "Value 2"], ["Value 3", "Value 4"]],
                "confidence": 0.95
            }
        ]
        
        # Save tables to database
        for table_data in mock_tables:
            table = FileTable(
                file_id=file_id,
                page_number=table_data["page_number"],
                table_json=table_data  # Store full JSON
            )
            db.add(table)
        
        # Update file status
        file_obj = await db.get(FileModel, file_id)
        if file_obj:
            file_obj.parse_status = "completed"
        
        await db.commit()
        logger.info(f"Azure parsing completed for file {file_id}")
        
    except Exception as e:
        logger.error(f"Azure parsing failed for file {file_id}: {e}")
        
        # Update file status to failed
        file_obj = await db.get(FileModel, file_id)
        if file_obj:
            file_obj.parse_status = "failed"
            file_obj.parse_error = str(e)
        await db.commit()


@router.get("/files/{file_id}/parse-status", response_model=ParseStatusResponse)
async def get_parse_status(
    file_id: int,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get parsing status for a file.
    
    Args:
        file_id: File ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        ParseStatusResponse with current status
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
    
    # Count tables
    tables_query = select(FileTable).where(FileTable.file_id == file_id)
    result = await db.execute(tables_query)
    tables = result.scalars().all()
    
    return ParseStatusResponse(
        file_id=file_id,
        file_name=file_obj.file_name,
        status=file_obj.parse_status or "pending",
        tables_found=len(tables),
        processing_error=file_obj.parse_error if hasattr(file_obj, 'parse_error') else None,
        created_at=file_obj.created_at.isoformat() if file_obj.created_at else None,
        completed_at=file_obj.updated_at.isoformat() if file_obj.parse_status == "completed" and file_obj.updated_at else None
    )


@router.get("/files/{file_id}/tables", response_model=TablesListResponse)
async def get_file_tables(
    file_id: int,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all extracted tables from a parsed file.
    
    Args:
        file_id: File ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        TablesListResponse with all tables
    """
    # Validate file access
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
    
    # Get all tables
    tables_query = select(FileTable).where(
        FileTable.file_id == file_id
    ).order_by(FileTable.page_number, FileTable.table_id)
    
    result = await db.execute(tables_query)
    tables = result.scalars().all()
    
    table_responses = []
    for table in tables:
        # Parse table_json if it exists
        table_data = table.table_json or {}
        
        # Extract bbox
        bbox_data = table_data.get("bbox")
        bbox = None
        if bbox_data:
            bbox = TableBoundingBox(
                x=bbox_data.get("x", 0),
                y=bbox_data.get("y", 0),
                width=bbox_data.get("width", 0),
                height=bbox_data.get("height", 0)
            )
        
        table_responses.append(
            TableResponse(
                table_id=table.table_id,
                file_id=table.file_id,
                page_number=table.page_number or 0,
                bbox=bbox,
                headers=table_data.get("headers", []),
                rows=table_data.get("rows", []),
                confidence=table_data.get("confidence"),
                table_json=table_data
            )
        )
    
    return TablesListResponse(
        file_id=file_id,
        tables=table_responses,
        total=len(table_responses)
    )


@router.get("/files/{file_id}/tables/{table_id}", response_model=TableResponse)
async def get_single_table(
    file_id: int,
    table_id: int,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific table by ID.
    
    Args:
        file_id: File ID
        table_id: Table ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        TableResponse with table details
    """
    # Validate file access
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
    
    # Get table
    table_query = select(FileTable).where(
        FileTable.table_id == table_id,
        FileTable.file_id == file_id
    )
    result = await db.execute(table_query)
    table = result.scalar_one_or_none()
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )
    
    # Parse table data
    table_data = table.table_json or {}
    bbox_data = table_data.get("bbox")
    bbox = None
    if bbox_data:
        bbox = TableBoundingBox(
            x=bbox_data.get("x", 0),
            y=bbox_data.get("y", 0),
            width=bbox_data.get("width", 0),
            height=bbox_data.get("height", 0)
        )
    
    return TableResponse(
        table_id=table.table_id,
        file_id=table.file_id,
        page_number=table.page_number or 0,
        bbox=bbox,
        headers=table_data.get("headers", []),
        rows=table_data.get("rows", []),
        confidence=table_data.get("confidence"),
        table_json=table_data
    )

