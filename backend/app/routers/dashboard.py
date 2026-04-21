from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.household import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.dashboard import YearCategoryRow, YearViewResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/year", response_model=YearViewResponse)
def get_year_view(
    year: int = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")

    cats = (
        db.query(Category)
        .filter(
            Category.household_id == user.active_household_id,
            Category.archived == False,
        )
        .all()
    )

    month_col = func.strftime("%m", Transaction.date)
    year_col = func.strftime("%Y", Transaction.date)

    rows = (
        db.query(
            Transaction.category_id,
            month_col,
            func.sum(func.abs(Transaction.amount)),
        )
        .filter(
            Transaction.household_id == user.active_household_id,
            year_col == str(year),
            Transaction.transaction_type.in_(["expense", "income"]),
        )
        .group_by(Transaction.category_id, month_col)
        .all()
    )

    agg: dict[int, dict[int, float]] = {}
    for cat_id, month_str, total in rows:
        if cat_id is not None:
            agg.setdefault(cat_id, {})[int(month_str)] = float(total or 0)

    monthly_income = [0.0] * 12
    monthly_expense = [0.0] * 12

    inc_rows = (
        db.query(month_col, func.sum(Transaction.amount))
        .filter(
            Transaction.household_id == user.active_household_id,
            year_col == str(year),
            Transaction.transaction_type == "income",
        )
        .group_by(month_col)
        .all()
    )
    for month_str, total in inc_rows:
        monthly_income[int(month_str) - 1] = float(total or 0)

    exp_rows = (
        db.query(month_col, func.sum(func.abs(Transaction.amount)))
        .filter(
            Transaction.household_id == user.active_household_id,
            year_col == str(year),
            Transaction.transaction_type == "expense",
        )
        .group_by(month_col)
        .all()
    )
    for month_str, total in exp_rows:
        monthly_expense[int(month_str) - 1] = float(total or 0)

    monthly_balance = [monthly_income[i] - monthly_expense[i] for i in range(12)]

    category_rows = [
        YearCategoryRow(
            id=cat.id,
            name=cat.name,
            type=cat.category_type,
            color=cat.color,
            months=[float(agg.get(cat.id, {}).get(m, 0)) for m in range(1, 13)],
        )
        for cat in cats
    ]

    return YearViewResponse(
        year=year,
        categories=category_rows,
        monthly_income=monthly_income,
        monthly_expense=monthly_expense,
        monthly_balance=monthly_balance,
    )
