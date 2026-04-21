import io
import openpyxl
import pytest


def _make_excel(rows: list[tuple]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["date", "description", "amount", "type"])
    for row in rows:
        ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_import_excel(registered_client):
    acc = registered_client.post(
        "/api/accounts",
        json={"name": "Test", "account_type": "checking", "starting_balance": 0, "currency": "EUR"},
    ).json()
    xlsx = _make_excel([("2025-01-15", "Salary", 3000.0, "income")])
    r = registered_client.post(
        "/api/import/excel",
        files={"file": ("test.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"account_id": str(acc["id"])},
    )
    assert r.status_code == 200
    assert r.json()["imported"] == 1
    assert r.json()["errors"] == 0


def test_export_excel(registered_client):
    r = registered_client.get("/api/export/excel?year=2025")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
    wb = openpyxl.load_workbook(io.BytesIO(r.content))
    assert wb.active is not None
