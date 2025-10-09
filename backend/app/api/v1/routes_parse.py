"""
Parse API routes for PDF upload and processing.
Handles file upload, table extraction, and parse status tracking.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File as FastAPIFile, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user, require_annotator
from app.core.logging import get_logger
from app.db.models import File as FileModel, FileTable, FileStatus, Project
from app.security.auth_stub import JWTPayload

logger = get_logger(__name__)
router = APIRouter()


# Response DTOs
class ParseResponse(BaseModel):
    """Response for PDF parse request."""
    file_id: str
    file_name: str
    status: FileStatus
    message: str
    pages: Optional[int] = None
    tables_count: Optional[int] = None


class ParseStatusResponse(BaseModel):
    """Response for parse status check."""
    file_id: str
    file_name: str
    status: FileStatus
    total_pages: Optional[int] = None
    tables_found: int
    tables_by_detector: dict
    processing_error: Optional[str] = None
    created_at: str
    processing_started_at: Optional[str] = None
    processing_completed_at: Optional[str] = None


class TableSummary(BaseModel):
    """Summary of a parsed table."""
    table_id: str
    page_number: int
    detector: str
    confidence: float
    n_rows: int
    n_cols: int


@router.post("/parse", response_model=ParseResponse)
async def upload_and_parse_pdf(
    project_id: str = Form(..., description="Project ID to upload file to"),
    file: UploadFile = FastAPIFile(..., description="PDF file to process"),
    current_user: JWTPayload = Depends(require_annotator),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a PDF file and start table extraction processing.
    
    This endpoint:
    1. Validates the uploaded file
    2. Stores it in S3/MinIO with multi-tenant path
    3. Creates a PDFFile record
    4. Enqueues parsing job
    5. Returns file ID and initial status
    """
    logger.info(
        "PDF upload request",
        project_id=project_id,
        filename=file.filename,
        user_id=current_user.user_id,
        organization_id=current_user.organization_id
    )
    
    # Validate file
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Verify project exists and user has access
    project_query = select(Project).where(
        Project.id == UUID(project_id),
        Project.organization_id == UUID(current_user.organization_id),
        Project.is_active == True
    )
    project = await db.scalar(project_query)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Initialize storage service
        from app.services.storage_s3 import S3StorageService
        storage_service = S3StorageService()
        
        # Generate S3 object key
        s3_path = storage_service.generate_object_key(
            organization_id=current_user.organization_id,
            project_id=project_id,
            file_type="files",
            filename=file.filename
        )
        
        # Upload file to S3/MinIO
        upload_success = await storage_service.upload_file(
            file_content=file_content,
            object_key=s3_path,
            content_type=file.content_type or "application/pdf",
            metadata={
                "original_filename": file.filename,
                "uploaded_by": current_user.user_id,
                "project_id": project_id,
                "organization_id": current_user.organization_id
            }
        )
        
        if not upload_success:
            raise ValueError("Failed to upload file to storage")
        
        # Create PDF file record
        pdf_file = PDFFile(
            project_id=UUID(project_id),
            file_name=file.filename,
            s3_path=s3_path,
            file_size=file_size,
            mime_type=file.content_type,
            status=FileStatus.UPLOADED,
            uploaded_by=UUID(current_user.user_id)
        )
        
        db.add(pdf_file)
        await db.commit()
        await db.refresh(pdf_file)
        
        # Enqueue PDF processing as background task
        try:
            from app.workers.tasks_parse import process_pdf
            
            # Queue the PDF processing task
            celery_task = process_pdf.delay(str(pdf_file.id))
            
            logger.info(
                f"PDF processing queued",
                file_id=pdf_file.file_id,
                celery_task_id=celery_task.id
            )
            
            # Store celery task ID for tracking (optional)
            pdf_file.celery_task_id = celery_task.id
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to queue PDF processing: {e}", exc_info=True)
            pdf_file.status = FileStatus.FAILED
            pdf_file.processing_error = f"Failed to queue processing: {str(e)}"
            await db.commit()
        
        logger.info(
            "PDF file uploaded successfully",
            file_id=pdf_file.file_id,
            s3_path=s3_path,
            file_size=file_size
        )
        
        return ParseResponse(
            file_id=pdf_file.file_id,
            file_name=file.filename,
            status=pdf_file.status,
            message="File uploaded successfully. Processing has been queued and will begin shortly.",
            pages=pdf_file.total_pages,
            tables_count=None  # Will be populated after processing completes
        )
        
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload and process PDF"
        )


