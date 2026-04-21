import io
import pytest


CSV_BYTES = b"Buchungsdatum;Betrag;Verwendungszweck\n01.01.2026;-45,50;Rewe\n15.01.2026;2500,00;Gehalt\n"

OFX_BYTES = b"""<OFX>
<BANKMSGSRSV1><STMTTRNRS><STMTRS>
<STMTTRN>
<DTPOSTED>20260101
<TRNAMT>-45.50
<FITID>TXN001
<MEMO>Rewe
</STMTTRN>
</STMTRS></STMTTRNRS></BANKMSGSRSV1>
</OFX>"""


def _account_id(registered_client) -> int:
    return registered_client.post("/api/accounts", json={
        "name": "Girokonto", "account_type": "checking",
        "starting_balance": "0.00", "currency": "EUR",
    }).json()["id"]


def _parse_csv(registered_client, account_id, content=CSV_BYTES):
    return registered_client.post(
        "/api/import/parse",
        data={"account_id": account_id},
        files={"file": ("bank.csv", io.BytesIO(content), "text/csv")},
    )


def test_parse_csv_returns_columns(registered_client):
    acc_id = _account_id(registered_client)
    r = _parse_csv(registered_client, acc_id)
    assert r.status_code == 200
    body = r.json()
    assert body["format"] == "csv"
    assert "Buchungsdatum" in body["columns"]
    assert "session_token" in body
    assert len(body["preview_rows"]) == 2
    assert body["suggested_mapping"]["date"] == "Buchungsdatum"


def test_parse_ofx_returns_fixed_columns(registered_client):
    acc_id = _account_id(registered_client)
    r = registered_client.post(
        "/api/import/parse",
        data={"account_id": acc_id},
        files={"file": ("bank.ofx", io.BytesIO(OFX_BYTES), "application/x-ofx")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["format"] == "ofx"
    assert body["suggested_mapping"]["date"] == "date"
    assert len(body["preview_rows"]) == 1


def test_parse_unsupported_extension_returns_400(registered_client):
    acc_id = _account_id(registered_client)
    r = registered_client.post(
        "/api/import/parse",
        data={"account_id": acc_id},
        files={"file": ("bank.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert r.status_code == 400


def test_parse_unauthenticated_returns_401(client):
    r = client.post(
        "/api/import/parse",
        data={"account_id": 1},
        files={"file": ("bank.csv", io.BytesIO(CSV_BYTES), "text/csv")},
    )
    assert r.status_code == 403


def _confirm(registered_client, account_id, parsed):
    return registered_client.post("/api/import/confirm", json={
        "session_token": parsed["session_token"],
        "account_id": account_id,
        "category_id": None,
        "field_map": parsed["suggested_mapping"],
        "date_format": parsed["detected_date_format"],
        "decimal_separator": parsed["detected_decimal_separator"],
    })


def test_confirm_csv_imports_rows(registered_client):
    acc_id = _account_id(registered_client)
    parsed = _parse_csv(registered_client, acc_id).json()
    r = _confirm(registered_client, acc_id, parsed)
    assert r.status_code == 200
    body = r.json()
    assert body["imported"] == 2
    assert body["duplicates"] == []
    assert body["errors"] == []


def test_confirm_csv_detects_duplicates(registered_client):
    acc_id = _account_id(registered_client)
    parsed1 = _parse_csv(registered_client, acc_id).json()
    _confirm(registered_client, acc_id, parsed1)
    parsed2 = _parse_csv(registered_client, acc_id).json()
    r = _confirm(registered_client, acc_id, parsed2)
    assert r.status_code == 200
    body = r.json()
    assert body["imported"] == 0
    assert len(body["duplicates"]) == 2


def test_confirm_expired_session_returns_400(registered_client):
    acc_id = _account_id(registered_client)
    r = registered_client.post("/api/import/confirm", json={
        "session_token": "00000000-0000-0000-0000-000000000000",
        "account_id": acc_id,
        "category_id": None,
        "field_map": {"date": "x", "amount": "y", "description": "z"},
        "date_format": "%d.%m.%Y",
        "decimal_separator": ",",
    })
    assert r.status_code == 400
    assert r.json()["detail"] == "session_expired"


def test_confirm_ofx_imports_row(registered_client):
    import io
    acc_id = _account_id(registered_client)
    r_parse = registered_client.post(
        "/api/import/parse",
        data={"account_id": acc_id},
        files={"file": ("bank.ofx", io.BytesIO(OFX_BYTES), "application/x-ofx")},
    )
    parsed = r_parse.json()
    r = _confirm(registered_client, acc_id, parsed)
    assert r.status_code == 200
    assert r.json()["imported"] == 1


def test_confirm_wrong_account_returns_403(registered_client, second_user_client):
    acc_id = _account_id(registered_client)
    parsed = _parse_csv(registered_client, acc_id).json()
    r = second_user_client.post("/api/import/confirm", json={
        "session_token": parsed["session_token"],
        "account_id": acc_id,
        "category_id": None,
        "field_map": parsed["suggested_mapping"],
        "date_format": parsed["detected_date_format"],
        "decimal_separator": parsed["detected_decimal_separator"],
    })
    assert r.status_code == 403
