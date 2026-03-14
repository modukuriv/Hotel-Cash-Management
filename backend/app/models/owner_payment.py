import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OwnerPayment(Base):
    __tablename__ = "owner_payments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    weekly_cash_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("weekly_cash_records.id"))
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
