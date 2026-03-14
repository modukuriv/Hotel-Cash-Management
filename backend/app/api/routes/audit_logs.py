import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogRead

router = APIRouter()


@router.get("", response_model=list[AuditLogRead])
async def list_audit_logs(
    tenant_id: uuid.UUID | None = Query(None),
    table_name: str | None = Query(None),
    record_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog)
    if tenant_id:
        stmt = stmt.where(AuditLog.tenant_id == tenant_id)
    if table_name:
        stmt = stmt.where(AuditLog.table_name == table_name)
    if record_id:
        stmt = stmt.where(AuditLog.record_id == record_id)
    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
