import uuid
from datetime import date, datetime

from pydantic import BaseModel


class ExpenseBase(BaseModel):
    expense_date: date
    category_id: uuid.UUID
    item_name: str
    vendor_name: str | None = None
    amount: float
    payment_type: str
    notes: str | None = None


class ExpenseCreate(ExpenseBase):
    tenant_id: uuid.UUID
    weekly_cash_id: uuid.UUID


class ExpenseUpdate(BaseModel):
    expense_date: date | None = None
    category_id: uuid.UUID | None = None
    item_name: str | None = None
    vendor_name: str | None = None
    amount: float | None = None
    payment_type: str | None = None
    notes: str | None = None


class ExpenseRead(ExpenseBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    weekly_cash_id: uuid.UUID
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None
    is_deleted: bool = False

    class Config:
        from_attributes = True
