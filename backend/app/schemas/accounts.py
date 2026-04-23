from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_serializer


class AccountCreate(BaseModel):
    name: str
    account_type: str
    starting_balance: Decimal
    currency: str = "EUR"
    account_role: str | None = None


class AccountUpdate(BaseModel):
    name: str | None = None
    account_type: str | None = None
    starting_balance: Decimal | None = None
    currency: str | None = None
    account_role: str | None = None


class AccountResponse(BaseModel):
    id: int
    household_id: int
    name: str
    account_type: str
    starting_balance: Decimal
    currency: str
    account_role: str | None
    archived: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

    @field_serializer("starting_balance")
    def serialize_balance(self, v: Decimal) -> str:
        return f"{v:.2f}"
