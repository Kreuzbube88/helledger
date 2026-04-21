from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.household import Category, ExpectedValue
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.dashboard import (
    MonthCategoryRow,
    MonthSection,
    MonthSummary,
    MonthViewResponse,
    YearCategoryRow,
    YearViewResponse,
)

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


@router.get("/month", response_model=MonthViewResponse)
def get_month_view(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")

    hh_id = user.active_household_id
    year_str = str(year)
    month_str = f"{month:02d}"

    cats = db.query(Category).filter(
        Category.household_id == hh_id,
        Category.archived == False,
    ).all()

    evs = db.query(ExpectedValue).filter(
        ExpectedValue.household_id == hh_id,
    ).all()
    ev_map = {ev.category_id: float(ev.amount) for ev in evs}

    tx_rows = (
        db.query(Transaction.category_id, func.sum(func.abs(Transaction.amount)))
        .filter(
            Transaction.household_id == hh_id,
            func.strftime("%Y", Transaction.date) == year_str,
            func.strftime("%m", Transaction.date) == month_str,
        )
        .group_by(Transaction.category_id)
        .all()
    )
    tx_map = {cat_id: float(total or 0) for cat_id, total in tx_rows}

    sections = []
    for section_type in ["income", "fixed", "variable"]:
        section_cats = [c for c in cats if c.category_type == section_type]
        rows = []
        for cat in section_cats:
            soll = ev_map.get(cat.id, 0.0)
            ist = tx_map.get(cat.id, 0.0)
            diff = ist - soll
            pct = (ist / soll * 100) if soll > 0 else 0.0
            rows.append(MonthCategoryRow(
                category_id=cat.id,
                name=cat.name,
                soll=soll,
                ist=ist,
                diff=diff,
                pct=pct,
            ))
        sections.append(MonthSection(
            type=section_type,
            rows=rows,
            total_soll=sum(r.soll for r in rows),
            total_ist=sum(r.ist for r in rows),
        ))

    total_income = sum(r.ist for r in sections[0].rows) if sections else 0.0
    total_expense = (
        sum(r.ist for r in sections[1].rows) + sum(r.ist for r in sections[2].rows)
        if len(sections) > 1
        else 0.0
    )
    balance = total_income - total_expense
    savings_rate = (balance / total_income * 100) if total_income > 0 else 0.0

    return MonthViewResponse(
        year=year,
        month=month,
        sections=sections,
        summary=MonthSummary(
            total_income=total_income,
            total_expense=total_expense,
            balance=balance,
            savings_rate=savings_rate,
        ),
    )
