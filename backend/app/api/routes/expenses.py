import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Role, require_roles
from app.schemas.common import Message
from app.schemas.expense import ExpenseCreate, ExpenseRead, ExpenseUpdate
from app.core.database import get_db
from app.models.expense import Expense
from app.services.audit import add_audit_log, get_request_ip, get_request_user_id, model_to_dict

router = APIRouter()


async def _get_expense(db: AsyncSession, expense_id: uuid.UUID) -> Expense | None:
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    return result.scalar_one_or_none()


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.ADMIN, Role.GLOBAL_ADMIN)),
):
    if payload.amount <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Amount must be positive.")

    expense = Expense(
        tenant_id=payload.tenant_id,
        weekly_cash_id=payload.weekly_cash_id,
        expense_date=payload.expense_date,
        category_id=payload.category_id,
        item_name=payload.item_name,
        vendor_name=payload.vendor_name,
        amount=payload.amount,
        payment_type=payload.payment_type,
        notes=payload.notes,
    )
    db.add(expense)
    await db.flush()
    add_audit_log(
        db,
        tenant_id=expense.tenant_id,
        user_id=get_request_user_id(request),
        action_type="Insert",
        table_name="expenses",
        record_id=expense.id,
        old_values=None,
        new_values=model_to_dict(expense),
        ip_address=get_request_ip(request),
    )
    await db.commit()
    await db.refresh(expense)
    return expense


@router.get("", response_model=list[ExpenseRead])
async def list_expenses(
    tenant_id: uuid.UUID,
    start: date | None = None,
    end: date | None = None,
    category_id: uuid.UUID | None = None,
    weekly_cash_id: uuid.UUID | None = None,
    payment_type: str | None = None,
    include_deleted: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Expense).where(Expense.tenant_id == tenant_id)
    if start:
        stmt = stmt.where(Expense.expense_date >= start)
    if end:
        stmt = stmt.where(Expense.expense_date <= end)
    if not include_deleted:
        stmt = stmt.where(Expense.is_deleted.is_(False))
    if category_id:
        stmt = stmt.where(Expense.category_id == category_id)
    if weekly_cash_id:
        stmt = stmt.where(Expense.weekly_cash_id == weekly_cash_id)
    if payment_type:
        stmt = stmt.where(Expense.payment_type == payment_type)

    stmt = stmt.order_by(Expense.expense_date.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{expense_id}", response_model=ExpenseRead)
async def get_expense(expense_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    expense = await _get_expense(db, expense_id)
    if not expense or expense.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")
    return expense


@router.put("/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: uuid.UUID,
    payload: ExpenseUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.ADMIN, Role.GLOBAL_ADMIN)),
):
    expense = await _get_expense(db, expense_id)
    if not expense or expense.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")

    old_values = model_to_dict(expense)
    update_data = payload.model_dump(exclude_unset=True)
    if "amount" in update_data and update_data["amount"] is not None and update_data["amount"] <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Amount must be positive.")

    for field, value in update_data.items():
        setattr(expense, field, value)
    expense.updated_at = datetime.utcnow()
    add_audit_log(
        db,
        tenant_id=expense.tenant_id,
        user_id=get_request_user_id(request),
        action_type="Update",
        table_name="expenses",
        record_id=expense.id,
        old_values=old_values,
        new_values=model_to_dict(expense),
        ip_address=get_request_ip(request),
    )
    await db.commit()
    await db.refresh(expense)
    return expense


@router.delete("/{expense_id}", response_model=Message)
async def delete_expense(
    expense_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.GLOBAL_ADMIN)),
):
    expense = await _get_expense(db, expense_id)
    if not expense or expense.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found.")

    old_values = model_to_dict(expense)
    expense.is_deleted = True
    expense.updated_at = datetime.utcnow()
    add_audit_log(
        db,
        tenant_id=expense.tenant_id,
        user_id=get_request_user_id(request),
        action_type="Delete",
        table_name="expenses",
        record_id=expense.id,
        old_values=old_values,
        new_values=model_to_dict(expense),
        ip_address=get_request_ip(request),
    )
    await db.commit()
    return {"message": "Expense deleted."}
