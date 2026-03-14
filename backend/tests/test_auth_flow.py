from fastapi.testclient import TestClient
from pathlib import Path
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base
from app.core.security import generate_totp_secret
from app.models.tenant import Tenant
from app.models.user import User


def test_totp_login_flow():
    base_dir = Path(__file__).resolve().parents[1]
    db_path = base_dir / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    secret = generate_totp_secret()
    with SessionLocal() as session:
        tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        session.add(
            Tenant(
                id=tenant_id,
                hotel_name="Test Hotel",
                is_active=True,
            )
        )
        user = User(
            tenant_id=tenant_id,
            email="tester@example.com",
            role="GLOBAL_ADMIN",
            is_active=True,
            totp_secret=secret,
            totp_enabled=True,
        )
        session.add(user)
        session.commit()

    client = TestClient(app)
    from pyotp import TOTP

    code = TOTP(secret).now()
    response = client.post(
        "/api/auth/login",
        json={"email": "tester@example.com", "code": code},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "tester@example.com"
