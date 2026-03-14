import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import Request

from app.core.security import decode_token
from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


def _serialize_value(value: Any):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


def model_to_dict(instance: Any) -> dict[str, Any]:
    mapper = sa_inspect(instance).mapper
    result: dict[str, Any] = {}
    for column in mapper.column_attrs:
        if column.key in {"password_hash", "totp_secret", "token_hash"}:
            continue
        result[column.key] = _serialize_value(getattr(instance, column.key))
    return result


def get_request_user_id(request: Request) -> uuid.UUID | None:
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
            if payload.get("sub"):
                return uuid.UUID(payload["sub"])
        except Exception:
            pass
    raw = request.headers.get("X-User-Id")
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


def get_request_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


def add_audit_log(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    action_type: str,
    table_name: str,
    record_id: uuid.UUID | None,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    ip_address: str | None = None,
):
    audit = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action_type=action_type,
        table_name=table_name,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
    )
    db.add(audit)
