import pytest


@pytest.fixture()
def backup_client(registered_client, tmp_path, monkeypatch):
    from app import config as cfg
    backup_dir = tmp_path / "backups"
    db_file = tmp_path / "helledger.db"
    db_file.write_bytes(b"SQLite format 3 fake db content")
    monkeypatch.setattr(cfg.settings, "BACKUP_PATH", str(backup_dir))
    monkeypatch.setattr(cfg.settings, "DATABASE_PATH", str(db_file))
    return registered_client


@pytest.fixture()
def non_admin_client(client):
    client.post("/api/auth/register", json={
        "email": "admin@x.com", "password": "password12345", "name": "Admin",
    })
    client.post("/api/auth/register", json={
        "email": "user@x.com", "password": "password12345", "name": "User",
    })
    r = client.post("/api/auth/login", json={"email": "user@x.com", "password": "password12345"})
    client.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return client


def test_get_settings_default(backup_client):
    r = backup_client.get("/api/backup/settings")
    assert r.status_code == 200
    assert r.json()["backup_retention_days"] == 7


def test_patch_settings(backup_client):
    r = backup_client.patch("/api/backup/settings", json={"backup_retention_days": 14})
    assert r.status_code == 200
    assert r.json()["backup_retention_days"] == 14

    r2 = backup_client.get("/api/backup/settings")
    assert r2.json()["backup_retention_days"] == 14


def test_patch_settings_rejects_zero(backup_client):
    r = backup_client.patch("/api/backup/settings", json={"backup_retention_days": 0})
    assert r.status_code == 422


def test_trigger_backup_creates_file(backup_client):
    r = backup_client.post("/api/backup/trigger")
    assert r.status_code == 201
    body = r.json()
    assert "filename" in body
    assert body["size_bytes"] > 0
    assert "created_at" in body


def test_list_backups_empty(backup_client):
    r = backup_client.get("/api/backup/list")
    assert r.status_code == 200
    assert r.json() == []


def test_list_backups_after_trigger(backup_client):
    backup_client.post("/api/backup/trigger")
    r = backup_client.get("/api/backup/list")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["size_bytes"] > 0


def test_delete_backup(backup_client):
    backup_client.post("/api/backup/trigger")
    filename = backup_client.get("/api/backup/list").json()[0]["filename"]

    r = backup_client.delete(f"/api/backup/{filename}")
    assert r.status_code == 204
    assert backup_client.get("/api/backup/list").json() == []


def test_delete_invalid_filename(backup_client):
    r = backup_client.delete("/api/backup/..%2Fevil.db")
    assert r.status_code in (400, 404, 405)


def test_download_backup(backup_client):
    backup_client.post("/api/backup/trigger")
    filename = backup_client.get("/api/backup/list").json()[0]["filename"]

    r = backup_client.get(f"/api/backup/{filename}/download")
    assert r.status_code == 200
    assert len(r.content) > 0


def test_non_admin_settings_returns_403(non_admin_client):
    r = non_admin_client.get("/api/backup/settings")
    assert r.status_code == 403


def test_non_admin_trigger_returns_403(non_admin_client):
    r = non_admin_client.post("/api/backup/trigger")
    assert r.status_code == 403


def test_non_admin_list_returns_403(non_admin_client):
    r = non_admin_client.get("/api/backup/list")
    assert r.status_code == 403


def test_non_admin_download_returns_403(non_admin_client):
    r = non_admin_client.get("/api/backup/helledger_20260101_120000.db/download")
    assert r.status_code == 403


def test_non_admin_delete_returns_403(non_admin_client):
    r = non_admin_client.delete("/api/backup/helledger_20260101_120000.db")
    assert r.status_code == 403
