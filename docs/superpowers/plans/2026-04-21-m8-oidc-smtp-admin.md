# HELLEDGER M8: OIDC, SMTP, Admin Panel — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add OIDC single sign-on, SMTP email (password reset + invitations), admin panel with user management, and login rate limiting.

**Architecture:** OIDC via Authorization Code + PKCE flow using python-jose (already a dep) + httpx for discovery; state/code_verifier stored in signed HttpOnly cookie to stay stateless. SMTP via stdlib `smtplib` wrapped in `asyncio.get_event_loop().run_in_executor`. Admin panel as new FastAPI router + Vue SFC. Runtime settings stored in existing `app_settings` key/value table. Rate limiting via in-memory TTL dict (no new dep).

**Tech Stack:** FastAPI, python-jose (already installed), httpx (add to requirements.txt), smtplib (stdlib), Vue 3 + shadcn-vue.

---

## File Map

```
backend/
├── requirements.txt                    ← MODIFY: add httpx==0.28.1
├── app/
│   ├── config.py                       ← MODIFY: add OIDC_*, SMTP_* fields
│   ├── models/
│   │   └── user.py                     ← MODIFY: add oidc_sub, is_active; add PasswordResetToken
│   ├── schemas/
│   │   ├── users.py                    ← CREATE: UserOut, UserPatch, PreferencesPatch
│   │   └── admin.py                    ← CREATE: AdminStatus, AdminSettings, AdminSettingsPatch
│   ├── services/
│   │   └── email.py                    ← CREATE: send_email(), reset/invite templates
│   ├── auth/
│   │   └── deps.py                     ← MODIFY: add get_admin_user dependency
│   ├── routers/
│   │   ├── auth.py                     ← MODIFY: add oidc/login, oidc/callback, password-reset/*
│   │   ├── users.py                    ← CREATE: /api/users CRUD + /me/preferences
│   │   └── admin.py                    ← CREATE: /api/admin/status + /api/admin/settings
│   └── main.py                         ← MODIFY: include users + admin routers
├── alembic/versions/
│   └── 006_oidc_admin.py               ← CREATE: migration
└── tests/
    ├── test_rate_limit.py              ← CREATE
    ├── test_password_reset.py          ← CREATE
    ├── test_users_admin.py             ← CREATE
    └── test_admin.py                   ← CREATE

frontend/src/
├── views/
│   ├── LoginView.vue                   ← MODIFY: add OIDC SSO button
│   ├── SettingsView.vue                ← MODIFY: add profile section (name/email/password/language)
│   └── AdminView.vue                   ← CREATE
├── router/index.js                     ← MODIFY: add /admin route with requiresAdmin guard
└── locales/
    ├── de.json                         ← MODIFY: add admin.* keys
    └── en.json                         ← MODIFY: add admin.* keys
```

---

### Task 1: Add OIDC + SMTP config fields + httpx dependency

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/config.py`

- [ ] **Step 1: Add httpx to requirements.txt**

```
# backend/requirements.txt — add after email-validator line:
httpx==0.28.1
```

- [ ] **Step 2: Run to verify import works**

```bash
cd backend && pip install httpx==0.28.1
python -c "import httpx; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Extend Settings class in config.py**

Replace the entire `config.py` content:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    SECRET_KEY: str
    DATABASE_PATH: str = "/data/helledger.db"
    BACKUP_PATH: str = "/backups"
    BACKUP_INTERVAL_HOURS: int = 24
    PORT: int = 3000
    TZ: str = "Europe/Berlin"
    DEFAULT_LANGUAGE: str = "de"
    DEFAULT_CURRENCY: str = "EUR"
    ALLOW_REGISTRATION: bool = True
    FIRST_USER_IS_ADMIN: bool = True
    LOG_LEVEL: str = "INFO"
    TRUST_PROXY_HEADER: bool = True
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TESTING: bool = False

    # OIDC (optional)
    OIDC_ENABLED: bool = False
    OIDC_CLIENT_ID: str = ""
    OIDC_CLIENT_SECRET: str = ""
    OIDC_DISCOVERY_URL: str = ""  # e.g. https://accounts.google.com/.well-known/openid-configuration

    # SMTP (optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""   # defaults to SMTP_USER if empty
    SMTP_TLS: bool = True


settings = Settings()
```

- [ ] **Step 4: Verify config loads**

```bash
cd backend && python -c "from app.config import settings; print(settings.OIDC_ENABLED)"
```
Expected: `False`

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt backend/app/config.py
git commit -m "feat: add OIDC and SMTP config fields, add httpx dep"
```

---

### Task 2: DB migration — oidc_sub, is_active, password_reset_tokens

**Files:**
- Create: `backend/alembic/versions/006_oidc_admin.py`

- [ ] **Step 1: Create migration file**

```python
# backend/alembic/versions/006_oidc_admin.py
"""add oidc_sub, is_active to users; add password_reset_tokens

Revision ID: 006
Revises: 005
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("oidc_sub", sa.String(255), nullable=True))
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
    )
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("token_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("password_reset_tokens")
    op.drop_column("users", "is_active")
    op.drop_column("users", "oidc_sub")
```

- [ ] **Step 2: Run migration against test DB**

```bash
cd backend && DATABASE_PATH=data/test_m8.db SECRET_KEY=test alembic upgrade head
```
Expected: no errors, migrations 001 through 006 applied.

```bash
rm backend/data/test_m8.db
```

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/versions/006_oidc_admin.py
git commit -m "feat: migration 006 - oidc_sub, is_active, password_reset_tokens"
```

---

### Task 3: Update User model + add PasswordResetToken model

**Files:**
- Modify: `backend/app/models/user.py`

- [ ] **Step 1: Update user.py**

```python
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="user")
    language: Mapped[str] = mapped_column(String(5), default="de")
    active_household_id: Mapped[int | None] = mapped_column(
        ForeignKey("households.id", ondelete="SET NULL"), index=True
    )
    oidc_sub: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped[User] = relationship(back_populates="password_reset_tokens")
