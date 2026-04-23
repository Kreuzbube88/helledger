from datetime import date as Date, datetime
from decimal import Decimal
from pydantic import BaseModel, field_serializer, model_validator


class TransactionCreate(BaseModel):
    account_id: int
    category_id: int | None = None
    amount: Decimal
    date: Date
    description: str
    transaction_type: str

    @model_validator(mode="after")
    def validate_category(self) -> "TransactionCreate":
        if self.transaction_type in ("income", "expense") and self.category_id is None:
            raise ValueError("category_id required for income and expense transactions")
        return self


class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal
    date: Date
    description: str


class TransactionUpdate(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    amount: Decimal | None = None
    date: Date | None = None
    description: str | None = None
    transaction_type: str | None = None


class TransactionResponse(BaseModel):
    id: int
    household_id: int
    account_id: int
    category_id: int | None
    amount: Decimal
    date: Date
    description: str
    transaction_type: str
    transfer_peer_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal) -> str:
        return f"{v:.2f}"


class SummaryResponse(BaseModel):
    income: str
    expenses: str
    balance: str


class BalanceResponse(BaseModel):
    id: int
    name: str
    account_type: str
    balance: str
    currency: str
    archived: bool


