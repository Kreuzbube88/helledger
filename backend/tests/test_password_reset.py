import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import pytest

from app.database import get_db
from app.models.user import User, PasswordResetToken


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
    # Register user
    client.post("/api/auth/register", json={"email": "flow@example.com", "password": "securepassword1", "name": "Flow User"})

    # Simulate token creation (bypass email)
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    db = next(client.app.dependency_overrides[get_db]())
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


def test_password_reset_token_single_use(client):
    """Token cannot be used twice."""
    client.post("/api/auth/register", json={"email": "once@example.com", "password": "securepassword1", "name": "Once User"})
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    db = next(client.app.dependency_overrides[get_db]())
    user = db.query(User).filter(User.email == "once@example.com").first()
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()

    r1 = client.post("/api/auth/password-reset/confirm", json={"token": raw, "new_password": "newpassword111"})
    assert r1.status_code == 200
    r2 = client.post("/api/auth/password-reset/confirm", json={"token": raw, "new_password": "newpassword222"})
    assert r2.status_code == 400  # token consumed
