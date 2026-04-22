def test_list_households_returns_own(registered_client):
    r = registered_client.get("/api/households")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Household"


def test_create_household(registered_client):
    r = registered_client.post("/api/households", json={"name": "Zweithaushalt"})
    assert r.status_code == 201
    assert r.json()["name"] == "Zweithaushalt"


def test_create_household_requires_auth(client):
    r = client.post("/api/households", json={"name": "X"})
    assert r.status_code == 403


def test_rename_household_owner(registered_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = registered_client.patch(f"/api/households/{hh_id}", json={"name": "Umbenannt"})
    assert r.status_code == 200
    assert r.json()["name"] == "Umbenannt"


def test_rename_household_forbidden_for_non_owner(registered_client, second_user_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = second_user_client.patch(f"/api/households/{hh_id}", json={"name": "X"})
    assert r.status_code == 403


def test_delete_last_household_forbidden(registered_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = registered_client.delete(f"/api/households/{hh_id}")
    assert r.status_code == 400
    assert r.json()["detail"] == "cannot_delete_last_household"


def test_delete_household(registered_client):
    registered_client.post("/api/households", json={"name": "Zweiter"})
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = registered_client.delete(f"/api/households/{hh_id}")
    assert r.status_code == 204


def test_activate_household(registered_client):
    r2 = registered_client.post("/api/households", json={"name": "Zweiter"})
    hh2_id = r2.json()["id"]
    r = registered_client.post(f"/api/households/{hh2_id}/activate")
    assert r.status_code == 200
    me = registered_client.get("/api/auth/me").json()
    assert me["active_household_id"] == hh2_id


def test_activate_foreign_household_forbidden(registered_client, second_user_client):
    hh_id = second_user_client.get("/api/households").json()[0]["id"]
    r = registered_client.post(f"/api/households/{hh_id}/activate")
    assert r.status_code == 403


def test_list_members(registered_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = registered_client.get(f"/api/households/{hh_id}/members")
    assert r.status_code == 200
    members = r.json()
    assert len(members) == 1
    assert members[0]["role"] == "owner"


def test_add_member(registered_client, second_user_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = registered_client.post(
        f"/api/households/{hh_id}/members",
        json={"email": "userb@example.com"},
    )
    assert r.status_code == 201
    members = registered_client.get(f"/api/households/{hh_id}/members").json()
    assert len(members) == 2


def test_add_nonexistent_member(registered_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = registered_client.post(
        f"/api/households/{hh_id}/members",
        json={"email": "nobody@example.com"},
    )
    assert r.status_code == 404


def test_remove_member(registered_client, second_user_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    registered_client.post(
        f"/api/households/{hh_id}/members",
        json={"email": "userb@example.com"},
    )
    me_b = second_user_client.get("/api/auth/me").json()
    r = registered_client.delete(f"/api/households/{hh_id}/members/{me_b['id']}")
    assert r.status_code == 204


def test_household_isolation(registered_client, second_user_client):
    hh_a = registered_client.get("/api/households").json()[0]["id"]
    hh_b = second_user_client.get("/api/households").json()[0]["id"]
    assert hh_a != hh_b
    r = second_user_client.get(f"/api/households/{hh_a}/members")
    assert r.status_code == 403
