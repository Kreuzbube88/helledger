import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars!!")
os.environ.setdefault("TESTING", "true")

import pytest
from jose import JWTError
from app.auth.jwt import create_access_token, create_refresh_token, decode_access_token


def test_access_token_round_trip():
    token = create_access_token(user_id=42)
    assert decode_access_token(token) == 42


def test_refresh_token_raw_and_hash_differ():
    raw, token_hash = create_refresh_token()
    assert raw != token_hash
    assert len(token_hash) == 64  # sha256 hex


def test_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_access_token("not.a.token")
