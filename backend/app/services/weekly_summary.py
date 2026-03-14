from dataclasses import dataclass


@dataclass
class WeeklySummary:
    total_cash_available: float
    total_expenses: float
    remaining_cash: float
    balance_deposited: float


def compute_weekly_summary(cash_adjust_amount: float, cash_from_safe: float, total_expenses: float, owner_payments_total: float) -> WeeklySummary:
    total_cash_available = cash_adjust_amount + cash_from_safe
    remaining_cash = total_cash_available - total_expenses
    balance_deposited = remaining_cash - owner_payments_total
    return WeeklySummary(
        total_cash_available=total_cash_available,
        total_expenses=total_expenses,
        remaining_cash=remaining_cash,
        balance_deposited=balance_deposited,
    )
