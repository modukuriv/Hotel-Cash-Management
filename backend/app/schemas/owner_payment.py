import uuid
from datetime import datetime

from pydantic import BaseModel


class OwnerPaymentBase(BaseModel):
    amount: float
    notes: str | None = None


class OwnerPaymentCreate(OwnerPaymentBase):
    tenant_id: uuid.UUID
    weekly_cash_id: uuid.UUID


class OwnerPaymentRead(OwnerPaymentBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    weekly_cash_id: uuid.UUID
    created_by: uuid.UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True