```

- [ ] **Step 2: Verify existing tests still pass**

```bash
cd backend && python -m pytest tests/ -x -q 2>&1 | tail -5
```
Expected: `149 passed`

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/user.py
git commit -m "feat: add oidc_sub, is_active to User; add PasswordResetToken model"
```

---

### Task 4: SMTP email service

**Files:**
- Create: `backend/app/services/email.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_email_service.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.email import _build_reset_email, _build_invite_email


def test_reset_email_de():
    subj, body_text, body_html = _build_reset_email("de", "https://app.example.com/#/reset?token=abc")
    assert "abc" in body_text
    assert "Passwort" in subj


def test_reset_email_en():
    subj, body_text, body_html = _build_reset_email("en", "https://app.example.com/#/reset?token=abc")
    assert "abc" in body_text
    assert "Password" in subj


def test_invite_email_de():
    subj, body_text, body_html = _build_invite_email("de", "Test Haushalt", "https://app.example.com/#/register?invite=xyz")
    assert "xyz" in body_text
    assert "Haushalt" in body_text


def test_invite_email_en():
    subj, body_text, body_html = _build_invite_email("en", "Test Household", "https://app.example.com/#/register?invite=xyz")
    assert "xyz" in body_text
    assert "Household" in body_text
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_email_service.py -v
```
Expected: `ImportError` or `ModuleNotFoundError`

- [ ] **Step 3: Create email service**

```python
# backend/app/services/email.py
import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def _build_reset_email(lang: str, reset_url: str) -> tuple[str, str, str]:
    if lang == "de":
        subject = "Passwort zurücksetzen — HELLEDGER"
        text = f"Klicke auf diesen Link, um dein Passwort zurückzusetzen:\n\n{reset_url}\n\nDer Link ist 1 Stunde gültig."
        html = f"<p>Klicke auf diesen Link, um dein Passwort zurückzusetzen:</p><p><a href='{reset_url}'>{reset_url}</a></p><p>Der Link ist 1 Stunde gültig.</p>"
    else:
        subject = "Reset your password — HELLEDGER"
        text = f"Click this link to reset your password:\n\n{reset_url}\n\nThe link expires in 1 hour."
        html = f"<p>Click this link to reset your password:</p><p><a href='{reset_url}'>{reset_url}</a></p><p>The link expires in 1 hour.</p>"
    return subject, text, html


def _build_invite_email(lang: str, household_name: str, invite_url: str) -> tuple[str, str, str]:
    if lang == "de":
        subject = f"Einladung zum Haushalt '{household_name}' — HELLEDGER"
        text = f"Du wurdest zum Haushalt '{household_name}' eingeladen:\n\n{invite_url}"
        html = f"<p>Du wurdest zum Haushalt '<strong>{household_name}</strong>' eingeladen:</p><p><a href='{invite_url}'>{invite_url}</a></p>"
    else:
        subject = f"Invitation to household '{household_name}' — HELLEDGER"
        text = f"You have been invited to household '{household_name}':\n\n{invite_url}"
        html = f"<p>You have been invited to household '<strong>{household_name}</strong>':</p><p><a href='{invite_url}'>{invite_url}</a></p>"
    return subject, text, html


def _send_sync(to: str, subject: str, body_text: str, body_html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_TLS:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(msg["From"], [to], msg.as_string())


async def send_email(to: str, subject: str, body_text: str, body_html: str) -> None:
    if not settings.SMTP_HOST:
        logger.debug("SMTP not configured, skipping email to %s", to)
        return
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send_sync, to, subject, body_text, body_html)
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_email_service.py -v
```
Expected: 4 tests pass

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/email.py backend/tests/test_email_service.py
git commit -m "feat: add SMTP email service with reset/invite templates"
```

---

### Task 5: Login rate limiting

**Files:**
- Create: `backend/app/auth/rate_limit.py`
- Modify: `backend/app/routers/auth.py` (login endpoint only)

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_rate_limit.py
from app.auth.rate_limit import RateLimiter


def test_allows_under_limit():
    rl = RateLimiter(max_attempts=3, window_minutes=15)
    assert rl.check("1.2.3.4") is True
    assert rl.check("1.2.3.4") is True
    assert rl.check("1.2.3.4") is True


def test_blocks_over_limit():
    rl = RateLimiter(max_attempts=3, window_minutes=15)
    rl.check("10.0.0.1")
    rl.check("10.0.0.1")
    rl.check("10.0.0.1")
    assert rl.check("10.0.0.1") is False


def test_different_ips_independent():
    rl = RateLimiter(max_attempts=2, window_minutes=15)
    rl.check("192.168.1.1")
    rl.check("192.168.1.1")
    assert rl.check("192.168.1.1") is False
    assert rl.check("192.168.1.2") is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_rate_limit.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Create rate limiter**

```python
# backend/app/auth/rate_limit.py
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from threading import Lock


class RateLimiter:
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15) -> None:
        self._max = max_attempts
        self._window = timedelta(minutes=window_minutes)
        self._attempts: dict[str, list[datetime]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str) -> bool:
        """Returns True if request is allowed, False if rate limited."""
        now = datetime.now(timezone.utc)
        cutoff = now - self._window
        with self._lock:
            self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]
            if len(self._attempts[key]) >= self._max:
                return False
            self._attempts[key].append(now)
            return True


_login_limiter = RateLimiter(max_attempts=5, window_minutes=15)
```

- [ ] **Step 4: Apply rate limiter to login endpoint**

In `backend/app/routers/auth.py`, update the login route:

```python
# Add import at top:
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from app.auth.rate_limit import _login_limiter

# Replace login function signature:
@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    if not _login_limiter.check(client_ip):
        raise HTTPException(status_code=429, detail="too_many_requests")
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="account_disabled")
    # ... rest of function unchanged
