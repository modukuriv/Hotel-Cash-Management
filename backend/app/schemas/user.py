import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    role: str
    is_mfa_enabled: bool = False
    is_active: bool = True


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None
    is_mfa_enabled: bool | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    last_login_at: datetime | None = None
    last_login_ip: str | None = None
    login_count: int | None = None
    must_reset_password: bool = False
    locked_until: datetime | None = None
    totp_enabled: bool = False

    class Config:
        from_attributes = True


class TotpSetupResponse(BaseModel):
    user_id: uuid.UUID
    secret: str
    otpauth_uri: str


class UserSelfUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
