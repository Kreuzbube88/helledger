from pydantic import BaseModel


class ParseResponse(BaseModel):
    session_token: str
    format: str
    columns: list[str]
    preview_rows: list[list[str]]
    suggested_mapping: dict[str, str | None]
    detected_date_format: str
    detected_decimal_separator: str


class ConfirmRequest(BaseModel):
    session_token: str
    account_id: int
    category_id: int | None = None
    field_map: dict[str, str]
    date_format: str
    decimal_separator: str


class DuplicateEntry(BaseModel):
    date: str
    amount: str
    description: str


class ErrorEntry(BaseModel):
    row: int
    reason: str


class ConfirmResponse(BaseModel):
    imported: int
    duplicates: list[DuplicateEntry]
    errors: list[ErrorEntry]
