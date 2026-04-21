from pydantic import BaseModel


class YearCategoryRow(BaseModel):
    id: int
    name: str
    type: str
    color: str | None
    months: list[float]


class YearViewResponse(BaseModel):
    year: int
    categories: list[YearCategoryRow]
    monthly_income: list[float]
    monthly_expense: list[float]
    monthly_balance: list[float]
