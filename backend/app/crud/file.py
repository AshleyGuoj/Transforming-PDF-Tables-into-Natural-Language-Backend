"""CRUD operations for File model."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import File
from app.schemas.file import FileCreate, FileUpdate

async def get_file(db: AsyncSession, file_id: int) -> Optional[File]:
    result = await db.execute(select(File).where(File.file_id == file_id))
    return result.scalar_one_or_none()

async def get_files(db: AsyncSession, project_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[File]:
    query = select(File)
    if project_id:
        query = query.where(File.project_id == project_id)
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())

async def create_file(db: AsyncSession, file_data: FileCreate) -> File:
    file = File(**file_data.model_dump())
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file

async def update_file(db: AsyncSession, file_id: int, file_data: FileUpdate) -> Optional[File]:
    file = await get_file(db, file_id)
    if not file:
        return None
    for field, value in file_data.model_dump(exclude_unset=True).items():
        setattr(file, field, value)
    await db.commit()
    await db.refresh(file)
    return file

async def delete_file(db: AsyncSession, file_id: int) -> bool:
    file = await get_file(db, file_id)
    if not file:
        return False
    file.is_active = False
    from datetime import datetime
    file.deleted_at = datetime.utcnow()
    await db.commit()
    return True

