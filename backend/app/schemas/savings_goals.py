from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, field_serializer


class SavingsGoalCreate(BaseModel):
    name: str
    target_amount: Decimal
    target_date: date | None = None
    account_id: int | None = None
    color: str | None = None
    notes: str | None = None


class SavingsGoalUpdate(BaseModel):
    name: str | None = None
    target_amount: Decimal | None = None
    target_date: date | None = None
    account_id: int | None = None
    color: str | None = None
    notes: str | None = None
    is_achieved: bool | None = None


class SavingsGoalResponse(BaseModel):
    id: int
    household_id: int
    name: str
    target_amount: Decimal
    target_date: date | None
    account_id: int | None
    color: str | None
    notes: str | None
    is_achieved: bool
    created_at: datetime
    current_amount: float = 0.0
    progress_pct: float = 0.0
    model_config = {"from_attributes": True}

    @field_serializer("target_amount")
    def serialize_target(self, v: Decimal) -> float:
        return float(v)
