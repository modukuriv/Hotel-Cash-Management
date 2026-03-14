import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Role, require_roles
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
    verify_totp_code,
    generate_totp_secret,
    totp_provisioning_uri,
)
from app.models.refresh_token import RefreshToken
from app.models.tenant import Tenant
from app.models.user import User
from app.models.user_invite import UserInvite
from app.schemas.auth import TokenResponse, UserInfo
from app.schemas.invite import (
    InviteAcceptRequest,
    InviteCreateRequest,
    InviteCreateResponse,
    InvitePublicResponse,
)
from app.services.audit import add_audit_log, get_request_ip, get_request_user_id, model_to_dict
from app.services.background import schedule_task
from app.services.email import send_invite_email

router = APIRouter()


def build_invite_link(token: str) -> str:
    return f"{settings.frontend_url}/invite/{token}"


async def issue_refresh_token(db: AsyncSession, user_id) -> str:
    raw = create_refresh_token(subject=str(user_id))
    token = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(raw),
        issued_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(token)
    await db.flush()
    return raw


@router.post("", response_model=InviteCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    payload: InviteCreateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.GLOBAL_ADMIN)),
):
    email = payload.email.strip().lower()
    existing_user = await db.scalar(select(User).where(func.lower(User.email) == email))
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists.")

    try:
        role = Role(payload.role.upper())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid role.") from exc

    now = datetime.utcnow()
    existing_invite = await db.scalar(
        select(UserInvite).where(
            func.lower(UserInvite.email) == email,
            UserInvite.accepted_at.is_(None),
            UserInvite.expires_at > now,
        )
    )
    if existing_invite:
        raise HTTPException(status_code=400, detail="Invite already exists.")

    tenant = await db.get(Tenant, payload.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Property not found.")

    raw_token = secrets.token_urlsafe(32)
    invite = UserInvite(
        tenant_id=payload.tenant_id,
        email=email,
        role=role.value,
        first_name=payload.first_name,
        last_name=payload.last_name,
        token_hash=hash_token(raw_token),
        totp_secret=generate_totp_secret(),
        expires_at=now + timedelta(hours=settings.invite_expires_hours),
        created_by=get_request_user_id(request),
    )
    db.add(invite)
    await db.flush()

    invite_link = build_invite_link(raw_token)
    try:
        schedule_task(background_tasks, send_invite_email, email, tenant.hotel_name, invite_link)
    except Exception:
        pass

    add_audit_log(
        db,
        tenant_id=invite.tenant_id,
        user_id=get_request_user_id(request),
        action_type="INSERT",
        table_name="user_invites",
        record_id=invite.id,
        old_values=None,
        new_values=model_to_dict(invite),
        ip_address=get_request_ip(request),
    )
    await db.commit()

    return InviteCreateResponse(
        email=invite.email,
        tenant_id=invite.tenant_id,
        role=invite.role,
        invite_link=invite_link,
        expires_at=invite.expires_at,
        message="Invite created.",
    )


@router.get("/{token}", response_model=InvitePublicResponse)
async def get_invite(token: str, db: AsyncSession = Depends(get_db)):
    token_hash = hash_token(token)
    invite = await db.scalar(select(UserInvite).where(UserInvite.token_hash == token_hash))
    now = datetime.utcnow()
    if not invite or invite.accepted_at or invite.expires_at <= now:
        raise HTTPException(status_code=404, detail="Invite not found or expired.")

    tenant = await db.get(Tenant, invite.tenant_id)
    return InvitePublicResponse(
        email=invite.email,
        tenant_id=invite.tenant_id,
        role=invite.role,
        first_name=invite.first_name,
        last_name=invite.last_name,
        property_name=tenant.hotel_name if tenant else None,
        otpauth_uri=totp_provisioning_uri(invite.totp_secret, invite.email),
        expires_at=invite.expires_at,
    )


@router.post("/{token}/accept", response_model=TokenResponse)
async def accept_invite(
    token: str,
    payload: InviteAcceptRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    token_hash = hash_token(token)
    invite = await db.scalar(select(UserInvite).where(UserInvite.token_hash == token_hash))
    now = datetime.utcnow()
    if not invite or invite.accepted_at or invite.expires_at <= now:
        raise HTTPException(status_code=404, detail="Invite not found or expired.")

    code = (payload.code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Code is required.")
    if not verify_totp_code(invite.totp_secret, code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid code.")

    existing_user = await db.scalar(select(User).where(func.lower(User.email) == invite.email))
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists.")

    user = User(
        tenant_id=invite.tenant_id,
        first_name=invite.first_name,
        last_name=invite.last_name,
        email=invite.email,
        role=invite.role,
        is_mfa_enabled=True,
        is_active=True,
        totp_secret=invite.totp_secret,
        totp_enabled=True,
        login_count=1,
        last_login_at=now,
        last_login_ip=get_request_ip(request),
    )
    db.add(user)
    invite.accepted_at = now

    add_audit_log(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        action_type="INSERT",
        table_name="users",
        record_id=user.id,
        old_values=None,
        new_values=model_to_dict(user),
        ip_address=get_request_ip(request),
    )
    add_audit_log(
        db,
        tenant_id=invite.tenant_id,
        user_id=user.id,
        action_type="UPDATE",
        table_name="user_invites",
        record_id=invite.id,
        old_values=None,
        new_values=model_to_dict(invite),
        ip_address=get_request_ip(request),
    )

    await db.commit()

    access_token = create_access_token(
        subject=str(user.id),
        extra={
            "role": user.role,
            "tenant_id": str(user.tenant_id),
            "email": user.email,
            "must_reset_password": False,
        },
    )
    refresh_token = await issue_refresh_token(db, user.id)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(
            id=user.id,
            tenant_id=user.tenant_id,
            role=user.role,
            email=user.email,
            must_reset_password=False,
        ),
    )