```

- [ ] **Step 5: Run rate limit tests**

```bash
cd backend && python -m pytest tests/test_rate_limit.py -v
```
Expected: 3 tests pass

- [ ] **Step 6: Run full test suite**

```bash
cd backend && python -m pytest tests/ -x -q 2>&1 | tail -5
```
Expected: `149 passed` (existing tests unaffected)

- [ ] **Step 7: Commit**

```bash
git add backend/app/auth/rate_limit.py backend/app/routers/auth.py backend/tests/test_rate_limit.py
git commit -m "feat: login rate limiting (5 attempts/IP/15 min)"
```

---

### Task 6: Password reset endpoints

**Files:**
- Modify: `backend/app/routers/auth.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_password_reset.py
import pytest


def test_password_reset_request_unknown_email(client):
    r = client.post("/api/auth/password-reset/request", json={"email": "nobody@example.com"})
    # Must return 200 even for unknown email (don't leak user existence)
    assert r.status_code == 200


def test_password_reset_request_known_email(client):
    client.post("/api/auth/register", json={"email": "reset@example.com", "password": "securepassword1", "name": "Reset User"})
    r = client.post("/api/auth/password-reset/request", json={"email": "reset@example.com"})
    assert r.status_code == 200


def test_password_reset_confirm_invalid_token(client):
    r = client.post("/api/auth/password-reset/confirm", json={"token": "invalidtoken", "new_password": "newpassword123"})
    assert r.status_code == 400


def test_password_reset_full_flow(client):
    from app.auth.password import hash_password
    from app.database import get_db
    import hashlib, secrets
    from datetime import datetime, timedelta, timezone

    # Register user
    client.post("/api/auth/register", json={"email": "flow@example.com", "password": "securepassword1", "name": "Flow User"})

    # Simulate token creation (bypass email)
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    db = next(client.app.dependency_overrides[get_db]())
    from app.models.user import User, PasswordResetToken
    user = db.query(User).filter(User.email == "flow@example.com").first()
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()

    # Confirm reset
    r = client.post("/api/auth/password-reset/confirm", json={"token": raw, "new_password": "newpassword999"})
    assert r.status_code == 200

    # Login with new password
    r2 = client.post("/api/auth/login", json={"email": "flow@example.com", "password": "newpassword999"})
    assert r2.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_password_reset.py -v
```
Expected: `ImportError` or `404`

- [ ] **Step 3: Add password reset endpoints to auth.py**

Add these imports at the top of `backend/app/routers/auth.py`:
```python
import hashlib
import secrets
from app.models.user import PasswordResetToken
from app.schemas.auth import PasswordResetRequest, PasswordResetConfirm
from app.services.email import send_email, _build_reset_email
```

Add to `backend/app/schemas/auth.py`:
```python
class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=12)
```

Add these two routes to `backend/app/routers/auth.py`:
```python
@router.post("/password-reset/request", status_code=200)
async def password_reset_request(body: PasswordResetRequest, db: Session = Depends(get_db)):
    # Always return 200 to avoid user enumeration
    user = db.query(User).filter(User.email == body.email).first()
    if user and settings.SMTP_HOST:
        raw, token_hash = secrets.token_urlsafe(32), None
        raw = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        # Invalidate previous tokens
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).delete()
        db.add(PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_at=datetime.now(timezone.utc),
        ))
        db.commit()
        reset_url = f"/#/reset-password?token={raw}"
        subject, body_text, body_html = _build_reset_email(user.language, reset_url)
        await send_email(user.email, subject, body_text, body_html)
    return {"ok": True}


@router.post("/password-reset/confirm", status_code=200)
async def password_reset_confirm(body: PasswordResetConfirm, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    prt = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()
    if not prt or prt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="invalid_or_expired_token")
    user = db.get(User, prt.user_id)
    user.password_hash = hash_password(body.new_password)
    db.delete(prt)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_password_reset.py -v
```
Expected: 4 tests pass

- [ ] **Step 5: Run full suite**

```bash
cd backend && python -m pytest tests/ -x -q 2>&1 | tail -5
```
Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/auth.py backend/app/schemas/auth.py backend/tests/test_password_reset.py
git commit -m "feat: password reset via email (request + confirm endpoints)"
```

---

### Task 7: OIDC endpoints (login + callback)

**Files:**
- Modify: `backend/app/routers/auth.py`

The OIDC flow: `GET /api/auth/oidc/login` → builds auth URL + stores code_verifier in signed cookie → redirects to IDP. `GET /api/auth/oidc/callback` → reads cookie, exchanges code, decodes ID token, finds/creates user, issues JWT, redirects to `/#/oidc-callback?access_token=...`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_oidc.py
import pytest


def test_oidc_login_disabled(client):
    r = client.get("/api/auth/oidc/login", follow_redirects=False)
    assert r.status_code == 404


def test_oidc_enabled_check(client):
    r = client.get("/api/auth/oidc/enabled")
    assert r.status_code == 200
    assert r.json()["enabled"] is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_oidc.py -v
```
Expected: `404` for both

- [ ] **Step 3: Add OIDC helper functions to a new module**

```python
# backend/app/auth/oidc.py
import base64
import hashlib
import secrets

import httpx
from jose import jwt as jose_jwt

from app.config import settings


def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


async def get_oidc_metadata() -> dict:
    if not settings.OIDC_DISCOVERY_URL:
        raise ValueError("OIDC_DISCOVERY_URL not set")
    async with httpx.AsyncClient() as c:
        r = await c.get(settings.OIDC_DISCOVERY_URL, timeout=10)
        r.raise_for_status()
        return r.json()


async def fetch_jwks(jwks_uri: str) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.get(jwks_uri, timeout=10)
        r.raise_for_status()
        return r.json()


async def exchange_code(
    token_endpoint: str, code: str, code_verifier: str, redirect_uri: str
) -> dict:
    async with httpx.AsyncClient() as c:
        r = await c.post(
            token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.OIDC_CLIENT_ID,
                "client_secret": settings.OIDC_CLIENT_SECRET,
                "code_verifier": code_verifier,
            },
            timeout=10,
        )
        r.raise_for_status()
        return r.json()


