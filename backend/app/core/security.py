from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any
import secrets
import string
import pyotp

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        to_encode.update(extra)
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def validate_password_policy(password: str) -> tuple[bool, str]:
    if len(password) < settings.password_min_length:
        return False, f"Password must be at least {settings.password_min_length} characters."
    if settings.password_require_upper and not any(c.isupper() for c in password):
        return False, "Password must include an uppercase letter."
    if settings.password_require_lower and not any(c.islower() for c in password):
        return False, "Password must include a lowercase letter."
    if settings.password_require_digit and not any(c.isdigit() for c in password):
        return False, "Password must include a number."
    if settings.password_require_special and not any(c in string.punctuation for c in password):
        return False, "Password must include a special character."
    return True, ""


def generate_temporary_password() -> str:
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(settings.password_min_length + 2))
        valid, _ = validate_password_policy(password)
        if valid:
            return password


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, email: str, issuer: str = "Hotel Cash") -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def verify_totp_code(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
