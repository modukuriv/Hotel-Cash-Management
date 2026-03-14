from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.tenant import Tenant
from app.schemas.tenant import TenantRead

router = APIRouter()


@router.get("", response_model=list[TenantRead])
async def list_tenants(
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Tenant)
    if not include_inactive:
        stmt = stmt.where(Tenant.is_active.is_(True))
    stmt = stmt.order_by(Tenant.hotel_name.asc())
    result = await db.execute(stmt)
    return result.scalars().all()
