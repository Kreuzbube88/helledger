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


class MonthCategoryRow(BaseModel):
    category_id: int
    name: str
    soll: float
    ist: float
    diff: float
    pct: float


class MonthSection(BaseModel):
    type: str
    rows: list[MonthCategoryRow]
    total_soll: float
    total_ist: float


class MonthSummary(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    savings_rate: float


class MonthViewResponse(BaseModel):
    year: int
    month: int
    sections: list[MonthSection]
    summary: MonthSummary
