import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    action_type: Mapped[str] = mapped_column(String(20))
    table_name: Mapped[str] = mapped_column(String(100))
    record_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    old_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
