import uuid
from datetime import datetime

from pydantic import BaseModel


class ExpenseCategoryBase(BaseModel):
    category_name: str
    is_system_defined: bool = True
    is_active: bool = True


class ExpenseCategoryCreate(ExpenseCategoryBase):
    tenant_id: uuid.UUID | None = None


class ExpenseCategoryRead(ExpenseCategoryBase):
    id: uuid.UUID
    tenant_id: uuid.UUID | None = None
    created_at: datetime

    class Config:
        from_attributes = True
