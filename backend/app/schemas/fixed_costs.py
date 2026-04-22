from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


class FixedCostCreate(BaseModel):
    name: str
    amount: Decimal
    cost_type: str  # "expense" | "income"
    category_id: int | None = None
    account_id: int | None = None
    interval_months: int = 1
    show_split: bool = False
    start_date: date
    end_date: date | None = None
    next_date: date


class FixedCostUpdate(BaseModel):
    name: str | None = None
    category_id: int | None = None
    account_id: int | None = None
    interval_months: int | None = None
    show_split: bool | None = None
    start_date: date | None = None
    end_date: date | None = None
    next_date: date | None = None


class FixedCostAmountChange(BaseModel):
    new_amount: Decimal
    valid_from: date


class FixedCostResponse(BaseModel):
    id: int
    household_id: int
    name: str
    amount: Decimal
    cost_type: str
    category_id: int | None
    account_id: int | None
    interval_months: int
    show_split: bool
    start_date: date
    end_date: date | None
    next_date: date
    loan_id: int | None
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class ReserveItem(BaseModel):
    id: int
    name: str
    full_amount: float
    interval_months: int
    monthly_share: float
    next_billing: str


class ReserveResponse(BaseModel):
    total_monthly: float
    items: list[ReserveItem]
