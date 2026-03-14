import asyncio
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import func, select, inspect

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal, engine  # noqa: E402
from app.core.security import generate_totp_secret, totp_provisioning_uri  # noqa: E402
from app.models.expense_category import ExpenseCategory  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.weekly_cash_record import WeeklyCashRecord  # noqa: E402

SYSTEM_CATEGORIES = [
    "Hotel Misc",
    "CC Payments",
    "Review Reward",
    "Commissions",
    "Employee Payroll - Cash",
    "Gas",
    "Laundry",
    "Maintenance",
    "Supplies",
    "Shuttle",
    "Utilities",
    "Food & Beverage",
    "Owner Expense",
    "Other",
]

DEFAULT_TENANT_NAME = os.getenv("BOOTSTRAP_TENANT_NAME", "Wingate")
DEFAULT_TENANT_ADDRESS = os.getenv("BOOTSTRAP_TENANT_ADDRESS", "123 Demo Street")
DEFAULT_TENANT_TIMEZONE = os.getenv("BOOTSTRAP_TENANT_TIMEZONE", "America/Chicago")
DEFAULT_ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "vmodukuri@outlook.com")
DEFAULT_ADMIN_FIRST_NAME = os.getenv("BOOTSTRAP_ADMIN_FIRST_NAME", "Admin")
DEFAULT_ADMIN_LAST_NAME = os.getenv("BOOTSTRAP_ADMIN_LAST_NAME", "User")


async def seed_if_empty() -> None:
    async with engine.begin() as conn:
        has_users = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table("users"))
        if not has_users:
            raise RuntimeError(
                "Database schema not initialized. Run: python -m alembic upgrade head"
            )

    async with SessionLocal() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        if total_users and total_users > 0:
            print("Bootstrap skipped: users already exist.")
            return

        tenant = await session.scalar(select(Tenant).where(Tenant.hotel_name == DEFAULT_TENANT_NAME))
        if not tenant:
            tenant = Tenant(
                hotel_name=DEFAULT_TENANT_NAME,
                address=DEFAULT_TENANT_ADDRESS,
                timezone=DEFAULT_TENANT_TIMEZONE,
                is_active=True,
            )
            session.add(tenant)
            await session.flush()

        categories_count = await session.scalar(select(func.count(ExpenseCategory.id)))
        if not categories_count:
            session.add_all(
                [
                    ExpenseCategory(category_name=name, is_system_defined=True, is_active=True)
                    for name in SYSTEM_CATEGORIES
                ]
            )

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        existing_week = await session.scalar(
            select(WeeklyCashRecord).where(
                WeeklyCashRecord.tenant_id == tenant.id,
                WeeklyCashRecord.week_start_date == week_start,
            )
        )
        if not existing_week:
            session.add(
                WeeklyCashRecord(
                    tenant_id=tenant.id,
                    week_start_date=week_start,
                    week_end_date=week_end,
                    cash_adjust_amount=0,
                    cash_from_safe=0,
                    notes="Seeded week",
                )
            )

        admin_user = User(
            tenant_id=tenant.id,
            first_name=DEFAULT_ADMIN_FIRST_NAME,
            last_name=DEFAULT_ADMIN_LAST_NAME,
            email=DEFAULT_ADMIN_EMAIL,
            role="GLOBAL_ADMIN",
            is_mfa_enabled=True,
            is_active=True,
            totp_secret=generate_totp_secret(),
            totp_enabled=True,
        )
        session.add(admin_user)
        await session.commit()

        uri = totp_provisioning_uri(admin_user.totp_secret, admin_user.email)
        print(f"Bootstrap admin created: {admin_user.email}")
        print(f"Admin TOTP URI: {uri}")


if __name__ == "__main__":
    asyncio.run(seed_if_empty())
