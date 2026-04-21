from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, field_serializer


class ExpectedValueCreate(BaseModel):
    category_id: int
    amount: Decimal
    valid_from: date


class ExpectedValueUpdate(BaseModel):
    amount: Decimal | None = None
    valid_from: date | None = None
    valid_until: date | None = None


class ExpectedValueResponse(BaseModel):
    id: int
    household_id: int
    category_id: int
    amount: Decimal
    valid_from: date
    valid_until: date | None
    created_at: datetime
    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal) -> str:
        return f"{v:.2f}"
