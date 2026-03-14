import csv
import io
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.models.owner_payment import OwnerPayment
from app.models.weekly_cash_record import WeeklyCashRecord
from app.schemas.common import Message
from app.schemas.report import WeeklyDashboardRow

router = APIRouter()


@router.get("/weekly-summary/{week_id}", response_model=Message)
async def weekly_summary(week_id: str):
    return {"message": f"weekly summary {week_id}"}


@router.get("/expense-summary", response_model=Message)
async def expense_summary():
    return {"message": "expense summary"}


@router.get("/cash-report", response_model=Message)
async def cash_report():
    return {"message": "cash report"}


@router.get("/expenses-export")
async def expenses_export(
    tenant_id: uuid.UUID = Query(...),
    start: date | None = None,
    end: date | None = None,
    category_id: uuid.UUID | None = None,
    weekly_cash_id: uuid.UUID | None = None,
    payment_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Expense, ExpenseCategory.category_name)
        .join(ExpenseCategory, Expense.category_id == ExpenseCategory.id, isouter=True)
        .where(Expense.tenant_id == tenant_id)
        .where(Expense.is_deleted.is_(False))
    )
    if start:
        stmt = stmt.where(Expense.expense_date >= start)
    if end:
        stmt = stmt.where(Expense.expense_date <= end)
    if category_id:
        stmt = stmt.where(Expense.category_id == category_id)
    if weekly_cash_id:
        stmt = stmt.where(Expense.weekly_cash_id == weekly_cash_id)
    if payment_type:
        stmt = stmt.where(Expense.payment_type == payment_type)

    stmt = stmt.order_by(Expense.expense_date.desc())
    result = await db.execute(stmt)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Expense Date",
            "Item Name",
            "Category",
            "Amount",
            "Payment Type",
            "Vendor",
            "Notes",
        ]
    )
    for expense, category_name in result.all():
        writer.writerow(
            [
                expense.expense_date,
                expense.item_name,
                category_name or expense.category_id,
                float(expense.amount),
                expense.payment_type,
                expense.vendor_name or "",
                expense.notes or "",
            ]
        )

    output.seek(0)
    headers = {"Content-Disposition": "attachment; filename=expenses_report.csv"}
    return StreamingResponse(output, media_type="text/csv", headers=headers)


@router.get("/weekly-dashboard", response_model=list[WeeklyDashboardRow])
async def weekly_dashboard(
    tenant_id: uuid.UUID = Query(...),
    start: date | None = None,
    end: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    weeks_stmt = select(WeeklyCashRecord).where(WeeklyCashRecord.tenant_id == tenant_id)
    if start:
        weeks_stmt = weeks_stmt.where(WeeklyCashRecord.week_end_date >= start)
    if end:
        weeks_stmt = weeks_stmt.where(WeeklyCashRecord.week_start_date <= end)
    weeks_stmt = weeks_stmt.order_by(WeeklyCashRecord.week_start_date.desc())
    weeks_result = await db.execute(weeks_stmt)
    weeks = weeks_result.scalars().all()
    if not weeks:
        return []

    week_ids = [week.id for week in weeks]

    expense_stmt = (
        select(
            Expense.weekly_cash_id,
            ExpenseCategory.category_name,
            func.coalesce(func.sum(Expense.amount), 0),
        )
        .join(ExpenseCategory, Expense.category_id == ExpenseCategory.id, isouter=True)
        .where(Expense.weekly_cash_id.in_(week_ids))
        .where(Expense.is_deleted.is_(False))
        .group_by(Expense.weekly_cash_id, ExpenseCategory.category_name)
    )
    expense_result = await db.execute(expense_stmt)
    expense_rows = expense_result.all()

    category_totals: dict[uuid.UUID, dict[str, float]] = {week_id: {} for week_id in week_ids}
    total_expenses: dict[uuid.UUID, float] = {week_id: 0.0 for week_id in week_ids}
    for week_id, category_name, total in expense_rows:
        name = category_name or "Unknown"
        total_value = float(total or 0)
        category_totals[week_id][name] = total_value
        total_expenses[week_id] += total_value

    payment_stmt = (
        select(OwnerPayment.weekly_cash_id, func.coalesce(func.sum(OwnerPayment.amount), 0))
        .where(OwnerPayment.weekly_cash_id.in_(week_ids))
        .group_by(OwnerPayment.weekly_cash_id)
    )
    payment_result = await db.execute(payment_stmt)
    payment_rows = payment_result.all()
    paid_to_boss = {week_id: 0.0 for week_id in week_ids}
    for week_id, total in payment_rows:
        paid_to_boss[week_id] = float(total or 0)

    response: list[WeeklyDashboardRow] = []
    for week in weeks:
        total_cash_available = float(week.cash_adjust_amount or 0) + float(week.cash_from_safe or 0)
        total_expense = total_expenses.get(week.id, 0.0)
        paid = paid_to_boss.get(week.id, 0.0)
        balance_deposited = total_cash_available - total_expense - paid
        response.append(
            WeeklyDashboardRow(
                weekly_cash_id=week.id,
                week_start_date=week.week_start_date,
                week_end_date=week.week_end_date,
                cash_adjust_amount=float(week.cash_adjust_amount or 0),
                cash_from_safe=float(week.cash_from_safe or 0),
                category_totals=category_totals.get(week.id, {}),
                total_expenses=total_expense,
                paid_to_boss=paid,
                balance_deposited=balance_deposited,
            )
        )
    return response
