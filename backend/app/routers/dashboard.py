from datetime import date as date_type

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.household import Category, Account
from app.models.loan import Loan, LoanExtraPayment
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
from app.services.loan_calc import calc_stats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/year", response_model=YearViewResponse)
def get_year_view(
    year: int = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")

    hh_id = user.active_household_id
    today = date_type.today()
    current_month = today.month if year == today.year else (12 if year < today.year else 0)
    planned_from = current_month + 1 if year == today.year else (1 if year > today.year else 13)

    cats = (
        db.query(Category)
        .filter(
            Category.household_id == hh_id,
            Category.archived.is_(False),
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
            Transaction.household_id == hh_id,
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

    # Build EV map and template-soll map for future months
    cat_ids = [c.id for c in cats]
    # TODO Phase 2: replace with FixedCost-based soll map
    template_soll: dict[int, float] = {}

    monthly_income = [0.0] * 12
    monthly_expense = [0.0] * 12

    inc_rows = (
        db.query(month_col, func.sum(Transaction.amount))
        .filter(
            Transaction.household_id == hh_id,
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
            Transaction.household_id == hh_id,
            year_col == str(year),
            Transaction.transaction_type == "expense",
        )
        .group_by(month_col)
        .all()
    )
    for month_str, total in exp_rows:
        monthly_expense[int(month_str) - 1] = float(total or 0)

    monthly_balance = [monthly_income[i] - monthly_expense[i] for i in range(12)]

    # TODO Phase 2: replace with FixedCost-based soll lookup
    def _ev_for(cat_id: int, first_of_month: date_type):
        return None

    category_rows = []
    for cat in cats:
        months_vals = []
        is_planned_flags = []
        for m in range(1, 13):
            is_future = m >= planned_from
            if not is_future:
                val = float(agg.get(cat.id, {}).get(m, 0))
                months_vals.append(val)
                is_planned_flags.append(False)
            else:
                first_of_month = date_type(year, m, 1)
                ev = _ev_for(cat.id, first_of_month)
                soll = float(ev.amount) if ev else template_soll.get(cat.id, 0.0)
                months_vals.append(soll)
                is_planned_flags.append(True)
        category_rows.append(YearCategoryRow(
            id=cat.id,
            name=cat.name,
            type=cat.category_type,
            color=cat.color,
            months=months_vals,
            is_planned=is_planned_flags,
        ))

    return YearViewResponse(
        year=year,
        categories=category_rows,
        monthly_income=monthly_income,
        monthly_expense=monthly_expense,
        monthly_balance=monthly_balance,
        planned_from=planned_from,
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
        Category.archived.is_(False),
    ).all()

    first_day = date_type(year, month, 1)
    # TODO Phase 2: replace with FixedCost-based soll maps
    ev_map: dict[int, float] = {}
    template_soll: dict[int, float] = {}

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
            soll = ev_map.get(cat.id) or template_soll.get(cat.id, 0.0)
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

    # debt_to_income: total active loan balances / monthly income * 100
    active_loans = db.query(Loan).filter(
        Loan.household_id == hh_id,
        Loan.status == "active",
    ).all()
    loan_ids = [l.id for l in active_loans]
    eps_map: dict[int, list[dict]] = {}
    if loan_ids:
        for ep in db.query(LoanExtraPayment).filter(LoanExtraPayment.loan_id.in_(loan_ids)).all():
            eps_map.setdefault(ep.loan_id, []).append(
                {"payment_date": ep.payment_date, "amount": float(ep.amount), "effect": ep.effect}
            )
    total_debt = 0.0
    for loan in active_loans:
        monthly_extra = float(loan.monthly_extra) if loan.monthly_extra else 0.0
        stats = calc_stats(
            float(loan.principal), float(loan.interest_rate),
            float(loan.monthly_payment), loan.term_months,
            loan.start_date, eps_map.get(loan.id, []), monthly_extra,
        )
        total_debt += stats["current_balance"]
    debt_to_income = (total_debt / total_income * 100) if total_income > 0 else 0.0

    # emergency_months: liquid account balances / avg monthly expenses (last 3 months)
    liquid_accounts = db.query(Account).filter(
        Account.household_id == hh_id,
        Account.account_type.in_(["checking", "savings"]),
        Account.archived.is_(False),
    ).all()
    liquid_ids = [a.id for a in liquid_accounts]
    liquid_balance = sum(float(a.starting_balance) for a in liquid_accounts)
    if liquid_ids:
        tx_sum = db.query(func.sum(Transaction.amount)).filter(
            Transaction.household_id == hh_id,
            Transaction.account_id.in_(liquid_ids),
        ).scalar() or 0.0
        liquid_balance += float(tx_sum)

    # avg expense over 3 months prior to selected month
    from datetime import date as _date
    months_back = []
    y, m = year, month
    for _ in range(3):
        m -= 1
        if m < 1:
            m = 12; y -= 1
        months_back.append((str(y), f"{m:02d}"))

    monthly_expenses = []
    for y_str, m_str in months_back:
        exp = db.query(func.sum(func.abs(Transaction.amount))).filter(
            Transaction.household_id == hh_id,
            func.strftime("%Y", Transaction.date) == y_str,
            func.strftime("%m", Transaction.date) == m_str,
            Transaction.transaction_type == "expense",
        ).scalar() or 0.0
        monthly_expenses.append(float(exp))
    avg_expense = sum(monthly_expenses) / len(monthly_expenses) if monthly_expenses else 0.0
    emergency_months = max(0.0, liquid_balance / avg_expense) if avg_expense > 0 else 0.0

    return MonthViewResponse(
        year=year,
        month=month,
        sections=sections,
        summary=MonthSummary(
            total_income=total_income,
            total_expense=total_expense,
            balance=balance,
            savings_rate=savings_rate,
            debt_to_income=debt_to_income,
            emergency_months=emergency_months,
        ),
    )
