def test_month_view_empty(registered_client):
    r = registered_client.get("/api/dashboard/month?year=2025&month=1")
    assert r.status_code == 200
    data = r.json()
    assert data["year"] == 2025
    assert data["month"] == 1
    assert len(data["sections"]) == 3
    assert data["summary"]["total_income"] == 0.0
    assert data["summary"]["savings_rate"] == 0.0


def test_month_view_with_income_and_expense(registered_client):
    acc = registered_client.post(
        "/api/accounts",
        json={"name": "Main", "account_type": "checking", "starting_balance": 0, "currency": "EUR"},
    ).json()
    inc_cat = registered_client.post(
        "/api/categories",
        json={"name": "Salary", "category_type": "income", "color": "#10b981"},
    ).json()
    exp_cat = registered_client.post(
        "/api/categories",
        json={"name": "Rent", "category_type": "fixed", "color": "#f43f5e"},
    ).json()

    registered_client.post(
        "/api/transactions",
        json={
            "date": "2025-03-01",
            "description": "Salary",
            "amount": 3000.0,
            "transaction_type": "income",
            "account_id": acc["id"],
            "category_id": inc_cat["id"],
        },
    )
    registered_client.post(
        "/api/transactions",
        json={
            "date": "2025-03-01",
            "description": "Rent",
            "amount": -1200.0,
            "transaction_type": "expense",
            "account_id": acc["id"],
            "category_id": exp_cat["id"],
        },
    )

    r = registered_client.get("/api/dashboard/month?year=2025&month=3")
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["total_income"] == 3000.0
    assert data["summary"]["total_expense"] == 1200.0
    assert data["summary"]["balance"] == 1800.0
    assert abs(data["summary"]["savings_rate"] - 60.0) < 0.01
