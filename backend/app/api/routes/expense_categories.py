import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.expense_category import ExpenseCategory
from app.schemas.expense_category import ExpenseCategoryRead

router = APIRouter()


@router.get("", response_model=list[ExpenseCategoryRead])
async def list_categories(
    tenant_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExpenseCategory).where(ExpenseCategory.is_active.is_(True))
    if tenant_id:
        stmt = stmt.where(
            or_(ExpenseCategory.tenant_id == tenant_id, ExpenseCategory.tenant_id.is_(None))
        )
    stmt = stmt.order_by(ExpenseCategory.category_name.asc())
    result = await db.execute(stmt)
    return result.scalars().all()