def decode_id_token(id_token: str, jwks: dict) -> dict:
    return jose_jwt.decode(
        id_token,
        jwks,
        algorithms=["RS256", "ES256"],
        audience=settings.OIDC_CLIENT_ID,
        options={"verify_at_hash": False},
    )
```

- [ ] **Step 4: Add OIDC endpoints to auth.py**

Add imports to `backend/app/routers/auth.py`:
```python
from fastapi import Request
from fastapi.responses import RedirectResponse
from app.auth.oidc import _pkce_pair, get_oidc_metadata, fetch_jwks, exchange_code, decode_id_token
```

Add routes:
```python
@router.get("/oidc/enabled")
async def oidc_enabled():
    return {"enabled": settings.OIDC_ENABLED}


@router.get("/oidc/login")
async def oidc_login(request: Request, response: Response):
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=404, detail="oidc_not_enabled")
    metadata = await get_oidc_metadata()
    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)
    # Store verifier+state in signed cookie (expires 10 min)
    cookie_val = f"{state}:{verifier}"
    redirect_uri = str(request.base_url) + "api/auth/oidc/callback"
    auth_url = (
        f"{metadata['authorization_endpoint']}"
        f"?response_type=code"
        f"&client_id={settings.OIDC_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=openid+email+profile"
        f"&state={state}"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
    )
    resp = RedirectResponse(url=auth_url)
    resp.set_cookie("oidc_state", cookie_val, httponly=True, samesite="lax", max_age=600)
    return resp


@router.get("/oidc/callback")
async def oidc_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=404, detail="oidc_not_enabled")
    cookie_val = request.cookies.get("oidc_state", "")
    parts = cookie_val.split(":", 1)
    if len(parts) != 2 or parts[0] != state:
        raise HTTPException(status_code=400, detail="invalid_state")
    verifier = parts[1]
    metadata = await get_oidc_metadata()
    redirect_uri = str(request.base_url) + "api/auth/oidc/callback"
    token_data = await exchange_code(metadata["token_endpoint"], code, verifier, redirect_uri)
    jwks = await fetch_jwks(metadata["jwks_uri"])
    claims = decode_id_token(token_data["id_token"], jwks)
    sub = claims["sub"]
    email = claims.get("email", "")
    name = claims.get("name") or claims.get("preferred_username") or email.split("@")[0]

    # Find existing user by oidc_sub or email
    user = db.query(User).filter(User.oidc_sub == sub).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.oidc_sub = sub  # link account
    if not user:
        # Auto-create user
        is_first = db.query(User).count() == 0
        role = "admin" if (is_first and settings.FIRST_USER_IS_ADMIN) else "user"
        user = User(
            email=email,
            password_hash="",
            name=name,
            role=role,
            oidc_sub=sub,
            language=settings.DEFAULT_LANGUAGE,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    access_token = create_access_token(user.id)
    resp = RedirectResponse(url=f"/#/oidc-callback?access_token={access_token}")
    resp.delete_cookie("oidc_state")
    return resp
```

- [ ] **Step 5: Run OIDC tests**

```bash
cd backend && python -m pytest tests/test_oidc.py -v
```
Expected: `test_oidc_login_disabled` → 404 ✓, `test_oidc_enabled_check` → 200 `{enabled: false}` ✓

- [ ] **Step 6: Run full suite**

```bash
cd backend && python -m pytest tests/ -x -q 2>&1 | tail -5
```
Expected: all pass

- [ ] **Step 7: Commit**

```bash
git add backend/app/auth/oidc.py backend/app/routers/auth.py backend/tests/test_oidc.py
git commit -m "feat: OIDC endpoints (login redirect + callback) with PKCE"
```

---

### Task 8: Admin user management API

**Files:**
- Modify: `backend/app/auth/deps.py`
- Create: `backend/app/schemas/users.py`
- Create: `backend/app/routers/users.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_users_admin.py
import pytest


def test_list_users_requires_admin(registered_client):
    r = registered_client.get("/api/users")
    assert r.status_code == 403


def test_list_users_as_admin(client):
    # first registered user is admin
    client.post("/api/auth/register", json={"email": "admin@example.com", "password": "securepassword1", "name": "Admin"})
    r = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "securepassword1"})
    token = r.json()["access_token"]
    r2 = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    users = r2.json()
    assert len(users) == 1
    assert users[0]["email"] == "admin@example.com"


