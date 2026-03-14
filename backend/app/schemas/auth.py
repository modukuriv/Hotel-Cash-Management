import uuid

from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    email: EmailStr = Field(alias="username")
    code: str | None = None


class UserInfo(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None = None
    role: str
    email: EmailStr
    must_reset_password: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str
