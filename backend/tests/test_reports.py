import pytest


def _acc(client, name="Checking", starting_balance="0.00"):
    return client.post("/api/accounts", json={
        "name": name, "account_type": "checking",
        "starting_balance": starting_balance, "currency": "EUR",
    }).json()


def _cat(client, name="Food", category_type="variable"):
    return client.post("/api/categories", json={"name": name, "category_type": category_type}).json()


def _tx(client, **kwargs):
    defaults = {
        "account_id": None, "category_id": None,
        "amount": "50.00", "date": "2026-04-01",
        "description": "Test", "transaction_type": "expense",
    }
    defaults.update(kwargs)
    return client.post("/api/transactions", json=defaults)


def test_expenses_by_category(registered_client):
    acc = _acc(registered_client)
    food = _cat(registered_client, "Food")
    rent = _cat(registered_client, "Rent", "fixed")
    _tx(registered_client, account_id=acc["id"], category_id=food["id"],
        amount="200.00", transaction_type="expense", date="2026-03-10")
    _tx(registered_client, account_id=acc["id"], category_id=food["id"],
        amount="100.00", transaction_type="expense", date="2026-03-20")
    _tx(registered_client, account_id=acc["id"], category_id=rent["id"],
        amount="800.00", transaction_type="expense", date="2026-03-01")
    inc_cat = _cat(registered_client, "Salary", "income")
    _tx(registered_client, account_id=acc["id"], category_id=inc_cat["id"],
        amount="3000.00", transaction_type="income", date="2026-03-25")

    r = registered_client.get(
        "/api/reports/expenses-by-category?from_date=2026-03-01&to_date=2026-03-31"
    )
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    totals = {i["category_name"]: i["total"] for i in items}
    assert totals["Food"] == "300.00"
    assert totals["Rent"] == "800.00"


def test_expenses_by_category_account_filter(registered_client):
    acc1 = _acc(registered_client, "A1")
    acc2 = _acc(registered_client, "A2")
    cat = _cat(registered_client)
    _tx(registered_client, account_id=acc1["id"], category_id=cat["id"],
        amount="100.00", transaction_type="expense", date="2026-03-01")
    _tx(registered_client, account_id=acc2["id"], category_id=cat["id"],
        amount="200.00", transaction_type="expense", date="2026-03-01")

    r = registered_client.get(
        f"/api/reports/expenses-by-category?from_date=2026-03-01&to_date=2026-03-31&account_id={acc1['id']}"
    )
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["total"] == "100.00"


def test_expenses_by_category_invalid_dates(registered_client):
    r = registered_client.get(
        "/api/reports/expenses-by-category?from_date=2026-04-30&to_date=2026-04-01"
    )
    assert r.status_code == 400


def test_monthly_trend(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client)
    inc_cat = _cat(registered_client, "Salary", "income")
    _tx(registered_client, account_id=acc["id"], category_id=inc_cat["id"],
        amount="2000.00", transaction_type="income", date="2026-01-15")
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="500.00", transaction_type="expense", date="2026-01-20")
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="600.00", transaction_type="expense", date="2026-02-10")

    r = registered_client.get(
        "/api/reports/monthly-trend?from_date=2026-01-01&to_date=2026-02-28"
    )
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    jan = next(m for m in items if m["month"] == 1)
    assert jan["income"] == "2000.00"
    assert jan["expenses"] == "500.00"
    feb = next(m for m in items if m["month"] == 2)
    assert feb["income"] == "0.00"
    assert feb["expenses"] == "600.00"


def test_balance_history(registered_client):
    acc = _acc(registered_client, "Main", "1000.00")
    cat = _cat(registered_client)
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="200.00", transaction_type="expense", date="2026-03-01")
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="100.00", transaction_type="expense", date="2026-04-05")

    r = registered_client.get(
        f"/api/reports/balance-history?from_date=2026-04-01&to_date=2026-04-05&account_id={acc['id']}"
    )
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 5
    assert items[0]["balance"] == "800.00"  # April 1: 1000 - 200 pre-range
    assert items[4]["balance"] == "700.00"  # April 5: -100


def test_balance_history_requires_account_id(registered_client):
    r = registered_client.get(
        "/api/reports/balance-history?from_date=2026-04-01&to_date=2026-04-30"
    )
    assert r.status_code == 422


def test_balance_history_wrong_household(registered_client, second_user_client):
    acc = _acc(registered_client, "Mine")
    r = second_user_client.get(
        f"/api/reports/balance-history?from_date=2026-04-01&to_date=2026-04-30&account_id={acc['id']}"
    )
    assert r.status_code == 403


def test_reports_soll_ist_scales_by_months(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client, "Food")
    registered_client.post("/api/budgets", json={
        "category_id": cat["id"], "amount": "300.00", "valid_from": "2026-01-01",
    })
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="120.00", transaction_type="expense", date="2026-04-05")
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="80.00", transaction_type="expense", date="2026-05-10")

    r = registered_client.get(
        "/api/reports/soll-ist?from_date=2026-04-01&to_date=2026-05-31"
    )
    assert r.status_code == 200
    nodes = r.json()
    node = next(n for n in nodes if n["id"] == cat["id"])
    assert node["soll"] == "600.00"   # 300 * 2 months
    assert node["ist"] == "-200.00"