def test_patch_user_role(client):
    client.post("/api/auth/register", json={"email": "admin2@example.com", "password": "securepassword1", "name": "Admin2"})
    r = client.post("/api/auth/login", json={"email": "admin2@example.com", "password": "securepassword1"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/auth/register", json={"email": "user2@example.com", "password": "securepassword1", "name": "User2"})
    users = client.get("/api/users", headers=headers).json()
    user_id = next(u["id"] for u in users if u["email"] == "user2@example.com")

    r2 = client.patch(f"/api/users/{user_id}", json={"role": "admin"}, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["role"] == "admin"


def test_get_me_preferences(registered_client):
    r = registered_client.get("/api/users/me/preferences")
    assert r.status_code == 200
    assert "language" in r.json()


def test_patch_me_preferences(registered_client):
    r = registered_client.patch("/api/users/me/preferences", json={"language": "en"})
    assert r.status_code == 200
    assert r.json()["language"] == "en"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_users_admin.py -v
```
Expected: 404 or ImportError

- [ ] **Step 3: Add admin dependency to deps.py**

Append to `backend/app/auth/deps.py`:
```python
def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="admin_required")
    return user
```

- [ ] **Step 4: Create user schemas**

```python
# backend/app/schemas/users.py
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    language: str
    is_active: bool
    created_at: datetime
    last_login: datetime | None

    model_config = {"from_attributes": True}


class UserPatch(BaseModel):
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    language: str | None = None


class PreferencesOut(BaseModel):
    language: str
    model_config = {"from_attributes": True}


class PreferencesPatch(BaseModel):
    language: str | None = None
```

- [ ] **Step 5: Create users router**

```python
# backend/app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_admin_user, get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.users import UserOut, UserPatch, PreferencesOut, PreferencesPatch

router = APIRouter(prefix="/users")


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    return db.query(User).order_by(User.id).all()


@router.get("/me/preferences", response_model=PreferencesOut)
def get_preferences(user: User = Depends(get_current_user)):
    return user


@router.patch("/me/preferences", response_model=PreferencesOut)
def update_preferences(
    body: PreferencesPatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.language is not None:
        user.language = body.language
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if current.role != "admin" and current.id != user_id:
        raise HTTPException(status_code=403, detail="forbidden")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def patch_user(
    user_id: int,
    body: UserPatch,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    if body.name is not None:
        user.name = body.name
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.language is not None:
        user.language = body.language
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="cannot_delete_self")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    db.delete(user)
    db.commit()
```

- [ ] **Step 6: Register router in main.py**

In `backend/app/main.py`, add:
```python
from app.routers import users as users_router
# ...
app.include_router(users_router.router, prefix="/api")
```

- [ ] **Step 7: Run tests**

```bash
cd backend && python -m pytest tests/test_users_admin.py -v
```
Expected: 5 tests pass

- [ ] **Step 8: Run full suite**

```bash
cd backend && python -m pytest tests/ -x -q 2>&1 | tail -5
```
Expected: all pass

- [ ] **Step 9: Commit**

```bash
git add backend/app/auth/deps.py backend/app/schemas/users.py backend/app/routers/users.py backend/app/main.py backend/tests/test_users_admin.py
git commit -m "feat: admin user management API (list/patch/delete users, preferences)"
```

---

### Task 9: Admin settings + status API

**Files:**
- Create: `backend/app/schemas/admin.py`
- Create: `backend/app/routers/admin.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_admin.py
import pytest


def _admin_client(client):
    client.post("/api/auth/register", json={"email": "sa@example.com", "password": "securepassword1", "name": "SA"})
    r = client.post("/api/auth/login", json={"email": "sa@example.com", "password": "securepassword1"})
    client.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return client


def test_admin_status(client):
    c = _admin_client(client)
    r = c.get("/api/admin/status")
    assert r.status_code == 200
    data = r.json()
    assert "user_count" in data
    assert "transaction_count" in data
    assert "db_size_bytes" in data


def test_admin_settings_get(client):
    c = _admin_client(client)
    r = c.get("/api/admin/settings")
    assert r.status_code == 200
    data = r.json()
    assert "allow_registration" in data


def test_admin_settings_patch(client):
    c = _admin_client(client)
    r = c.patch("/api/admin/settings", json={"allow_registration": False})
    assert r.status_code == 200
    assert r.json()["allow_registration"] is False


def test_admin_requires_admin_role(registered_client):
    # registered_client is a non-first user → role=user
    r = registered_client.get("/api/admin/status")
    assert r.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_admin.py -v
```
Expected: 404 or ImportError

- [ ] **Step 3: Create admin schemas**

```python
# backend/app/schemas/admin.py
from pydantic import BaseModel


class AdminStatus(BaseModel):
    user_count: int
    household_count: int
    transaction_count: int
    db_size_bytes: int
    allow_registration: bool


class AdminSettings(BaseModel):
    allow_registration: bool
    default_language: str
    oidc_enabled: bool
    oidc_client_id: str
    oidc_discovery_url: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_from: str


class AdminSettingsPatch(BaseModel):
    allow_registration: bool | None = None
    default_language: str | None = None
    oidc_enabled: bool | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    oidc_discovery_url: str | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
```

- [ ] **Step 4: Create admin router**

```python
# backend/app/routers/admin.py
import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import get_admin_user
from app.config import settings
from app.database import get_db
from app.models.household import Household
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.admin import AdminSettings, AdminSettingsPatch, AdminStatus
from app.services.settings import get_setting, set_setting

router = APIRouter(prefix="/admin")


def _runtime(key: str, env_val: str, db: Session) -> str:
    """Return runtime setting from DB, falling back to ENV value."""
    return get_setting(db, key) or env_val


@router.get("/status", response_model=AdminStatus)
def admin_status(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    db_path = settings.DATABASE_PATH
    db_size = os.path.getsize(db_path) if os.path.isfile(db_path) else 0
    return AdminStatus(
        user_count=db.query(User).count(),
        household_count=db.query(Household).count(),
        transaction_count=db.query(Transaction).count(),
        db_size_bytes=db_size,
        allow_registration=_runtime("allow_registration", str(settings.ALLOW_REGISTRATION), db).lower() != "false",
    )


@router.get("/settings", response_model=AdminSettings)
def get_admin_settings(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    return AdminSettings(
        allow_registration=_runtime("allow_registration", str(settings.ALLOW_REGISTRATION), db).lower() != "false",
        default_language=_runtime("default_language", settings.DEFAULT_LANGUAGE, db),
        oidc_enabled=_runtime("oidc_enabled", str(settings.OIDC_ENABLED), db).lower() == "true",
        oidc_client_id=_runtime("oidc_client_id", settings.OIDC_CLIENT_ID, db),
        oidc_discovery_url=_runtime("oidc_discovery_url", settings.OIDC_DISCOVERY_URL, db),
        smtp_host=_runtime("smtp_host", settings.SMTP_HOST, db),
        smtp_port=int(_runtime("smtp_port", str(settings.SMTP_PORT), db)),
        smtp_user=_runtime("smtp_user", settings.SMTP_USER, db),
        smtp_from=_runtime("smtp_from", settings.SMTP_FROM, db),
    )


@router.patch("/settings", response_model=AdminSettings)
def update_admin_settings(
    body: AdminSettingsPatch,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    mapping = {
        "allow_registration": body.allow_registration,
        "default_language": body.default_language,
        "oidc_enabled": body.oidc_enabled,
        "oidc_client_id": body.oidc_client_id,
        "oidc_client_secret": body.oidc_client_secret,
        "oidc_discovery_url": body.oidc_discovery_url,
        "smtp_host": body.smtp_host,
        "smtp_port": body.smtp_port,
        "smtp_user": body.smtp_user,
        "smtp_password": body.smtp_password,
        "smtp_from": body.smtp_from,
    }
    for key, val in mapping.items():
        if val is not None:
            set_setting(db, key, str(val))
    # Re-read and return
    return get_admin_settings(db=db, _admin=_admin)
```

- [ ] **Step 5: Register in main.py**

```python
# Add to backend/app/main.py:
from app.routers import admin as admin_router
# ...
app.include_router(admin_router.router, prefix="/api")
```

- [ ] **Step 6: Run tests**

```bash
cd backend && python -m pytest tests/test_admin.py -v
```
Expected: 4 tests pass

- [ ] **Step 7: Run full suite**

```bash
cd backend && python -m pytest tests/ -x -q 2>&1 | tail -5
```
Expected: all pass

- [ ] **Step 8: Commit**

```bash
git add backend/app/schemas/admin.py backend/app/routers/admin.py backend/app/main.py backend/tests/test_admin.py
git commit -m "feat: admin status + settings API (runtime config via app_settings)"
```

---

### Task 10: Frontend — LoginView.vue OIDC button

**Files:**
- Modify: `frontend/src/views/LoginView.vue`
- Modify: `frontend/src/locales/de.json` and `en.json`

The login page must check `GET /api/auth/oidc/enabled` on mount. If `enabled: true`, show a "Login mit SSO" / "Login with SSO" button below the password form that navigates to `/api/auth/oidc/login` (full browser redirect). Also add an `#/oidc-callback` handler route that reads the `access_token` query param, stores it, and navigates to `#/dashboard`.

- [ ] **Step 1: Add i18n keys**

In `frontend/src/locales/de.json`, add to `auth`:
```json
"ssoLogin": "Login mit SSO",
"orContinueWith": "oder weiter mit"
```

In `frontend/src/locales/en.json`, add to `auth`:
```json
"ssoLogin": "Login with SSO",
"orContinueWith": "or continue with"
```

- [ ] **Step 2: Add OIDC callback route to router**

In `frontend/src/router/index.js`, add before the catch-all:
```javascript
{ path: '/oidc-callback', component: () => import('../views/OidcCallbackView.vue') },
```

- [ ] **Step 3: Create OidcCallbackView.vue**

```vue
<!-- frontend/src/views/OidcCallbackView.vue -->
<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

onMounted(async () => {
  const token = route.query.access_token
  if (token) {
    localStorage.setItem('helledger_token', token)
    await auth.fetchUser()
    router.replace('/dashboard')
  } else {
    router.replace('/login')
  }
})
</script>

<template>
  <div class="flex h-screen items-center justify-center">
    <p class="text-muted-foreground">{{ $t('auth.redirecting') }}</p>
  </div>
</template>
```

Add `"redirecting": "Weiterleitung..."` / `"redirecting": "Redirecting..."` to `auth` in both locale files.

- [ ] **Step 4: Update LoginView.vue to show OIDC button**

In the `<script setup>` section of `frontend/src/views/LoginView.vue`, add:
```javascript
import { ref, onMounted } from 'vue'
const oidcEnabled = ref(false)

onMounted(async () => {
  try {
    const r = await fetch('/api/auth/oidc/enabled')
    const data = await r.json()
    oidcEnabled.value = data.enabled
  } catch {}
})

function loginWithOidc() {
  window.location.href = '/api/auth/oidc/login'
}
```

In the template, after the main card content (before closing `</Card>`):
```html
<template v-if="oidcEnabled">
  <Separator class="my-4" />
  <p class="text-center text-sm text-muted-foreground mb-3">{{ $t('auth.orContinueWith') }}</p>
  <Button variant="outline" class="w-full" @click="loginWithOidc">
    {{ $t('auth.ssoLogin') }}
  </Button>
</template>
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/LoginView.vue frontend/src/views/OidcCallbackView.vue frontend/src/router/index.js frontend/src/locales/de.json frontend/src/locales/en.json
git commit -m "feat: OIDC SSO button on login page + oidc-callback route"
```

---

### Task 11: Frontend — SettingsView.vue profile section

**Files:**
- Modify: `frontend/src/views/SettingsView.vue`
- Modify: `frontend/src/locales/de.json` and `en.json`

Add a "Profil" card above the existing household card with fields: name, email (read-only), current password, new password (min 12 chars), language select (de/en). On save: PATCH /api/users/me with name+language, then if new_password set: POST /api/auth/password-change (new endpoint) — BUT since we don't have a password-change endpoint yet, use PATCH /api/users/me/preferences for language, and for password use the existing password reset flow. 

Actually, for profile update: add `PATCH /api/users/me` endpoint to users.py, accepting `{name, language}`. For password change: add `POST /api/auth/change-password` accepting `{current_password, new_password}`.

- [ ] **Step 1: Add profile update + password change to users.py**

Add to `backend/app/schemas/users.py`:
```python
class ProfilePatch(BaseModel):
    name: str | None = None
    language: str | None = None
```

Add route to `backend/app/routers/users.py`:
```python
@router.patch("/me", response_model=UserOut)
def update_profile(
    body: ProfilePatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.name is not None:
        user.name = body.name
    if body.language is not None:
        user.language = body.language
    db.commit()
    db.refresh(user)
    return user
```

Add to `backend/app/routers/auth.py`:
```python
from app.schemas.auth import ChangePasswordRequest

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=12)

@router.post("/change-password", status_code=200)
def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="invalid_current_password")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 2: Add i18n keys**

In both locale files, add to `settings`:
```json
"profile": "Profil",
"changeName": "Name",
"changeLanguage": "Sprache",
"currentPassword": "Aktuelles Passwort",
"newPassword": "Neues Passwort",
"saveProfile": "Profil speichern",
"changePassword": "Passwort ändern",
"passwordChanged": "Passwort geändert"
```
(English equivalents in en.json)

- [ ] **Step 3: Add profile card to SettingsView.vue**

In `frontend/src/views/SettingsView.vue`, in `<script setup>` add:
```javascript
const profileName = ref(auth.user?.name || '')
const profileLang = ref(auth.user?.language || 'de')
const currentPassword = ref('')
const newPassword = ref('')

async function saveProfile() {
  const r = await api.patch('/users/me', { name: profileName.value, language: profileLang.value })
  if (r.ok) {
    await auth.fetchUser()
    toast.success(t('settings.save'))
  }
}

async function changePassword() {
  if (!currentPassword.value || !newPassword.value) return
  const r = await api.post('/auth/change-password', {
    current_password: currentPassword.value,
    new_password: newPassword.value,
  })
  if (r.ok) {
    currentPassword.value = ''
    newPassword.value = ''
    toast.success(t('settings.passwordChanged'))
  } else {
    toast.error(t('errors.generic'))
  }
}
```

In the template, insert before the household card:
```html
<Card>
  <CardHeader><CardTitle>{{ $t('settings.profile') }}</CardTitle></CardHeader>
  <CardContent class="space-y-4">
    <div class="space-y-1">
      <Label>{{ $t('settings.changeName') }}</Label>
      <Input v-model="profileName" />
    </div>
    <div class="space-y-1">
      <Label>{{ $t('settings.changeLanguage') }}</Label>
      <Select v-model="profileLang">
        <SelectTrigger><SelectValue /></SelectTrigger>
        <SelectContent>
          <SelectItem value="de">{{ $t('lang.de') }}</SelectItem>
          <SelectItem value="en">{{ $t('lang.en') }}</SelectItem>
        </SelectContent>
      </Select>
    </div>
    <Button @click="saveProfile">{{ $t('settings.saveProfile') }}</Button>
  </CardContent>
</Card>

<Card class="mt-4">
  <CardHeader><CardTitle>{{ $t('settings.changePassword') }}</CardTitle></CardHeader>
  <CardContent class="space-y-4">
    <div class="space-y-1">
      <Label>{{ $t('settings.currentPassword') }}</Label>
      <Input type="password" v-model="currentPassword" />
    </div>
    <div class="space-y-1">
      <Label>{{ $t('settings.newPassword') }}</Label>
      <Input type="password" v-model="newPassword" />
    </div>
    <Button @click="changePassword">{{ $t('settings.changePassword') }}</Button>
  </CardContent>
</Card>
```

- [ ] **Step 4: Write test for password change**

```python
# In backend/tests/test_password_reset.py, add:
def test_change_password(registered_client):
    r = registered_client.post("/api/auth/change-password", json={
        "current_password": "securepassword1",
        "new_password": "newpassword999999",
    })
    assert r.status_code == 200

def test_change_password_wrong_current(registered_client):
    r = registered_client.post("/api/auth/change-password", json={
        "current_password": "wrongpassword",
        "new_password": "newpassword999999",
    })
    assert r.status_code == 400
```

- [ ] **Step 5: Run tests**

```bash
cd backend && python -m pytest tests/test_password_reset.py -v
```
Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/auth.py backend/app/routers/users.py backend/app/schemas/users.py backend/tests/test_password_reset.py frontend/src/views/SettingsView.vue frontend/src/locales/de.json frontend/src/locales/en.json
git commit -m "feat: profile editing + password change in settings"
```

---

### Task 12: Frontend — AdminView.vue

**Files:**
- Create: `frontend/src/views/AdminView.vue`
- Modify: `frontend/src/locales/de.json` and `en.json`

- [ ] **Step 1: Add i18n keys**

Add to both locale files:
```json
"admin": {
  "title": "Admin",
  "users": "Benutzer",
  "status": "System-Status",
  "settings": "Einstellungen",
  "userCount": "Benutzer",
  "householdCount": "Haushalte",
  "transactionCount": "Transaktionen",
  "dbSize": "Datenbankgröße",
  "allowRegistration": "Registrierung erlauben",
  "defaultLanguage": "Standard-Sprache",
  "oidcEnabled": "OIDC aktivieren",
  "smtpHost": "SMTP-Host",
  "smtpPort": "SMTP-Port",
  "smtpUser": "SMTP-Benutzer",
  "smtpFrom": "Absender-E-Mail",
  "save": "Speichern",
  "banUser": "Sperren",
  "unbanUser": "Entsperren",
  "deleteUser": "Löschen",
  "confirmDelete": "Benutzer wirklich löschen?"
}
```
(English equivalents in en.json)

- [ ] **Step 2: Create AdminView.vue**

```vue
<!-- frontend/src/views/AdminView.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { useApi } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Switch } from '@/components/ui/switch'

const { t } = useI18n()
const api = useApi()

const users = ref([])
const status = ref(null)
const adminSettings = ref(null)

async function loadUsers() {
  const r = await api.get('/users')
  if (r.ok) users.value = await r.json()
}

async function loadStatus() {
  const r = await api.get('/admin/status')
  if (r.ok) status.value = await r.json()
}

async function loadSettings() {
  const r = await api.get('/admin/settings')
  if (r.ok) adminSettings.value = await r.json()
}

onMounted(() => Promise.all([loadUsers(), loadStatus(), loadSettings()]))

async function toggleUser(user) {
  await api.patch(`/users/${user.id}`, { is_active: !user.is_active })
  await loadUsers()
}

async function deleteUser(user) {
  if (!confirm(t('admin.confirmDelete'))) return
  await api.delete(`/users/${user.id}`)
  await loadUsers()
}

async function saveSettings() {
  const r = await api.patch('/admin/settings', {
    allow_registration: adminSettings.value.allow_registration,
    default_language: adminSettings.value.default_language,
    oidc_enabled: adminSettings.value.oidc_enabled,
    oidc_client_id: adminSettings.value.oidc_client_id,
    oidc_discovery_url: adminSettings.value.oidc_discovery_url,
    smtp_host: adminSettings.value.smtp_host,
    smtp_port: adminSettings.value.smtp_port,
    smtp_user: adminSettings.value.smtp_user,
    smtp_from: adminSettings.value.smtp_from,
  })
  if (r.ok) toast.success(t('admin.save'))
}

function formatBytes(b) {
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  return `${(b / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <div class="container mx-auto py-6 space-y-4">
    <h1 class="text-2xl font-bold">{{ $t('admin.title') }}</h1>

    <Tabs default-value="users">
      <TabsList>
        <TabsTrigger value="users">{{ $t('admin.users') }}</TabsTrigger>
        <TabsTrigger value="status">{{ $t('admin.status') }}</TabsTrigger>
        <TabsTrigger value="settings">{{ $t('admin.settings') }}</TabsTrigger>
      </TabsList>

      <TabsContent value="users" class="mt-4">
        <Card>
          <CardContent class="pt-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>{{ $t('settings.changeName') }}</TableHead>
                  <TableHead>Rolle</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="u in users" :key="u.id">
                  <TableCell>{{ u.id }}</TableCell>
                  <TableCell>{{ u.email }}</TableCell>
                  <TableCell>{{ u.name }}</TableCell>
                  <TableCell><Badge>{{ u.role }}</Badge></TableCell>
                  <TableCell>
                    <Badge :variant="u.is_active ? 'default' : 'destructive'">
                      {{ u.is_active ? 'aktiv' : 'gesperrt' }}
                    </Badge>
                  </TableCell>
                  <TableCell class="space-x-2">
                    <Button size="sm" variant="outline" @click="toggleUser(u)">
                      {{ u.is_active ? $t('admin.banUser') : $t('admin.unbanUser') }}
                    </Button>
                    <Button size="sm" variant="destructive" @click="deleteUser(u)">
                      {{ $t('admin.deleteUser') }}
                    </Button>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="status" class="mt-4">
        <Card v-if="status">
          <CardContent class="pt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('admin.userCount') }}</p>
              <p class="text-2xl font-bold">{{ status.user_count }}</p>
            </div>
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('admin.householdCount') }}</p>
              <p class="text-2xl font-bold">{{ status.household_count }}</p>
            </div>
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('admin.transactionCount') }}</p>
              <p class="text-2xl font-bold">{{ status.transaction_count }}</p>
            </div>
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('admin.dbSize') }}</p>
              <p class="text-2xl font-bold">{{ formatBytes(status.db_size_bytes) }}</p>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="settings" class="mt-4">
        <Card v-if="adminSettings">
          <CardContent class="pt-4 space-y-4">
            <div class="flex items-center gap-3">
              <Switch v-model:checked="adminSettings.allow_registration" />
              <Label>{{ $t('admin.allowRegistration') }}</Label>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-1">
                <Label>{{ $t('admin.smtpHost') }}</Label>
                <Input v-model="adminSettings.smtp_host" placeholder="smtp.example.com" />
              </div>
              <div class="space-y-1">
                <Label>{{ $t('admin.smtpPort') }}</Label>
                <Input v-model="adminSettings.smtp_port" type="number" />
              </div>
              <div class="space-y-1">
                <Label>{{ $t('admin.smtpUser') }}</Label>
                <Input v-model="adminSettings.smtp_user" />
              </div>
              <div class="space-y-1">
                <Label>{{ $t('admin.smtpFrom') }}</Label>
                <Input v-model="adminSettings.smtp_from" placeholder="helledger@example.com" />
              </div>
            </div>
            <div class="flex items-center gap-3">
              <Switch v-model:checked="adminSettings.oidc_enabled" />
              <Label>{{ $t('admin.oidcEnabled') }}</Label>
            </div>
            <div v-if="adminSettings.oidc_enabled" class="space-y-2">
              <div class="space-y-1">
                <Label>Client ID</Label>
                <Input v-model="adminSettings.oidc_client_id" />
              </div>
              <div class="space-y-1">
                <Label>Discovery URL</Label>
                <Input v-model="adminSettings.oidc_discovery_url" placeholder="https://idp.example.com/.well-known/openid-configuration" />
              </div>
            </div>
            <Button @click="saveSettings">{{ $t('admin.save') }}</Button>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/AdminView.vue frontend/src/locales/de.json frontend/src/locales/en.json
git commit -m "feat: AdminView with users/status/settings tabs"
```

---

### Task 13: Frontend — Router + nav update for admin

**Files:**
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/components/AppNav.vue`

- [ ] **Step 1: Add /admin route to router**

In `frontend/src/router/index.js`, add to routes array:
```javascript
{
  path: '/admin',
  component: () => import('../views/AdminView.vue'),
  meta: { requiresAuth: true, requiresAdmin: true }
},
```

Update the navigation guard to check `requiresAdmin`:
```javascript
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return next('/login')
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return next('/dashboard')
  }
  if ((to.path === '/login' || to.path === '/register') && auth.isAuthenticated) {
    return next('/dashboard')
  }
  next()
})
```

- [ ] **Step 2: Add "Admin" link to AppNav.vue**

In `frontend/src/components/AppNav.vue`, in the nav links list, add after "backup" link:
```html
<RouterLink v-if="auth.isAdmin" to="/admin" ...>
  {{ $t('nav.admin') }}
</RouterLink>
```

Add to both locale files under `nav`:
```json
"admin": "Admin"
```

- [ ] **Step 3: Run full test suite**

```bash
cd backend && python -m pytest tests/ -q 2>&1 | tail -5
```
Expected: all pass

- [ ] **Step 4: Commit**

```bash
git add frontend/src/router/index.js frontend/src/components/AppNav.vue frontend/src/locales/de.json frontend/src/locales/en.json
git commit -m "feat: /admin route with admin guard + nav link"
```
