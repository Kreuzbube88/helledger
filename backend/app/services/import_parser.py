import csv
import io
import re
from dataclasses import dataclass
from datetime import date as Date, datetime
from decimal import Decimal, InvalidOperation

DATE_FORMATS = ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%y"]

_KEYWORDS: dict[str, list[str]] = {
    "date": ["datum", "date", "buchungsdatum", "buchung", "wertstellung", "valuta"],
    "amount": ["betrag", "amount", "umsatz", "wert", "summe"],
    "description": ["verwendungszweck", "beschreibung", "description", "memo", "text", "buchungstext"],
}


@dataclass
class ParsedRow:
    date: Date
    amount: Decimal
    description: str
    external_id: str | None = None


@dataclass
class ParseError:
    row: int
    reason: str


@dataclass
class OfxParseResult:
    transactions: list[ParsedRow]
    preview_rows: list[list[str]]


@dataclass
class CsvParseResult:
    columns: list[str]
    raw_rows: list[list[str]]
    preview_rows: list[list[str]]
    suggested_mapping: dict[str, str | None]
    detected_date_format: str
    detected_decimal_separator: str


def _detect_encoding(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            data.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"  # latin-1 decodes all bytes, so this is never reached


def _try_parse_date(s: str, fmt: str) -> Date | None:
    try:
        return datetime.strptime(s.strip(), fmt).date()
    except ValueError:
        return None


def _detect_date_format(samples: list[str]) -> str:
    for fmt in DATE_FORMATS:
        hits = sum(1 for s in samples if _try_parse_date(s.strip(), fmt) is not None)
        if hits / max(len(samples), 1) >= 0.8:
            return fmt
    return "%d.%m.%Y"


def _detect_decimal_sep(samples: list[str]) -> str:
    for s in samples:
        if "," in s.strip():
            return ","
    return "."


def _suggest_mapping(columns: list[str]) -> dict[str, str | None]:
    result: dict[str, str | None] = {"date": None, "amount": None, "description": None}
    for col in columns:
        col_lower = col.lower()
        for field_name, keywords in _KEYWORDS.items():
            if result[field_name] is None:
                for kw in keywords:
                    if kw in col_lower:
                        result[field_name] = col
                        break
    return result


def parse_csv(data: bytes) -> CsvParseResult:
    enc = _detect_encoding(data)
    text = data.decode(enc)
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        class _FallbackDialect(csv.excel):
            delimiter = ";"
        dialect = _FallbackDialect

    reader = csv.reader(io.StringIO(text), dialect)
    all_rows = list(reader)

    if len(all_rows) < 2:
        raise ValueError("Keine Datenzeilen gefunden")

    columns = all_rows[0]
    data_rows = [r for r in all_rows[1:] if any(cell.strip() for cell in r)]

    if not data_rows:
        raise ValueError("Keine Datenzeilen gefunden")

    suggested = _suggest_mapping(columns)

    date_col_idx = columns.index(suggested["date"]) if suggested["date"] else None
    date_samples = [
        r[date_col_idx]
        for r in data_rows[:20]
        if date_col_idx is not None and date_col_idx < len(r) and r[date_col_idx].strip()
    ]
    detected_fmt = _detect_date_format(date_samples) if date_samples else "%d.%m.%Y"

    amount_col_idx = columns.index(suggested["amount"]) if suggested["amount"] else None
    amount_samples = [
        r[amount_col_idx]
        for r in data_rows[:20]
        if amount_col_idx is not None and amount_col_idx < len(r) and r[amount_col_idx].strip()
    ]
    detected_dec = _detect_decimal_sep(amount_samples) if amount_samples else ","

    return CsvParseResult(
        columns=columns,
        raw_rows=data_rows,
        preview_rows=data_rows[:5],
        suggested_mapping=suggested,
        detected_date_format=detected_fmt,
        detected_decimal_separator=detected_dec,
    )


def apply_csv_mapping(
    raw_rows: list[list[str]],
    columns: list[str],
    field_map: dict[str, str],
    date_format: str,
    decimal_separator: str,
) -> tuple[list[ParsedRow], list[ParseError]]:
    try:
        date_idx = columns.index(field_map["date"])
        amount_idx = columns.index(field_map["amount"])
        desc_idx = columns.index(field_map["description"])
    except (KeyError, ValueError) as e:
        raise ValueError(f"Ungültige Spalten-Konfiguration: {e}") from e

    rows: list[ParsedRow] = []
    errors: list[ParseError] = []

    for i, row in enumerate(raw_rows, start=1):
        try:
            raw_date = row[date_idx].strip()
            parsed_date = _try_parse_date(raw_date, date_format)
            if parsed_date is None:
                errors.append(ParseError(row=i, reason=f"Ungültiges Datum: '{raw_date}'"))
                continue

            raw_amount = row[amount_idx].strip()
            if decimal_separator == ",":
                raw_amount = raw_amount.replace(".", "").replace(",", ".")
            raw_amount = raw_amount.replace("\xa0", "").replace(" ", "")
            try:
                amount = Decimal(raw_amount)
            except InvalidOperation:
                errors.append(ParseError(row=i, reason=f"Ungültiger Betrag: '{row[amount_idx].strip()}'"))
                continue

            if amount == Decimal("0"):
                errors.append(ParseError(row=i, reason="Betrag ist 0"))
                continue

            description = row[desc_idx].strip()[:255]
            rows.append(ParsedRow(date=parsed_date, amount=amount, description=description))

        except IndexError:
            errors.append(ParseError(row=i, reason="Zeile hat zu wenige Spalten"))

    return rows, errors


def _ofx_field(block: str, tag: str) -> str | None:
    m = re.search(rf"<{tag}>(.*?)(?:<|$)", block, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else None


def _parse_ofx_date(raw: str) -> Date:
    return datetime.strptime(raw[:8], "%Y%m%d").date()


def parse_ofx(data: bytes) -> OfxParseResult:
    enc = _detect_encoding(data)
    text = data.decode(enc)

    # XML-style with closing tags
    blocks = re.findall(r"<STMTTRN>(.*?)</STMTTRN>", text, re.IGNORECASE | re.DOTALL)
    if not blocks:
        # SGML-style: no closing tags
        blocks = re.findall(
            r"<STMTTRN>(.*?)(?=<STMTTRN>|</STMTTRNRS>|</OFX>|$)",
            text, re.IGNORECASE | re.DOTALL,
        )

    if not blocks:
        raise ValueError("Keine Transaktionen gefunden")

    transactions: list[ParsedRow] = []
    for block in blocks:
        dtposted = _ofx_field(block, "DTPOSTED")
        trnamt = _ofx_field(block, "TRNAMT")
        memo = _ofx_field(block, "MEMO")
        name = _ofx_field(block, "NAME")
        fitid = _ofx_field(block, "FITID")

        if not dtposted or not trnamt:
            continue
        try:
            parsed_date = _parse_ofx_date(dtposted)
            amount = Decimal(trnamt)
        except (ValueError, InvalidOperation):
            continue

        description = (memo or name or "").strip()[:255]
        transactions.append(ParsedRow(
            date=parsed_date,
            amount=amount,
            description=description,
            external_id=fitid,
        ))

    if not transactions:
        raise ValueError("Keine Transaktionen gefunden")

    preview_rows = [
        [str(tx.date), str(tx.amount), tx.description, tx.external_id or ""]
        for tx in transactions[:5]
    ]
    return OfxParseResult(transactions=transactions, preview_rows=preview_rows)
