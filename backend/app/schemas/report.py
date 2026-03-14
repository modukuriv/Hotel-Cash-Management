import uuid
from datetime import date

from pydantic import BaseModel


class WeeklyDashboardRow(BaseModel):
    weekly_cash_id: uuid.UUID
    week_start_date: date
    week_end_date: date
    cash_adjust_amount: float
    cash_from_safe: float
    category_totals: dict[str, float]
    total_expenses: float
    paid_to_boss: float
    balance_deposited: float
