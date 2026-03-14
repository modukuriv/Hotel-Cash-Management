from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_totp_code,
)
from app.core.config import settings
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo, RefreshRequest
from app.services.audit import get_request_ip
from app.services.rate_limit import SlidingWindowRateLimiter

router = APIRouter()
login_limiter = SlidingWindowRateLimiter(
    max_requests=settings.login_rate_limit,
    window_seconds=settings.login_rate_window_seconds,
)


async def issue_refresh_token(db: AsyncSession, user_id, ip_address: str | None = None) -> str:
    raw = create_refresh_token(subject=str(user_id))
    expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    token = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(raw),
        issued_at=datetime.utcnow(),
        expires_at=expires_at,
    )
    db.add(token)
    await db.flush()
    return raw


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip_address = get_request_ip(request) or "unknown"
    limit_result = login_limiter.hit(ip_address)
    if not limit_result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(limit_result.retry_after or settings.login_rate_window_seconds)},
        )
    identifier = payload.email.strip().lower()
    stmt = select(User).where(func.lower(User.email) == identifier)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    now = datetime.utcnow()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    if user.locked_until and user.locked_until > now:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account locked. Try again later.")

    if not user.totp_enabled or not user.totp_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticator not set up.")

    code = (payload.code or "").strip()
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code is required.")
    if not verify_totp_code(user.totp_secret, code):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= settings.lockout_threshold:
            user.locked_until = now + timedelta(minutes=settings.lockout_minutes)
            user.failed_login_attempts = 0
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid code.")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.login_count = (user.login_count or 0) + 1
    user.last_login_at = now
    user.last_login_ip = get_request_ip(request)
    await db.commit()

    access_token = create_access_token(
        subject=str(user.id),
        extra={
            "role": user.role,
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "email": user.email,
            "must_reset_password": bool(user.must_reset_password),
        },
    )
    refresh_token = await issue_refresh_token(db, user.id, get_request_ip(request))
    await db.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(
            id=user.id,
            tenant_id=user.tenant_id,
            role=user.role,
            email=user.email,
            must_reset_password=bool(user.must_reset_password),
        ),
    )


# MFA verify endpoint removed in passwordless TOTP flow.


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token.")

    token_hash = hash_token(payload.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()
    now = datetime.utcnow()
    if not stored or stored.revoked_at or stored.expires_at < now:
        raise HTTPException(status_code=401, detail="Refresh token expired.")

    user = await db.get(User, stored.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized.")

    stored.revoked_at = now
    access_token = create_access_token(
        subject=str(user.id),
        extra={
            "role": user.role,
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "email": user.email,
            "must_reset_password": bool(user.must_reset_password),
        },
    )
    new_refresh = await issue_refresh_token(db, user.id, get_request_ip(request))
    await db.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        user=UserInfo(
            id=user.id,
            tenant_id=user.tenant_id,
            role=user.role,
            email=user.email,
            must_reset_password=bool(user.must_reset_password),
        ),
    )
