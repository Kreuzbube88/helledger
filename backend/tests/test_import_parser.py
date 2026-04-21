import pytest
from decimal import Decimal
from datetime import date
from app.services.import_parser import parse_csv, apply_csv_mapping, parse_ofx


def test_parse_csv_detects_semicolon_columns():
    data = b"Buchungsdatum;Betrag;Verwendungszweck\n01.01.2026;-45,50;Rewe\n15.01.2026;2500,00;Gehalt\n"
    result = parse_csv(data)
    assert result.columns == ["Buchungsdatum", "Betrag", "Verwendungszweck"]
    assert result.suggested_mapping["date"] == "Buchungsdatum"
    assert result.suggested_mapping["amount"] == "Betrag"
    assert result.suggested_mapping["description"] == "Verwendungszweck"


def test_parse_csv_detects_comma_delimiter():
    data = b"Date,Amount,Desc\n2026-01-01,-45.50,Test\n"
    result = parse_csv(data)
    assert len(result.columns) == 3


def test_parse_csv_detects_date_format_german():
    data = b"Datum;Betrag;Memo\n01.01.2026;-45,50;Test\n15.01.2026;100,00;Income\n"
    result = parse_csv(data)
    assert result.detected_date_format == "%d.%m.%Y"


def test_parse_csv_detects_date_format_iso():
    data = b"Date;Amount;Desc\n2026-01-01;-45.50;Test\n2026-01-15;100.00;Income\n"
    result = parse_csv(data)
    assert result.detected_date_format == "%Y-%m-%d"


def test_parse_csv_detects_decimal_comma():
    data = b"Date;Amount;Desc\n2026-01-01;-45,50;Test\n"
    result = parse_csv(data)
    assert result.detected_decimal_separator == ","


def test_parse_csv_detects_decimal_dot():
    data = b"Date;Amount;Desc\n2026-01-01;-45.50;Test\n"
    result = parse_csv(data)
    assert result.detected_decimal_separator == "."


def test_parse_csv_preview_max_5_rows():
    rows = "\n".join(f"2026-01-{i:02d};{i}.00;Desc {i}" for i in range(1, 11))
    data = f"Date;Amount;Desc\n{rows}\n".encode()
    result = parse_csv(data)
    assert len(result.preview_rows) == 5


def test_parse_csv_raw_rows_excludes_header():
    data = b"Date;Amount;Desc\n2026-01-01;-45.50;Test\n2026-01-15;100.00;Income\n"
    result = parse_csv(data)
    assert len(result.raw_rows) == 2
    assert result.raw_rows[0][0] != "Date"


def test_parse_csv_empty_raises():
    data = b"Date;Amount;Desc\n"
    with pytest.raises(ValueError, match="Keine Datenzeilen"):
        parse_csv(data)


def test_apply_csv_mapping_basic():
    raw_rows = [["01.01.2026", "-45,50", "Rewe"], ["15.01.2026", "2500,00", "Gehalt"]]
    columns = ["Buchungsdatum", "Betrag", "Verwendungszweck"]
    field_map = {"date": "Buchungsdatum", "amount": "Betrag", "description": "Verwendungszweck"}
    rows, errors = apply_csv_mapping(raw_rows, columns, field_map, "%d.%m.%Y", ",")
    assert len(rows) == 2
    assert len(errors) == 0
    assert rows[0].date == date(2026, 1, 1)
    assert rows[0].amount == Decimal("-45.50")
    assert rows[0].description == "Rewe"
    assert rows[1].amount == Decimal("2500.00")


def test_apply_csv_mapping_dot_decimal():
    raw_rows = [["2026-01-01", "-45.50", "Test"]]
    columns = ["Date", "Amount", "Desc"]
    field_map = {"date": "Date", "amount": "Amount", "description": "Desc"}
    rows, errors = apply_csv_mapping(raw_rows, columns, field_map, "%Y-%m-%d", ".")
    assert rows[0].amount == Decimal("-45.50")


def test_apply_csv_mapping_bad_date_is_error():
    raw_rows = [["not-a-date", "-45.50", "Test"]]
    columns = ["Date", "Amount", "Desc"]
    field_map = {"date": "Date", "amount": "Amount", "description": "Desc"}
    rows, errors = apply_csv_mapping(raw_rows, columns, field_map, "%d.%m.%Y", ".")
    assert len(rows) == 0
    assert len(errors) == 1
    assert errors[0].row == 1


