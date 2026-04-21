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


def test_admin_requires_admin_role(client):
    # register second user (non-admin)
    client.post("/api/auth/register", json={"email": "admin_first@example.com", "password": "securepassword1", "name": "First"})
    client.post("/api/auth/register", json={"email": "regular@example.com", "password": "securepassword1", "name": "Regular"})
    r = client.post("/api/auth/login", json={"email": "regular@example.com", "password": "securepassword1"})
    token = r.json()["access_token"]
    r2 = client.get("/api/admin/status", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 403
