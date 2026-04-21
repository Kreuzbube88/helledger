def test_list_empty(registered_client):
    r = registered_client.get("/api/net-worth")
    assert r.status_code == 200
    assert r.json() == []


def test_create_snapshot(registered_client):
    body = {"snapshot_date": "2025-01-01", "total_assets": "50000.00", "total_liabilities": "10000.00"}
    r = registered_client.post("/api/net-worth", json=body)
    assert r.status_code == 201
    data = r.json()
    assert float(data["net_worth"]) == 40000.0
    assert float(data["total_assets"]) == 50000.0
    assert data["household_id"] is not None


def test_delete_snapshot(registered_client):
    body = {"snapshot_date": "2025-02-01", "total_assets": "60000.00", "total_liabilities": "15000.00"}
    snap = registered_client.post("/api/net-worth", json=body).json()
    r = registered_client.delete(f"/api/net-worth/{snap['id']}")
    assert r.status_code == 204
    assert registered_client.get("/api/net-worth").json() == []


def test_delete_not_found(registered_client):
    r = registered_client.delete("/api/net-worth/9999")
    assert r.status_code == 404
