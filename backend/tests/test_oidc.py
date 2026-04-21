import pytest


def test_oidc_login_disabled(client):
    r = client.get("/api/auth/oidc/login", follow_redirects=False)
    assert r.status_code == 404


def test_oidc_enabled_check(client):
    r = client.get("/api/auth/oidc/enabled")
    assert r.status_code == 200
    assert r.json()["enabled"] is False
