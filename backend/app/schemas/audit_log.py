import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    action_type: str
    table_name: str
    record_id: uuid.UUID | None = None
    old_values: dict | None = None
    new_values: dict | None = None
    ip_address: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
