"""
PDF Parsing API Routes (Azure Document Intelligence)
Handles PDF table extraction using Azure Document Intelligence API.
"""

from typing import List, Optional, Dict, Any
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

from app.core.deps import get_db, get_current_user
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import File as FileModel, FileTable, Project, FileStatus, FileVersion
from app.db.session import get_async_session
from app.security.auth_stub import JWTPayload

settings = get_settings()

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
    page_count: int
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
    if file_obj.status == FileStatus.in_progress:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File is already being processed"
        )

    # 4. Get storage path from active version
    storage_path = None
    if file_obj.active_version_id:
        version_query = select(FileVersion).where(FileVersion.version_id == file_obj.active_version_id)
        version_result = await db.execute(version_query)
        version_obj = version_result.scalar_one_or_none()
        if version_obj:
            storage_path = version_obj.storage_path

    if not storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File has no storage path - cannot parse"
        )

    # 5. Update status to in_progress (processing)
    file_obj.status = FileStatus.in_progress
    await db.commit()

    # 6. Start background task to call Azure Document Intelligence
    background_tasks.add_task(parse_with_azure, file_id, storage_path)
    logger.info(f"Parse task queued for file {file_id} with storage path {storage_path}")
    
    return ParseResponse(
        file_id=file_id,
        message="Parsing started successfully",
        status="processing"
    )


