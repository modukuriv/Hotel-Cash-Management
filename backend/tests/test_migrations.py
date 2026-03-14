import os
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


def test_alembic_heads_match():
    env = {
        **os.environ,
        "DATABASE_URL": "sqlite+aiosqlite:///./alembic_test.db",
    }
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "heads"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() != "", "No alembic heads found"
