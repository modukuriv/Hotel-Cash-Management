import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import generate_totp_secret, totp_provisioning_uri  # noqa: E402
from app.models.user import User  # noqa: E402

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "vmodukuri@outlook.com").strip().lower()


async def reset_totp() -> None:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
        user = result.scalar_one_or_none()
        if not user:
            raise SystemExit(f"Admin user not found for email: {ADMIN_EMAIL}")

        user.totp_secret = generate_totp_secret()
        user.totp_enabled = True
        await session.commit()

        uri = totp_provisioning_uri(user.totp_secret, user.email)
        print(f"Admin TOTP URI: {uri}")


if __name__ == "__main__":
    asyncio.run(reset_totp())
