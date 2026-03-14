import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class InviteCreateRequest(BaseModel):
    email: EmailStr
    role: str
    tenant_id: uuid.UUID
    first_name: str | None = None
    last_name: str | None = None


class InviteCreateResponse(BaseModel):
    email: EmailStr
    tenant_id: uuid.UUID
    role: str
    invite_link: str
    expires_at: datetime
    message: str


class InvitePublicResponse(BaseModel):
    email: EmailStr
    tenant_id: uuid.UUID
    role: str
    first_name: str | None = None
    last_name: str | None = None
    property_name: str | None = None
    otpauth_uri: str
    expires_at: datetime


class InviteAcceptRequest(BaseModel):
    code: str
