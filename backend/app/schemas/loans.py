from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, model_validator, field_serializer


class LoanCreate(BaseModel):
    name: str
    loan_type: Literal["consumer", "mortgage"]
    lender: str | None = None
    # 3-of-4: exactly one may be None
    principal: Decimal | None = None
    interest_rate: Decimal | None = None
    monthly_payment: Decimal | None = None
    term_months: int | None = None
    start_date: date
    is_existing: bool = False
    monthly_extra: Decimal | None = None
    include_in_net_worth: bool = True
    # Mortgage-only
    purchase_price: Decimal | None = None
    equity: Decimal | None = None
    property_value: Decimal | None = None
    fixed_rate_until: date | None = None
    land_charge: Decimal | None = None

    @model_validator(mode="after")
    def check_3_of_4(self):
        fields = [self.principal, self.interest_rate, self.monthly_payment, self.term_months]
        none_count = sum(1 for f in fields if f is None)
        if none_count != 1:
            raise ValueError("exactly 3 of 4 fields (principal, interest_rate, monthly_payment, term_months) required")
        return self


class LoanUpdate(BaseModel):
    name: str | None = None
    lender: str | None = None
    monthly_extra: Decimal | None = None
    include_in_net_worth: bool | None = None
    property_value: Decimal | None = None
    fixed_rate_until: date | None = None
    land_charge: Decimal | None = None


class LoanResponse(BaseModel):
    id: int
    household_id: int
    name: str
    loan_type: str
    lender: str | None
    principal: Decimal
    interest_rate: Decimal
    monthly_payment: Decimal
    term_months: int
    start_date: date
    is_existing: bool
    monthly_extra: Decimal | None
    status: str
    paid_off_date: date | None
    category_id: int | None
    include_in_net_worth: bool
    current_balance: float
    payoff_date: str | None
    # Mortgage
    purchase_price: Decimal | None
    equity: Decimal | None
    property_value: Decimal | None
    fixed_rate_until: date | None
    land_charge: Decimal | None
    ltv: float | None
    fixed_rate_expiring_soon: bool
    model_config = {"from_attributes": True}

    @field_serializer("principal", "interest_rate", "monthly_payment")
    def serialize_decimal(self, v: Decimal) -> str:
        return f"{v:.4f}" if v is not None else None

    @field_serializer("monthly_extra", "purchase_price", "equity", "property_value", "land_charge")
    def serialize_optional_decimal(self, v: Decimal | None) -> str | None:
        return f"{v:.2f}" if v is not None else None


class ExtraPaymentCreate(BaseModel):
    payment_date: date
    amount: Decimal
    effect: Literal["shorten_term", "reduce_payment"]
    notes: str | None = None


class ExtraPaymentResponse(BaseModel):
    id: int
    loan_id: int
    payment_date: date
    amount: Decimal
    effect: str
    notes: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal) -> str:
        return f"{v:.2f}"


class LoanStatsResponse(BaseModel):
    total_interest: float
    total_paid: float
    interest_saved: float
    months_saved: int
    payoff_date: str | None
    current_balance: float
    total_months: int


class LoanNetWorthSummary(BaseModel):
    total_liability: float
    loans: list[dict]
