import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.authz import Role, require_roles
from app.core.database import get_db
from app.models.weekly_cash_record import WeeklyCashRecord
from app.schemas.common import Message
from app.schemas.weekly_cash import WeeklyCashCreate, WeeklyCashRead, WeeklyCashBase
from app.services.audit import add_audit_log, get_request_ip, get_request_user_id, model_to_dict

router = APIRouter()


@router.post("", response_model=WeeklyCashRead, status_code=status.HTTP_201_CREATED)
async def create_week(
    payload: WeeklyCashCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.ADMIN, Role.GLOBAL_ADMIN)),
):
    week = WeeklyCashRecord(
        tenant_id=payload.tenant_id,
        week_start_date=payload.week_start_date,
        week_end_date=payload.week_end_date,
        cash_adjust_amount=payload.cash_adjust_amount,
        cash_from_safe=payload.cash_from_safe,
        notes=payload.notes,
    )
    db.add(week)
    try:
        await db.flush()
        add_audit_log(
            db,
            tenant_id=week.tenant_id,
            user_id=get_request_user_id(request),
            action_type="Insert",
            table_name="weekly_cash_records",
            record_id=week.id,
            old_values=None,
            new_values=model_to_dict(week),
            ip_address=get_request_ip(request),
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Week already exists for this tenant.",
        )
    await db.refresh(week)
    return week


@router.get("", response_model=list[WeeklyCashRead])
async def list_weeks(
    tenant_id: uuid.UUID = Query(...),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(WeeklyCashRecord)
        .where(WeeklyCashRecord.tenant_id == tenant_id)
        .order_by(WeeklyCashRecord.week_start_date.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{week_id}", response_model=WeeklyCashRead)
async def get_week(week_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WeeklyCashRecord).where(WeeklyCashRecord.id == week_id))
    week = result.scalar_one_or_none()
    if not week:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Week not found.")
    return week


@router.put("/{week_id}", response_model=WeeklyCashRead)
async def update_week(
    week_id: uuid.UUID,
    payload: WeeklyCashBase,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.ADMIN, Role.GLOBAL_ADMIN)),
):
    result = await db.execute(select(WeeklyCashRecord).where(WeeklyCashRecord.id == week_id))
    week = result.scalar_one_or_none()
    if not week:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Week not found.")
    if week.is_locked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Week is locked.")

    old_values = model_to_dict(week)
    week.week_start_date = payload.week_start_date
    week.week_end_date = payload.week_end_date
    week.cash_adjust_amount = payload.cash_adjust_amount
    week.cash_from_safe = payload.cash_from_safe
    week.notes = payload.notes
    week.updated_at = datetime.utcnow()
    add_audit_log(
        db,
        tenant_id=week.tenant_id,
        user_id=get_request_user_id(request),
        action_type="Update",
        table_name="weekly_cash_records",
        record_id=week.id,
        old_values=old_values,
        new_values=model_to_dict(week),
        ip_address=get_request_ip(request),
    )
    await db.commit()
    await db.refresh(week)
    return week


@router.post("/{week_id}/lock", response_model=Message)
async def lock_week(
    week_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.ADMIN, Role.GLOBAL_ADMIN)),
):
    result = await db.execute(select(WeeklyCashRecord).where(WeeklyCashRecord.id == week_id))
    week = result.scalar_one_or_none()
    if not week:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Week not found.")

    old_values = model_to_dict(week)
    week.is_locked = True
    week.updated_at = datetime.utcnow()
    add_audit_log(
        db,
        tenant_id=week.tenant_id,
        user_id=get_request_user_id(request),
        action_type="Update",
        table_name="weekly_cash_records",
        record_id=week.id,
        old_values=old_values,
        new_values=model_to_dict(week),
        ip_address=get_request_ip(request),
    )
    await db.commit()
    return {"message": f"Week {week_id} locked."}
