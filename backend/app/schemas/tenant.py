import uuid
from datetime import datetime

from pydantic import BaseModel


class TenantBase(BaseModel):
    hotel_name: str
    logo_url: str | None = None
    theme_color: str | None = None
    address: str | None = None
    timezone: str | None = None
    is_active: bool = True


class TenantCreate(TenantBase):
    pass


class TenantRead(TenantBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
