import os

# Must be before any app import
os.environ["SECRET_KEY"] = "test-secret-key-minimum-32-chars!!"
os.environ["DATABASE_PATH"] = ":memory:"
os.environ["TESTING"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.rate_limit import _login_limiter
from app.database import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    _login_limiter.reset()
    yield


def _make_engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _setup_override(engine) -> None:
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def client():
    engine = _make_engine()
    Base.metadata.create_all(engine)
    _setup_override(engine)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def _shared_engine():
    engine = _make_engine()
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def registered_client(_shared_engine):
    _setup_override(_shared_engine)
    with TestClient(app) as c:
        c.post("/api/auth/register", json={
            "email": "usera@example.com",
            "password": "securepassword1",
            "name": "User A",
        })
        r = c.post("/api/auth/login", json={
            "email": "usera@example.com",
            "password": "securepassword1",
        })
        c.headers.update(auth_headers(r.json()["access_token"]))
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def second_user_client(_shared_engine, registered_client):
    # dependency override already active via registered_client
    with TestClient(app) as c:
        c.post("/api/auth/register", json={
            "email": "userb@example.com",
            "password": "securepassword1",
            "name": "User B",
        })
        r = c.post("/api/auth/login", json={
            "email": "userb@example.com",
            "password": "securepassword1",
        })
        c.headers.update(auth_headers(r.json()["access_token"]))
        yield c
