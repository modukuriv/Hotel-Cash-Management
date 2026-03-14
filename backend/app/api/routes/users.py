import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import Role, require_roles
from app.core.database import get_db
from app.core.security import generate_totp_secret, totp_provisioning_uri
from app.models.user import User
from app.models.tenant import Tenant
from app.schemas.user import (
    UserInviteRequest,
    UserInviteResponse,
    UserRead,
    UserSelfUpdate,
    UserUpdate,
    TotpSetupResponse,
)
from app.services.audit import add_audit_log, get_request_ip, get_request_user_id, model_to_dict
from app.services.email import send_invite_email
from app.services.background import schedule_task

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = get_request_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized.")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.put("/me", response_model=UserRead)
async def update_me(
    payload: UserSelfUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_request_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized.")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    old_values = model_to_dict(user)

    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name

    # Passwordless login: profile updates are name-only for now.

    add_audit_log(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        action_type="UPDATE",
        table_name="users",
        record_id=user.id,
        old_values=old_values,
        new_values=model_to_dict(user),
        ip_address=get_request_ip(request),
    )
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/me/totp", response_model=TotpSetupResponse)
async def generate_totp_for_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_request_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized.")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    old_values = model_to_dict(user)
    user.totp_secret = generate_totp_secret()
    user.totp_enabled = True
    add_audit_log(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        action_type="UPDATE",
        table_name="users",
        record_id=user.id,
        old_values=old_values,
        new_values=model_to_dict(user),
        ip_address=get_request_ip(request),
    )
    await db.commit()
    return TotpSetupResponse(
        user_id=user.id,
        secret=user.totp_secret,
        otpauth_uri=totp_provisioning_uri(user.totp_secret, user.email),
    )


@router.get("", response_model=list[UserRead])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.GLOBAL_ADMIN)),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=UserInviteResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    payload: UserInviteRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.GLOBAL_ADMIN)),
):
    email = payload.email.strip().lower()
    existing = await db.scalar(select(User).where(func.lower(User.email) == email))
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists.")

    try:
        role = Role(payload.role.upper())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid role.") from exc

    user = User(
        tenant_id=payload.tenant_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=email,
        role=role.value,
        is_active=True,
        must_reset_password=False,
        totp_secret=generate_totp_secret(),
        totp_enabled=True,
    )
    db.add(user)
    await db.flush()

    tenant = await db.get(Tenant, payload.tenant_id)
    property_name = tenant.hotel_name if tenant else "your property"
    try:
        schedule_task(background_tasks, send_invite_email, email, property_name)
    except Exception:
        pass

    add_audit_log(
        db,
        tenant_id=user.tenant_id,
        user_id=get_request_user_id(request),
        action_type="INSERT",
        table_name="users",
        record_id=user.id,
        old_values=None,
        new_values=model_to_dict(user),
        ip_address=get_request_ip(request),
    )
    await db.commit()
    await db.refresh(user)

    setup = TotpSetupResponse(
        user_id=user.id,
        secret=user.totp_secret,
        otpauth_uri=totp_provisioning_uri(user.totp_secret, user.email),
    )
    return UserInviteResponse(user=user, message="Invite sent.", totp_setup=setup)


@router.post("/{user_id}/totp", response_model=TotpSetupResponse)
async def generate_totp_for_user(
    user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.GLOBAL_ADMIN)),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    old_values = model_to_dict(user)
    user.totp_secret = generate_totp_secret()
    user.totp_enabled = True
    add_audit_log(
        db,
        tenant_id=user.tenant_id,
        user_id=get_request_user_id(request),
        action_type="UPDATE",
        table_name="users",
        record_id=user.id,
        old_values=old_values,
        new_values=model_to_dict(user),
        ip_address=get_request_ip(request),
    )
    await db.commit()
    return TotpSetupResponse(
        user_id=user.id,
        secret=user.totp_secret,
        otpauth_uri=totp_provisioning_uri(user.totp_secret, user.email),
    )


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.GLOBAL_ADMIN)),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    old_values = model_to_dict(user)

    if payload.first_name is not None:
        user.first_name = payload.first_name
    if payload.last_name is not None:
        user.last_name = payload.last_name
    if payload.role is not None:
        try:
            role = Role(payload.role.upper())
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid role.") from exc
        user.role = role.value
    if payload.is_mfa_enabled is not None:
        user.is_mfa_enabled = payload.is_mfa_enabled
    if payload.is_active is not None:
        user.is_active = payload.is_active

    add_audit_log(
        db,
        tenant_id=user.tenant_id,
        user_id=get_request_user_id(request),
        action_type="UPDATE",
        table_name="users",
        record_id=user.id,
        old_values=old_values,
        new_values=model_to_dict(user),
        ip_address=get_request_ip(request),
    )
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _role: Role = Depends(require_roles(Role.GLOBAL_ADMIN)),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    old_values = model_to_dict(user)
    await db.delete(user)
    add_audit_log(
        db,
        tenant_id=user.tenant_id,
        user_id=get_request_user_id(request),
        action_type="DELETE",
        table_name="users",
        record_id=user.id,
        old_values=old_values,
        new_values=None,
        ip_address=get_request_ip(request),
    )
    await db.commit()
    return {"message": "User deleted."}
