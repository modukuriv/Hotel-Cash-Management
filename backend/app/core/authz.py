from enum import Enum

from fastapi import HTTPException, Request, status

from app.core.security import decode_token


class Role(str, Enum):
    GLOBAL_ADMIN = "GLOBAL_ADMIN"
    ADMIN = "ADMIN"
    USER = "USER"


def get_request_role(request: Request) -> Role:
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
            role = (payload.get("role") or "").upper()
            return Role(role)
        except Exception:
            return Role.USER

    raw = (request.headers.get("X-Role") or "").upper()
    try:
        return Role(raw)
    except ValueError:
        return Role.USER


def require_roles(*roles: Role):
    def _checker(request: Request):
        role = get_request_role(request)
        if role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return role

    return _checker
