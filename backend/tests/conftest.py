import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from app.core.database import Base

BASE_DIR = Path(__file__).resolve().parents[1]
TEST_DB_PATH = BASE_DIR / "test.db"

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{TEST_DB_PATH}")


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    engine = create_engine(f"sqlite:///{TEST_DB_PATH}")
    Base.metadata.create_all(engine)
    yield
