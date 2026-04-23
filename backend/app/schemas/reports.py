from pydantic import BaseModel


class ExpensesByCategoryItem(BaseModel):
    category_id: int | None
    category_name: str
    total: str


class MonthlyTrendItem(BaseModel):
    year: int
    month: int
    income: str
    expenses: str
    savings: str


class BalanceHistoryItem(BaseModel):
    date: str
    balance: str
