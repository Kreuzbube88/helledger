import pytest


def _acc(client, name="Checking", account_type="checking"):
    return client.post("/api/accounts", json={
        "name": name, "account_type": account_type,
        "starting_balance": "0.00", "currency": "EUR",
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


def test_create_expense(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client)
    r = _tx(registered_client, account_id=acc["id"], category_id=cat["id"])
    assert r.status_code == 201
    body = r.json()
    assert body["amount"] == "-50.00"
    assert body["transaction_type"] == "expense"


def test_create_income(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client, category_type="income")
    r = _tx(registered_client, account_id=acc["id"], category_id=cat["id"], transaction_type="income")
    assert r.status_code == 201
    assert r.json()["amount"] == "50.00"


def test_expense_requires_category(registered_client):
    acc = _acc(registered_client)
    r = _tx(registered_client, account_id=acc["id"], category_id=None, transaction_type="expense")
    assert r.status_code == 422


def test_create_transfer(registered_client):
    acc1 = _acc(registered_client, "Acc1")
    acc2 = _acc(registered_client, "Acc2")
    r = registered_client.post("/api/transactions/transfer", json={
        "from_account_id": acc1["id"], "to_account_id": acc2["id"],
        "amount": "100.00", "date": "2026-04-01", "description": "Transfer",
    })
    assert r.status_code == 201
    rows = r.json()
    assert len(rows) == 2
    debit = next(x for x in rows if x["account_id"] == acc1["id"])
    credit = next(x for x in rows if x["account_id"] == acc2["id"])
    assert debit["amount"] == "-100.00"
    assert credit["amount"] == "100.00"
    assert debit["transfer_peer_id"] == credit["id"]
    assert credit["transfer_peer_id"] == debit["id"]


def test_patch_transfer_is_405(registered_client):
    acc1 = _acc(registered_client, "A1")
    acc2 = _acc(registered_client, "A2")
    rows = registered_client.post("/api/transactions/transfer", json={
        "from_account_id": acc1["id"], "to_account_id": acc2["id"],
        "amount": "50.00", "date": "2026-04-01", "description": "x",
    }).json()
    tx_id = rows[0]["id"]
    r = registered_client.patch(f"/api/transactions/{tx_id}", json={"description": "new"})
    assert r.status_code == 405


def test_delete_transfer_removes_both(registered_client):
    acc1 = _acc(registered_client, "A1")
    acc2 = _acc(registered_client, "A2")
    rows = registered_client.post("/api/transactions/transfer", json={
        "from_account_id": acc1["id"], "to_account_id": acc2["id"],
        "amount": "50.00", "date": "2026-04-01", "description": "x",
    }).json()
    tx_id = rows[0]["id"]
    peer_id = rows[0]["transfer_peer_id"]
    r = registered_client.delete(f"/api/transactions/{tx_id}")
    assert r.status_code == 204
    assert registered_client.get(f"/api/transactions/{peer_id}").status_code == 404


def test_list_transactions_month_filter(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client)
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"], date="2026-04-01")
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"], date="2026-03-15")
    r = registered_client.get("/api/transactions?year=2026&month=4")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_soll_ist(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client, "Lebensmittel", "variable")
    registered_client.post("/api/budgets", json={
        "category_id": cat["id"], "amount": "300.00", "valid_from": "2026-01-01",
    })
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="120.00", transaction_type="expense", date="2026-04-05")
    r = registered_client.get("/api/categories/soll-ist?year=2026&month=4")
    assert r.status_code == 200
    nodes = r.json()
    node = next(n for n in nodes if n["id"] == cat["id"])
    assert node["soll"] == "300.00"
    assert node["ist"] == "-120.00"


def test_balances(registered_client):
    acc = _acc(registered_client, "Main")
    cat = _cat(registered_client)
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="100.00", transaction_type="expense", date="2026-04-01")
    r = registered_client.get("/api/accounts/balances")
    assert r.status_code == 200
    balances = r.json()
    acc_bal = next(b for b in balances if b["id"] == acc["id"])
    assert acc_bal["balance"] == "-100.00"


def test_summary(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client)
    inc_cat = _cat(registered_client, "Salary", "income")
    _tx(registered_client, account_id=acc["id"], category_id=inc_cat["id"],
        amount="1000.00", transaction_type="income", date="2026-04-10")
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="200.00", transaction_type="expense", date="2026-04-15")
    r = registered_client.get("/api/transactions/summary?year=2026&month=4")
    assert r.status_code == 200
    body = r.json()
    assert body["income"] == "1000.00"
    assert body["expenses"] == "-200.00"
    assert body["balance"] == "800.00"
