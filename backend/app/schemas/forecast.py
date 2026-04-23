from pydantic import BaseModel


class AccountForecastBalance(BaseModel):
    account_id: int
    account_name: str
    account_role: str | None
    balance: float


class ForecastMonth(BaseModel):
    month: str
    income: float
    fixed_expenses: float
    variable_expenses: float
    total_expenses: float
    savings: float
    savings_total: float
    accounts: list[AccountForecastBalance]


class ForecastResponse(BaseModel):
    months: list[ForecastMonth]
