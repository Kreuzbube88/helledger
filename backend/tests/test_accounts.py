def _create_account(client, **kwargs):
    payload = {
        "name": "Girokonto",
        "account_type": "checking",
        "starting_balance": "1000.00",
        "currency": "EUR",
        **kwargs,
    }
    return client.post("/api/accounts", json=payload)


def test_create_account(registered_client):
    r = _create_account(registered_client)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Girokonto"
    assert body["starting_balance"] == "1000.00"
    assert body["archived"] is False


def test_list_accounts(registered_client):
    _create_account(registered_client, name="A")
    _create_account(registered_client, name="B")
    r = registered_client.get("/api/accounts")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_excludes_archived_by_default(registered_client):
    r = _create_account(registered_client)
    acc_id = r.json()["id"]
    registered_client.delete(f"/api/accounts/{acc_id}")
    r2 = registered_client.get("/api/accounts")
    assert len(r2.json()) == 0


def test_list_includes_archived_when_requested(registered_client):
    r = _create_account(registered_client)
    acc_id = r.json()["id"]
    registered_client.delete(f"/api/accounts/{acc_id}")
    r2 = registered_client.get("/api/accounts?include_archived=true")
    assert len(r2.json()) == 1
    assert r2.json()[0]["archived"] is True


def test_get_account(registered_client):
    acc_id = _create_account(registered_client).json()["id"]
    r = registered_client.get(f"/api/accounts/{acc_id}")
    assert r.status_code == 200
    assert r.json()["id"] == acc_id


def test_patch_account(registered_client):
    acc_id = _create_account(registered_client).json()["id"]
    r = registered_client.patch(f"/api/accounts/{acc_id}", json={"name": "Sparkonto"})
    assert r.status_code == 200
    assert r.json()["name"] == "Sparkonto"


def test_delete_account_soft(registered_client):
    acc_id = _create_account(registered_client).json()["id"]
    r = registered_client.delete(f"/api/accounts/{acc_id}")
    assert r.status_code == 204
    r2 = registered_client.get(f"/api/accounts/{acc_id}")
    assert r2.json()["archived"] is True


def test_account_isolation(registered_client, second_user_client):
    acc_id = _create_account(registered_client).json()["id"]
    r = second_user_client.get(f"/api/accounts/{acc_id}")
    assert r.status_code == 404


def test_account_requires_auth(client):
    r = client.get("/api/accounts")
    assert r.status_code == 403
