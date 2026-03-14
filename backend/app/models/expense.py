import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    weekly_cash_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("weekly_cash_records.id"))
    expense_date: Mapped[date] = mapped_column(Date)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("expense_categories.id"))
    item_name: Mapped[str] = mapped_column(String(300))
    vendor_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    payment_type: Mapped[str] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
