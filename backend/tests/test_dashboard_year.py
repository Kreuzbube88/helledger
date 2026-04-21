import pytest


def test_year_view_empty(registered_client):
    r = registered_client.get("/api/dashboard/year?year=2025")
    assert r.status_code == 200
    data = r.json()
    assert data["year"] == 2025
    assert data["categories"] == []
    assert len(data["monthly_income"]) == 12
    assert len(data["monthly_expense"]) == 12
    assert len(data["monthly_balance"]) == 12
    assert all(v == 0.0 for v in data["monthly_income"])


def test_year_view_with_transactions(registered_client):
    acc = registered_client.post("/api/accounts", json={
        "name": "Checking", "account_type": "checking",
        "starting_balance": "1000.00", "currency": "EUR",
    }).json()
    cat = registered_client.post("/api/categories", json={
        "name": "Salary", "category_type": "income", "color": "#10b981",
    }).json()

    registered_client.post("/api/transactions", json={
        "date": "2025-01-15",
        "description": "Salary",
        "amount": "3000.00",
        "transaction_type": "income",
        "account_id": acc["id"],
        "category_id": cat["id"],
    })

    r = registered_client.get("/api/dashboard/year?year=2025")
    assert r.status_code == 200
    data = r.json()
    assert data["monthly_income"][0] == 3000.0  # January
    assert data["monthly_balance"][0] == 3000.0
