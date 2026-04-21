def _create_cat(client, name="Lebensmittel"):
    return client.post("/api/categories", json={
        "name": name, "category_type": "variable"
    }).json()["id"]


def _create_budget(client, category_id, amount="300.00", valid_from="2026-01-01"):
    return client.post("/api/budgets", json={
        "category_id": category_id, "amount": amount, "valid_from": valid_from,
    })


def test_create_budget(registered_client):
    cat_id = _create_cat(registered_client)
    r = _create_budget(registered_client, cat_id)
    assert r.status_code == 201
    assert r.json()["amount"] == "300.00"
    assert r.json()["valid_until"] is None


def test_list_budgets(registered_client):
    cat_id = _create_cat(registered_client)
    _create_budget(registered_client, cat_id)
    r = registered_client.get("/api/budgets")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_autoclose_open_budget(registered_client):
    cat_id = _create_cat(registered_client)
    _create_budget(registered_client, cat_id, "300.00", "2026-01-01")
    _create_budget(registered_client, cat_id, "400.00", "2026-04-01")
    all_b = registered_client.get(f"/api/budgets?category_id={cat_id}").json()
    assert len(all_b) == 2
    closed = next(b for b in all_b if b["amount"] == "300.00")
    assert closed["valid_until"] == "2026-03-31"


def test_patch_budget(registered_client):
    cat_id = _create_cat(registered_client)
    b_id = _create_budget(registered_client, cat_id).json()["id"]
    r = registered_client.patch(f"/api/budgets/{b_id}", json={"amount": "500.00"})
    assert r.status_code == 200
    assert r.json()["amount"] == "500.00"


def test_delete_budget(registered_client):
    cat_id = _create_cat(registered_client)
    b_id = _create_budget(registered_client, cat_id).json()["id"]
    r = registered_client.delete(f"/api/budgets/{b_id}")
    assert r.status_code == 204


def test_budget_isolation(registered_client, second_user_client):
    cat_id = _create_cat(registered_client)
    _create_budget(registered_client, cat_id)
    r = second_user_client.get("/api/budgets")
    assert len(r.json()) == 0