def test_apply_csv_mapping_bad_amount_is_error():
    raw_rows = [["01.01.2026", "N/A", "Test"]]
    columns = ["Date", "Amount", "Desc"]
    field_map = {"date": "Date", "amount": "Amount", "description": "Desc"}
    rows, errors = apply_csv_mapping(raw_rows, columns, field_map, "%d.%m.%Y", ".")
    assert len(rows) == 0
    assert len(errors) == 1


def test_apply_csv_mapping_zero_amount_is_error():
    raw_rows = [["01.01.2026", "0,00", "Test"]]
    columns = ["Date", "Amount", "Desc"]
    field_map = {"date": "Date", "amount": "Amount", "description": "Desc"}
    rows, errors = apply_csv_mapping(raw_rows, columns, field_map, "%d.%m.%Y", ",")
    assert len(rows) == 0
    assert errors[0].row == 1


def test_apply_csv_mapping_partial_errors_continue():
    raw_rows = [["01.01.2026", "N/A", "Bad"], ["15.01.2026", "100,00", "Good"]]
    columns = ["Date", "Amount", "Desc"]
    field_map = {"date": "Date", "amount": "Amount", "description": "Desc"}
    rows, errors = apply_csv_mapping(raw_rows, columns, field_map, "%d.%m.%Y", ",")
    assert len(rows) == 1
    assert rows[0].description == "Good"
    assert len(errors) == 1
    assert errors[0].row == 1


OFX_XML = b"""
<OFX>
<BANKMSGSRSV1><STMTTRNRS><STMTRS>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20260101
<TRNAMT>-45.50
<FITID>TXN001
<MEMO>Rewe Markt
</STMTTRN>
<STMTTRN>
<TRNTYPE>CREDIT
<DTPOSTED>20260115120000
<TRNAMT>2500.00
<FITID>TXN002
<NAME>Arbeitgeber GmbH
</STMTTRN>
</STMTRS></STMTTRNRS></BANKMSGSRSV1>
</OFX>
"""

OFX_SGML = b"""OFXHEADER:100
DATA:OFXSGML

<OFX>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20260101
<TRNAMT>-45.50
<FITID>SGML001
<MEMO>SGML Test
<STMTTRN>
<TRNTYPE>CREDIT
<DTPOSTED>20260201
<TRNAMT>1000.00
<FITID>SGML002
<MEMO>SGML Income
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""


def test_parse_ofx_xml_finds_transactions():
    result = parse_ofx(OFX_XML)
    assert len(result.transactions) == 2


def test_parse_ofx_xml_debit_fields():
    result = parse_ofx(OFX_XML)
    tx = result.transactions[0]
    assert tx.date == date(2026, 1, 1)
    assert tx.amount == Decimal("-45.50")
    assert tx.description == "Rewe Markt"
    assert tx.external_id == "TXN001"


def test_parse_ofx_xml_name_fallback():
    result = parse_ofx(OFX_XML)
    tx = result.transactions[1]
    assert tx.amount == Decimal("2500.00")
    assert tx.description == "Arbeitgeber GmbH"
    assert tx.external_id == "TXN002"


def test_parse_ofx_xml_datetime_truncated():
    result = parse_ofx(OFX_XML)
    assert result.transactions[1].date == date(2026, 1, 15)


def test_parse_ofx_sgml_finds_transactions():
    result = parse_ofx(OFX_SGML)
    assert len(result.transactions) == 2
    assert result.transactions[0].external_id == "SGML001"


def test_parse_ofx_preview_rows():
    result = parse_ofx(OFX_XML)
    assert len(result.preview_rows) == 2
    assert result.preview_rows[0] == ["2026-01-01", "-45.50", "Rewe Markt", "TXN001"]


def test_parse_ofx_no_transactions_raises():
    data = b"<OFX><BANKMSGSRSV1></BANKMSGSRSV1></OFX>"
    with pytest.raises(ValueError, match="Keine Transaktionen"):
        parse_ofx(data)


def test_parse_ofx_sgml_last_block_no_sentinel():
    data = b"""<OFX>
<BANKMSGSRSV1>
<STMTTRN>
<DTPOSTED>20260101
<TRNAMT>-10.00
<FITID>X1
<MEMO>Last Block
</BANKMSGSRSV1>
</OFX>
"""
    result = parse_ofx(data)
    assert len(result.transactions) == 1
    assert result.transactions[0].amount == Decimal("-10.00")
