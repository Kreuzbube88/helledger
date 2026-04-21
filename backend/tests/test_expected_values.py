def _create_cat(client, name="Miete", cat_type="fixed"):
    return client.post("/api/categories", json={
        "name": name, "category_type": cat_type
    }).json()["id"]


def _create_ev(client, category_id, amount="1200.00", valid_from="2026-01-01"):
    return client.post("/api/expected-values", json={
        "category_id": category_id, "amount": amount, "valid_from": valid_from,
    })


def test_create_expected_value(registered_client):
    cat_id = _create_cat(registered_client)
    r = _create_ev(registered_client, cat_id)
    assert r.status_code == 201
    body = r.json()
    assert body["amount"] == "1200.00"
    assert body["valid_from"] == "2026-01-01"
    assert body["valid_until"] is None


def test_list_expected_values(registered_client):
    cat_id = _create_cat(registered_client)
    _create_ev(registered_client, cat_id)
    r = registered_client.get("/api/expected-values")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_list_by_category(registered_client):
    cat1 = _create_cat(registered_client, "Miete")
    cat2 = _create_cat(registered_client, "Strom")
    _create_ev(registered_client, cat1)
    _create_ev(registered_client, cat2)
    r = registered_client.get(f"/api/expected-values?category_id={cat1}")
    assert len(r.json()) == 1
    assert r.json()[0]["category_id"] == cat1


def test_autoclose_open_entry(registered_client):
    cat_id = _create_cat(registered_client)
    _create_ev(registered_client, cat_id, "1000.00", "2026-01-01")
    r2 = _create_ev(registered_client, cat_id, "1200.00", "2026-04-01")
    assert r2.status_code == 201
    all_evs = registered_client.get(f"/api/expected-values?category_id={cat_id}").json()
    assert len(all_evs) == 2
    closed = next(e for e in all_evs if e["amount"] == "1000.00")
    assert closed["valid_until"] == "2026-03-31"
    open_ev = next(e for e in all_evs if e["amount"] == "1200.00")
    assert open_ev["valid_until"] is None


def test_patch_expected_value(registered_client):
    cat_id = _create_cat(registered_client)
    ev_id = _create_ev(registered_client, cat_id).json()["id"]
    r = registered_client.patch(f"/api/expected-values/{ev_id}", json={"amount": "999.00"})
    assert r.status_code == 200
    assert r.json()["amount"] == "999.00"


def test_delete_expected_value(registered_client):
    cat_id = _create_cat(registered_client)
    ev_id = _create_ev(registered_client, cat_id).json()["id"]
    r = registered_client.delete(f"/api/expected-values/{ev_id}")
    assert r.status_code == 204
    assert len(registered_client.get("/api/expected-values").json()) == 0


def test_expected_value_isolation(registered_client, second_user_client):
    cat_id = _create_cat(registered_client)
    _create_ev(registered_client, cat_id)
    r = second_user_client.get("/api/expected-values")
    assert len(r.json()) == 0


def test_expected_value_wrong_category(registered_client, second_user_client):
    cat_b = _create_cat(second_user_client, "Fremd")
    r = _create_ev(registered_client, cat_b)
    assert r.status_code == 404
