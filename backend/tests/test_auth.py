import pytest


def test_register_first_user_is_admin(client):
    r = client.post("/api/auth/register", json={
        "email": "admin@example.com", "password": "securepassword1", "name": "Admin"
    })
    assert r.status_code == 201
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "admin@example.com"
    assert me.json()["role"] == "admin"
    assert "password_hash" not in me.json()


def test_register_second_user_is_not_admin(client):
    client.post("/api/auth/register", json={
        "email": "first@example.com", "password": "securepassword1", "name": "First"
    })
    r = client.post("/api/auth/register", json={
        "email": "second@example.com", "password": "securepassword1", "name": "Second"
    })
    assert r.status_code == 201
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["role"] == "user"


def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "securepassword1", "name": "A"}
    client.post("/api/auth/register", json=payload)
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 409
    assert r.json()["detail"] == "email_taken"


def test_register_password_too_short(client):
    r = client.post("/api/auth/register", json={
        "email": "x@example.com", "password": "short", "name": "X"
    })
    assert r.status_code == 422


@pytest.fixture()
def registered(client):
    client.post("/api/auth/register", json={
        "email": "user@example.com", "password": "securepassword1", "name": "User"
    })
    return client


def test_login_success(registered):
    r = registered.post("/api/auth/login", json={
        "email": "user@example.com", "password": "securepassword1"
    })
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "refresh_token" in registered.cookies


def test_login_wrong_password(registered):
    r = registered.post("/api/auth/login", json={
        "email": "user@example.com", "password": "wrongpassword12"
    })
    assert r.status_code == 401
    assert r.json()["detail"] == "invalid_credentials"


def test_login_unknown_email(client):
    r = client.post("/api/auth/login", json={
        "email": "nobody@example.com", "password": "securepassword1"
    })
    assert r.status_code == 401


def test_me_returns_current_user(registered):
    login_r = registered.post("/api/auth/login", json={
        "email": "user@example.com", "password": "securepassword1"
    })
    token = login_r.json()["access_token"]
    r = registered.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "user@example.com"


def test_me_requires_auth(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 403


def test_me_invalid_token(client):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token"})
    assert r.status_code == 401


def test_refresh_returns_new_token(registered):
    registered.post("/api/auth/login", json={
        "email": "user@example.com", "password": "securepassword1"
    })
    r = registered.post("/api/auth/refresh")
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_refresh_without_cookie_fails(client):
    r = client.post("/api/auth/refresh")
    assert r.status_code == 401


def test_logout_clears_cookie(registered):
    registered.post("/api/auth/login", json={
        "email": "user@example.com", "password": "securepassword1"
    })
    r = registered.post("/api/auth/logout")
    assert r.status_code == 204
    assert "refresh_token" not in registered.cookies


def test_logout_invalidates_refresh_token(registered):
    registered.post("/api/auth/login", json={
        "email": "user@example.com", "password": "securepassword1"
    })
    registered.post("/api/auth/logout")
    r = registered.post("/api/auth/refresh")
    assert r.status_code == 401


def test_register_no_household_until_wizard(client):
    r = client.post("/api/auth/register", json={
        "email": "h@example.com", "password": "securepassword1", "name": "H"
    })
    assert r.status_code == 201
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["active_household_id"] is None


def test_login_me_active_household_after_creation(client):
    r = client.post("/api/auth/register", json={
        "email": "h@example.com", "password": "securepassword1", "name": "H"
    })
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    hh = client.post("/api/households", json={"name": "My Home"}, headers=headers).json()
    client.post(f"/api/households/{hh['id']}/activate", json={}, headers=headers)
    me = client.get("/api/auth/me", headers=headers)
    assert me.json()["active_household_id"] == hh["id"]