async def parse_with_azure(file_id: int, file_path: str):
    """
    Background task to parse PDF with Azure Document Intelligence.

    This function:
    1. Reads file from storage
    2. Calls Azure Document Intelligence API
    3. Extracts tables and structure
    4. Saves results to FileTable
    5. Updates file status

    Args:
        file_id: File ID
        file_path: Path to file in storage (relative or absolute)
    """
    # Create new database session for background task
    async with get_async_session() as db:
        try:
            logger.info(f"Starting Azure parsing for file {file_id}")

            # 1. Validate Azure credentials
            if not settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT or not settings.AZURE_DOCUMENT_INTELLIGENCE_KEY:
                raise ValueError("Azure Document Intelligence credentials not configured")

            # 2. Read PDF file from storage
            # For now, assume file_path is a local path (could be S3 path in production)
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found at path: {file_path}")

            with open(file_path, "rb") as f:
                pdf_bytes = f.read()

            logger.info(f"Read {len(pdf_bytes)} bytes from {file_path}")

            # 3. Initialize Azure Document Intelligence client
            client = DocumentIntelligenceClient(
                endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY)
            )

            # 4. Call Azure API to analyze document with prebuilt-layout model
            logger.info("Calling Azure Document Intelligence API...")
            poller = client.begin_analyze_document(
                model_id="prebuilt-layout",
                body=pdf_bytes,
                content_type="application/pdf"
            )

            # 5. Wait for analysis to complete
            result = poller.result()
            logger.info(f"Azure analysis completed for file {file_id}")

            # Get page count from result
            page_count = len(result.pages) if result.pages else 0
            logger.info(f"Document has {page_count} pages")

            # 6. Extract tables from result
            tables_extracted = []
            if result.tables:
                for table_idx, table in enumerate(result.tables):
                    # Extract table structure
                    row_count = table.row_count
                    column_count = table.column_count

                    # Initialize table data structure
                    table_cells = [[None for _ in range(column_count)] for _ in range(row_count)]

                    # Fill in cells
                    for cell in table.cells:
                        row_idx = cell.row_index
                        col_idx = cell.column_index
                        table_cells[row_idx][col_idx] = cell.content or ""

                    # Convert any remaining None values to empty strings
                    for i in range(row_count):
                        for j in range(column_count):
                            if table_cells[i][j] is None:
                                table_cells[i][j] = ""

                    # Separate headers (first row) from data rows
                    headers = [table_cells[0]] if row_count > 0 else [[]]
                    rows = table_cells[1:] if row_count > 1 else []

                    # Extract bounding box if available
                    bbox = None
                    if table.bounding_regions and len(table.bounding_regions) > 0:
                        region = table.bounding_regions[0]
                        polygon = region.polygon
                        if polygon and len(polygon) >= 8:  # polygon is [x1, y1, x2, y2, x3, y3, x4, y4]
                            # Convert polygon to bounding box (x, y, width, height)
                            x_coords = [polygon[i] for i in range(0, len(polygon), 2)]
                            y_coords = [polygon[i] for i in range(1, len(polygon), 2)]
                            bbox = {
                                "x": min(x_coords),
                                "y": min(y_coords),
                                "width": max(x_coords) - min(x_coords),
                                "height": max(y_coords) - min(y_coords)
                            }

                    # Get page number (1-indexed)
                    page_number = table.bounding_regions[0].page_number if table.bounding_regions else 1

                    # Calculate confidence (average of cell confidences)
                    confidences = [cell.confidence for cell in table.cells if hasattr(cell, 'confidence') and cell.confidence is not None]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else None

                    table_data = {
                        "page_number": page_number,
                        "bbox": bbox,
                        "headers": headers,
                        "rows": rows,
                        "confidence": avg_confidence,
                        "row_count": row_count,
                        "column_count": column_count
                    }

                    tables_extracted.append(table_data)
                    logger.info(f"Extracted table {table_idx + 1} from page {page_number} with {row_count}x{column_count} cells")

            # 7. Save tables to database
            for table_data in tables_extracted:
                table = FileTable(
                    file_id=file_id,
                    page_number=table_data["page_number"],
                    table_json=table_data,
                    name=f"Table on page {table_data['page_number']}",
                    status=FileStatus.completed
                )
                db.add(table)

            # 8. Update file status to completed and store metadata
            file_obj = await db.get(FileModel, file_id)
            if file_obj:
                file_obj.status = FileStatus.completed

                # Update active version with page count (stored in llm_params as metadata)
                if file_obj.active_version_id:
                    version_obj = await db.get(FileVersion, file_obj.active_version_id)
                    if version_obj:
                        # Store page_count and table_count in llm_params as metadata
                        metadata = version_obj.llm_params or {}
                        metadata['page_count'] = page_count
                        metadata['table_count'] = len(tables_extracted)
                        version_obj.llm_params = metadata
                        logger.info(f"Updated version metadata: {page_count} pages, {len(tables_extracted)} tables")

            await db.commit()
            logger.info(f"Azure parsing completed for file {file_id}. Extracted {len(tables_extracted)} tables from {page_count} pages.")

        except Exception as e:
            logger.error(f"Azure parsing failed for file {file_id}: {e}", exc_info=True)

            # Update file status to pending (failed)
            try:
                file_obj = await db.get(FileModel, file_id)
                if file_obj:
                    file_obj.status = FileStatus.pending
                await db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update file status after error: {db_error}")


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

    # Get page count from active version metadata
    page_count = 0
    if file_obj.active_version_id:
        version_query = select(FileVersion).where(FileVersion.version_id == file_obj.active_version_id)
        version_result = await db.execute(version_query)
        version_obj = version_result.scalar_one_or_none()
        if version_obj and version_obj.llm_params:
            page_count = version_obj.llm_params.get('page_count', 0)

    # Map FileStatus enum to string status
    status_map = {
        FileStatus.pending: "pending",
        FileStatus.ready_for_annotation: "ready",
        FileStatus.in_progress: "processing",
        FileStatus.completed: "completed",
        FileStatus.archived: "archived"
    }

    logger.info(f"Parse status for file {file_id}: status={status_map.get(file_obj.status, 'pending')}, tables={len(tables)}, pages={page_count}")

    return ParseStatusResponse(
        file_id=file_id,
        file_name=file_obj.name,  # Fixed: file_name -> name
        status=status_map.get(file_obj.status, "pending"),
        tables_found=len(tables),
        page_count=page_count,
        processing_error=None,  # parse_error field doesn't exist
        created_at=file_obj.created_at.isoformat() if file_obj.created_at else None,
        completed_at=file_obj.updated_at.isoformat() if file_obj.status == FileStatus.completed and file_obj.updated_at else None
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
        
        # Sanitize None values in headers and rows (for old database records)
        headers = table_data.get("headers", [])
        rows = table_data.get("rows", [])

        # Convert None values to empty strings in headers
        sanitized_headers = [[cell if cell is not None else "" for cell in row] for row in headers]

        # Convert None values to empty strings in rows
        sanitized_rows = [[cell if cell is not None else "" for cell in row] for row in rows]

        table_responses.append(
            TableResponse(
                table_id=table.table_id,
                file_id=table.file_id,
                page_number=table.page_number or 0,
                bbox=bbox,
                headers=sanitized_headers,
                rows=sanitized_rows,
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

