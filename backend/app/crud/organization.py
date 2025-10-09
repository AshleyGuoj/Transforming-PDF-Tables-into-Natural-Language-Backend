"""CRUD operations for Organization model."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate

async def get_organization(db: AsyncSession, org_id: int) -> Optional[Organization]:
    result = await db.execute(select(Organization).where(Organization.org_id == org_id))
    return result.scalar_one_or_none()

async def get_organizations(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Organization]:
    result = await db.execute(select(Organization).offset(skip).limit(limit))
    return list(result.scalars().all())

async def create_organization(db: AsyncSession, org_data: OrganizationCreate) -> Organization:
    org = Organization(**org_data.model_dump())
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org

async def update_organization(db: AsyncSession, org_id: int, org_data: OrganizationUpdate) -> Optional[Organization]:
    org = await get_organization(db, org_id)
    if not org:
        return None
    for field, value in org_data.model_dump(exclude_unset=True).items():
        setattr(org, field, value)
    await db.commit()
    await db.refresh(org)
    return org

async def delete_organization(db: AsyncSession, org_id: int) -> bool:
    org = await get_organization(db, org_id)
    if not org:
        return False
    org.is_active = False
    from datetime import datetime
    org.deleted_at = datetime.utcnow()
    await db.commit()
    return True

