from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, field_serializer


class RecurringTemplateCreate(BaseModel):
    name: str
    amount: Decimal
    category_id: int | None = None
    account_id: int | None = None
    interval: str  # monthly|quarterly|semi_annual|annual
    day_of_month: int = 1
    next_date: date
    show_as_monthly: bool = False


class RecurringTemplateUpdate(BaseModel):
    name: str | None = None
    amount: Decimal | None = None
    category_id: int | None = None
    account_id: int | None = None
    interval: str | None = None
    day_of_month: int | None = None
    next_date: date | None = None
    show_as_monthly: bool | None = None
    is_active: bool | None = None


class RecurringTemplateResponse(BaseModel):
    id: int
    household_id: int
    name: str
    amount: Decimal
    category_id: int | None
    account_id: int | None
    interval: str
    day_of_month: int
    next_date: date
    show_as_monthly: bool
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal) -> str:
        return f"{v:.2f}"
