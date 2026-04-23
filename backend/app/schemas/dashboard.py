from pydantic import BaseModel


class YearCategoryRow(BaseModel):
    id: int
    name: str
    type: str
    color: str | None
    months: list[float]
    is_planned: list[bool]


class YearViewResponse(BaseModel):
    year: int
    categories: list[YearCategoryRow]
    monthly_income: list[float]
    monthly_expense: list[float]
    monthly_balance: list[float]
    planned_from: int
    savings_by_month: dict[str, float] = {}
    savings_planned_by_month: dict[str, float] = {}


class MonthCategoryRow(BaseModel):
    category_id: int
    name: str
    ist: float


class MonthSection(BaseModel):
    type: str
    rows: list[MonthCategoryRow]
    total_ist: float


class MonthSummary(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    savings_rate: float
    real_savings_rate: float
    savings_amount: float
    available: float
    debt_to_income: float
    emergency_months: float


class SavingsRow(BaseModel):
    description: str
    amount: float
    date: str


class MonthViewResponse(BaseModel):
    year: int
    month: int
    sections: list[MonthSection]
    summary: MonthSummary
    savings_rows: list[SavingsRow] = []
