import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Role, require_roles
from app.schemas.common import Message
from app.schemas.owner_payment import OwnerPaymentCreate, OwnerPaymentRead
from app.core.database import get_db
from app.models.owner_payment import OwnerPayment
from app.services.audit import add_audit_log, get_request_ip, get_request_user_id, model_to_dict

router = APIRouter()


@router.post("", response_model=OwnerPaymentRead, status_code=status.HTTP_201_CREATED)
async def create_owner_payment(
    payload: OwnerPaymentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.ADMIN, Role.GLOBAL_ADMIN)),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Amount must be positive.")

    payment = OwnerPayment(
        tenant_id=payload.tenant_id,
        weekly_cash_id=payload.weekly_cash_id,
        amount=payload.amount,
        notes=payload.notes,
        created_at=datetime.utcnow(),
    )
    db.add(payment)
    await db.flush()
    add_audit_log(
        db,
        tenant_id=payment.tenant_id,
        user_id=get_request_user_id(request),
        action_type="Insert",
        table_name="owner_payments",
        record_id=payment.id,
        old_values=None,
        new_values=model_to_dict(payment),
        ip_address=get_request_ip(request),
    )
    await db.commit()
    await db.refresh(payment)
    return payment


@router.get("", response_model=list[OwnerPaymentRead])
async def list_owner_payments(
    tenant_id: uuid.UUID = Query(...),
    weekly_cash_id: uuid.UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(OwnerPayment).where(OwnerPayment.tenant_id == tenant_id)
    if weekly_cash_id:
        stmt = stmt.where(OwnerPayment.weekly_cash_id == weekly_cash_id)
    stmt = stmt.order_by(OwnerPayment.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
