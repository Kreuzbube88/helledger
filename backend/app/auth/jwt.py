import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError  # noqa: F401

from app.config import settings

_ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, settings.SECRET_KEY, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> int:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
    return int(payload["sub"])


def create_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, sha256_hash). Store hash server-side, send raw to client."""
    raw = secrets.token_urlsafe(32)
    return raw, hashlib.sha256(raw.encode()).hexdigest()
