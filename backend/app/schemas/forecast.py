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
    savings_transfers: float
    total_balance: float
    accounts: list[AccountForecastBalance]


class ForecastResponse(BaseModel):
    months: list[ForecastMonth]
