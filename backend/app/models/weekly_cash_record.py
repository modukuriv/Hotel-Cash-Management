import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WeeklyCashRecord(Base):
    __tablename__ = "weekly_cash_records"
    __table_args__ = (UniqueConstraint("tenant_id", "week_start_date"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    week_start_date: Mapped[date] = mapped_column(Date)
    week_end_date: Mapped[date] = mapped_column(Date)
    cash_adjust_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    cash_from_safe: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
