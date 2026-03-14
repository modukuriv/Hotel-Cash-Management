from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Hotel Cash Management API"
    env: str = "dev"
    api_v1_prefix: str = "/api"
    allowed_origins: str = "http://localhost:5173"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hotel_cash"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    frontend_url: str = "http://localhost:5173"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "no-reply@hotelcash.local"
    smtp_use_tls: bool = True
    lockout_threshold: int = 5
    lockout_minutes: int = 15
    password_min_length: int = 10
    password_require_upper: bool = True
    password_require_lower: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True
    mfa_code_length: int = 6
    mfa_code_expire_minutes: int = 10
    mfa_max_attempts: int = 5
    allow_admin_no_totp: bool = False
    login_rate_limit: int = 5
    login_rate_window_seconds: int = 60
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.0

    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), case_sensitive=False)

    @property
    def allowed_origins_list(self) -> list[str]:
        if not self.allowed_origins:
            return ["http://localhost:5173"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    def validate_for_env(self) -> None:
        if self.env.lower() not in {"prod", "production"}:
            return

        if not self.jwt_secret or self.jwt_secret == "change-me" or len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be set and at least 32 chars in production.")

        if any(origin == "*" for origin in self.allowed_origins_list):
            raise ValueError("ALLOWED_ORIGINS cannot include '*' in production.")

        if self.allow_admin_no_totp:
            raise ValueError("ALLOW_ADMIN_NO_TOTP must be false in production.")

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not value:
            return value
        if value.startswith("sqlite+aiosqlite:///./"):
            relative = value.replace("sqlite+aiosqlite:///./", "", 1)
            return f"sqlite+aiosqlite:///{BASE_DIR / relative}"
        if value.startswith("sqlite:///./"):
            relative = value.replace("sqlite:///./", "", 1)
            return f"sqlite:///{BASE_DIR / relative}"
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://") and "postgresql+asyncpg://" not in value:
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value


settings = Settings()
