import asyncio
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


DEMO_HOTEL_NAME = "Wingate"
ADMIN_EMAIL = "vmodukuri@outlook.com"

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


async def seed():
    async with engine.begin() as conn:
        has_users = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table("users"))
        if not has_users:
            raise RuntimeError(
                "Database schema not initialized. Run: python3 -m alembic upgrade head"
            )

    async with SessionLocal() as session:
        tenant = await session.scalar(select(Tenant).where(Tenant.hotel_name == DEMO_HOTEL_NAME))
        if not tenant:
            legacy_tenant = await session.scalar(
                select(Tenant).where(Tenant.hotel_name == "Demo Hotel")
            )
            if legacy_tenant:
                legacy_tenant.hotel_name = DEMO_HOTEL_NAME
                tenant = legacy_tenant
            else:
                tenant = Tenant(
                    hotel_name=DEMO_HOTEL_NAME,
                    address="123 Demo Street",
                    timezone="America/Chicago",
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

        admin_user = await session.scalar(select(User).where(User.email == ADMIN_EMAIL))
        if not admin_user:
            legacy_admin = await session.scalar(
                select(User).where(User.email == "admin@wingate.com")
            )
            if legacy_admin:
                legacy_admin.email = ADMIN_EMAIL
                legacy_admin.role = "GLOBAL_ADMIN"
                legacy_admin.is_mfa_enabled = True
                legacy_admin.is_active = True
                if not legacy_admin.totp_secret:
                    legacy_admin.totp_secret = generate_totp_secret()
                legacy_admin.totp_enabled = True
                admin_user = legacy_admin
            else:
                admin_user = User(
                    tenant_id=tenant.id,
                    first_name="Admin",
                    last_name="User",
                    email=ADMIN_EMAIL,
                    role="GLOBAL_ADMIN",
                    is_mfa_enabled=True,
                    is_active=True,
                    totp_secret=generate_totp_secret(),
                    totp_enabled=True,
                )
                session.add(admin_user)
        else:
            admin_user.role = "GLOBAL_ADMIN"
            admin_user.is_mfa_enabled = True
            if not admin_user.totp_secret:
                admin_user.totp_secret = generate_totp_secret()
            admin_user.totp_enabled = True

        if admin_user and admin_user.totp_secret:
            uri = totp_provisioning_uri(admin_user.totp_secret, admin_user.email)
            print(f"Admin TOTP URI: {uri}")

        global_admin = await session.scalar(select(User).where(User.email == "globaladmin@wingate.com"))
        if not global_admin:
            session.add(
                User(
                    tenant_id=tenant.id,
                    first_name="Global",
                    last_name="Admin",
                    email="globaladmin@wingate.com",
                    role="GLOBAL_ADMIN",
                    is_active=True,
                    totp_secret=generate_totp_secret(),
                    totp_enabled=True,
                )
            )
        else:
            if not global_admin.totp_secret:
                global_admin.totp_secret = generate_totp_secret()
            global_admin.totp_enabled = True

        viewer_user = await session.scalar(select(User).where(User.email == "user@wingate.com"))
        if not viewer_user:
            session.add(
                User(
                    tenant_id=tenant.id,
                    first_name="Viewer",
                    last_name="User",
                    email="user@wingate.com",
                    role="USER",
                    is_active=True,
                    totp_secret=generate_totp_secret(),
                    totp_enabled=True,
                )
            )
        else:
            if not viewer_user.totp_secret:
                viewer_user.totp_secret = generate_totp_secret()
            viewer_user.totp_enabled = True

        await session.commit()

    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
