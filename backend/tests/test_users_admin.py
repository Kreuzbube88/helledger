import pytest


def test_list_users_requires_admin(second_user_client):
    r = second_user_client.get("/api/users")
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
