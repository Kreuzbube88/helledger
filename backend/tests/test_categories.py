def _create_cat(client, name="Fixkosten", cat_type="fixed", **kwargs):
    return client.post("/api/categories", json={
        "name": name, "category_type": cat_type, **kwargs,
    })


def test_create_category(registered_client):
    r = _create_cat(registered_client)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Fixkosten"
    assert body["archived"] is False
    assert body["parent_id"] is None


def test_list_categories_tree(registered_client):
    parent_id = _create_cat(registered_client, "Fixkosten", "fixed").json()["id"]
    _create_cat(registered_client, "Miete", "fixed", parent_id=parent_id)
    r = registered_client.get("/api/categories")
    assert r.status_code == 200
    tree = r.json()
    assert len(tree) == 1
    assert tree[0]["name"] == "Fixkosten"
    assert len(tree[0]["children"]) == 1
    assert tree[0]["children"][0]["name"] == "Miete"


def test_list_categories_by_type(registered_client):
    _create_cat(registered_client, "Gehalt", "income")
    _create_cat(registered_client, "Miete", "fixed")
    _create_cat(registered_client, "Lebensmittel", "variable")
    r = registered_client.get("/api/categories")
    names = [c["name"] for c in r.json()]
    assert "Gehalt" in names and "Miete" in names and "Lebensmittel" in names


def test_get_category(registered_client):
    cat_id = _create_cat(registered_client).json()["id"]
    r = registered_client.get(f"/api/categories/{cat_id}")
    assert r.status_code == 200
    assert r.json()["id"] == cat_id


def test_patch_category(registered_client):
    cat_id = _create_cat(registered_client).json()["id"]
    r = registered_client.patch(f"/api/categories/{cat_id}", json={"name": "Neu", "color": "#ff0000"})
    assert r.status_code == 200
    assert r.json()["name"] == "Neu"
    assert r.json()["color"] == "#ff0000"


def test_patch_category_parent(registered_client):
    p_id = _create_cat(registered_client, "Eltern", "fixed").json()["id"]
    c_id = _create_cat(registered_client, "Kind", "fixed").json()["id"]
    r = registered_client.patch(f"/api/categories/{c_id}", json={"parent_id": p_id})
    assert r.status_code == 200
    assert r.json()["parent_id"] == p_id


def test_archive_category(registered_client):
    cat_id = _create_cat(registered_client).json()["id"]
    r = registered_client.delete(f"/api/categories/{cat_id}")
    assert r.status_code == 204
    r2 = registered_client.get(f"/api/categories/{cat_id}")
    assert r2.json()["archived"] is True


def test_archived_excluded_from_tree_by_default(registered_client):
    cat_id = _create_cat(registered_client).json()["id"]
    registered_client.delete(f"/api/categories/{cat_id}")
    r = registered_client.get("/api/categories")
    assert len(r.json()) == 0


def test_category_isolation(registered_client, second_user_client):
    cat_id = _create_cat(registered_client).json()["id"]
    r = second_user_client.get(f"/api/categories/{cat_id}")
    assert r.status_code == 404
