import uuid
from datetime import date, datetime

from pydantic import BaseModel


class WeeklyCashBase(BaseModel):
    week_start_date: date
    week_end_date: date
    cash_adjust_amount: float = 0
    cash_from_safe: float = 0
    notes: str | None = None


class WeeklyCashCreate(WeeklyCashBase):
    tenant_id: uuid.UUID


class WeeklyCashRead(WeeklyCashBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_locked: bool
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