@router.get("/files/{file_id}/parse-status", response_model=ParseStatusResponse)
async def get_parse_status(
    file_id: str,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the parsing status of a PDF file.
    
    Returns detailed information about:
    - File processing status
    - Number of tables found
    - Tables grouped by detector
    - Any processing errors
    """
    logger.info(
        "Parse status request",
        file_id=file_id,
        user_id=current_user.user_id
    )
    
    # Get PDF file with organization access check
    file_query = select(PDFFile).join(Project).where(
        PDFFile.id == UUID(file_id),
        Project.organization_id == UUID(current_user.organization_id)
    )
    pdf_file = await db.scalar(file_query)
    
    if not pdf_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or access denied"
        )
    
    # Get parsed tables
    tables_query = select(ParsedTable).where(
        ParsedTable.file_id == UUID(file_id)
    )
    tables = (await db.execute(tables_query)).scalars().all()
    
    # Group tables by detector
    tables_by_detector = {}
    for table in tables:
        detector = table.detector
        if detector not in tables_by_detector:
            tables_by_detector[detector] = 0
        tables_by_detector[detector] += 1
    
    return ParseStatusResponse(
        file_id=file_id,
        file_name=pdf_file.file_name,
        status=pdf_file.status,
        total_pages=pdf_file.total_pages,
        tables_found=len(tables),
        tables_by_detector=tables_by_detector,
        processing_error=pdf_file.processing_error,
        created_at=pdf_file.created_at.isoformat(),
        processing_started_at=pdf_file.processing_started_at,
        processing_completed_at=pdf_file.processing_completed_at
    )


@router.get("/files/{file_id}/tables", response_model=List[TableSummary])
async def get_file_tables(
    file_id: str,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary of all tables extracted from a PDF file.
    
    Returns basic information about each table without the full schema.
    """
    logger.info(
        "File tables request",
        file_id=file_id,
        user_id=current_user.user_id
    )
    
    # Verify file access
    file_query = select(PDFFile).join(Project).where(
        PDFFile.id == UUID(file_id),
        Project.organization_id == UUID(current_user.organization_id)
    )
    pdf_file = await db.scalar(file_query)
    
    if not pdf_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or access denied"
        )
    
    # Get tables
    tables_query = select(ParsedTable).where(
        ParsedTable.file_id == UUID(file_id)
    ).order_by(ParsedTable.page_number, ParsedTable.created_at)
    
    tables = (await db.execute(tables_query)).scalars().all()
    
    return [
        TableSummary(
            table_id=table.table_id,
            page_number=table.page_number,
            detector=table.detector,
            confidence=table.confidence,
            n_rows=table.schema_json.get("n_rows", 0),
            n_cols=table.schema_json.get("n_cols", 0)
        )
        for table in tables
    ]


@router.get("/files/{file_id}/tables/{table_id}")
async def get_table_schema(
    file_id: str,
    table_id: str,
    current_user: JWTPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the full unified schema for a specific table.
    
    Returns the complete JSON schema including all cells and metadata.
    """
    logger.info(
        "Table schema request",
        file_id=file_id,
        table_id=table_id,
        user_id=current_user.user_id
    )
    
    # Get table with access check
    table_query = select(ParsedTable).join(PDFFile).join(Project).where(
        ParsedTable.id == UUID(table_id),
        ParsedTable.file_id == UUID(file_id),
        Project.organization_id == UUID(current_user.organization_id)
    )
    table = await db.scalar(table_query)
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found or access denied"
        )
    
    return table.schema_json 