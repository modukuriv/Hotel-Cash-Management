from fastapi import APIRouter

from app.api.routes import (
    auth,
    users,
    weekly_cash,
    expenses,
    owner_payments,
    reports,
    tenants,
    expense_categories,
    audit_logs,
    health,
    invites,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(weekly_cash.router, prefix="/weeks", tags=["weekly-cash"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(owner_payments.router, prefix="/owner-payments", tags=["owner-payments"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(expense_categories.router, prefix="/expense-categories", tags=["expense-categories"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(invites.router, prefix="/invites", tags=["invites"])
