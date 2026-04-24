from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator, model_validator


class FixedCostCreate(BaseModel):
    name: str
    amount: Decimal
    cost_type: str  # "expense" | "income" | "transfer" | "distribution"
    category_id: int | None = None
    account_id: int | None = None
    to_account_id: int | None = None
    interval_months: int = 1
    show_split: bool = False
    start_date: date
    end_date: date | None = None
    next_date: date | None = None

    @field_validator("interval_months")
    @classmethod
    def interval_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("interval_months must be >= 1")
        return v

    @model_validator(mode='after')
    def validate_transfer(self) -> 'FixedCostCreate':
        if self.cost_type in ('transfer', 'distribution'):
            if not self.to_account_id:
                raise ValueError('to_account_id required for transfer and distribution types')
            self.interval_months = 1
        return self


class FixedCostUpdate(BaseModel):
    name: str | None = None
    amount: Decimal | None = None
    cost_type: str | None = None
    category_id: int | None = None
    account_id: int | None = None
    to_account_id: int | None = None
    interval_months: int | None = None
    show_split: bool | None = None
    start_date: date | None = None
    end_date: date | None = None
    next_date: date | None = None

    @field_validator("interval_months")
    @classmethod
    def interval_must_be_positive(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("interval_months must be >= 1")
        return v

    @model_validator(mode='after')
    def validate_transfer(self) -> 'FixedCostUpdate':
        if self.cost_type in ('transfer', 'distribution') and self.to_account_id is None:
            raise ValueError('to_account_id required for transfer and distribution types')
        return self


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
    to_account_id: int | None
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
