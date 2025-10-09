"""CRUD operations for AnnotationJob model."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import AnnotationJob
from app.schemas.annotation import AnnotationJobCreate, AnnotationJobUpdate

async def get_annotation_job(db: AsyncSession, job_id: int) -> Optional[AnnotationJob]:
    result = await db.execute(select(AnnotationJob).where(AnnotationJob.job_id == job_id))
    return result.scalar_one_or_none()

async def get_annotation_jobs(db: AsyncSession, project_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[AnnotationJob]:
    query = select(AnnotationJob)
    if project_id:
        query = query.where(AnnotationJob.project_id == project_id)
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())

async def create_annotation_job(db: AsyncSession, job_data: AnnotationJobCreate) -> AnnotationJob:
    job = AnnotationJob(**job_data.model_dump())
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job

async def update_annotation_job(db: AsyncSession, job_id: int, job_data: AnnotationJobUpdate) -> Optional[AnnotationJob]:
    job = await get_annotation_job(db, job_id)
    if not job:
        return None
    for field, value in job_data.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    await db.commit()
    await db.refresh(job)
    return job

async def delete_annotation_job(db: AsyncSession, job_id: int) -> bool:
    job = await get_annotation_job(db, job_id)
    if not job:
        return False
    job.is_active = False
    from datetime import datetime
    job.deleted_at = datetime.utcnow()
    await db.commit()
    return True

