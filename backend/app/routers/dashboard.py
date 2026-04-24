import calendar as _calendar
from datetime import date as date_type

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.fixed_cost import FixedCost
from app.models.household import Category, Account
from app.models.loan import Loan
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.dashboard import (
    DistributionRow,
    MonthCategoryRow,
    MonthSection,
    MonthSummary,
    MonthViewResponse,
    SavingsRow,
    YearCategoryRow,
    YearViewResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _fc_active_in_month(fc, year: int, month: int) -> bool:
    first = date_type(year, month, 1)
    last_day = _calendar.monthrange(year, month)[1]
    last = date_type(year, month, last_day)
    if fc.start_date > last:
        return False
    if fc.end_date is not None and fc.end_date < first:
        return False
    return True


def _fc_bills_in_month(fc, year: int, month: int) -> bool:
    months_diff = (year - fc.start_date.year) * 12 + (month - fc.start_date.month)
    return months_diff >= 0 and months_diff % fc.interval_months == 0


def _fc_planned_amount(active_fcs: list, cat_id: int, year: int, month: int) -> float:
    total = 0.0
    for fc in active_fcs:
        if fc.category_id != cat_id:
            continue
        if not _fc_active_in_month(fc, year, month):
            continue
        if fc.show_split:
            total += float(fc.amount) / fc.interval_months
        elif _fc_bills_in_month(fc, year, month):
            total += float(fc.amount)
    return total


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

    # Build FixedCost projection for future months
    year_start = date_type(year, 1, 1)
    year_end = date_type(year, 12, 31)
    active_fcs = (
        db.query(FixedCost)
        .filter(
            FixedCost.household_id == hh_id,
            FixedCost.is_active.is_(True),
            FixedCost.start_date <= year_end,
            or_(FixedCost.end_date.is_(None), FixedCost.end_date >= year_start),
        )
        .all()
    )

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
                soll = _fc_planned_amount(active_fcs, cat.id, year, m)
                if soll == 0.0:
                    past_vals = [float(agg.get(cat.id, {}).get(pm, 0)) for pm in range(1, planned_from)]
                    nonzero = [v for v in past_vals if v > 0]
                    soll = sum(nonzero) / len(nonzero) if nonzero else 0.0
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

    savings_acc_ids_y = [
        a.id for a in db.query(Account).filter(
            Account.household_id == hh_id,
            Account.account_role == "savings",
            Account.archived.is_(False),
        ).all()
    ]
    savings_by_month: dict[str, float] = {}
    if savings_acc_ids_y:
        s_rows = (
            db.query(month_col, func.sum(Transaction.amount))
            .filter(
                Transaction.household_id == hh_id,
                year_col == str(year),
                Transaction.account_id.in_(savings_acc_ids_y),
                Transaction.transaction_type == "transfer",
                Transaction.amount > 0,
            )
            .group_by(month_col)
            .all()
        )
        savings_by_month = {m: float(v) for m, v in s_rows}

    savings_planned_by_month: dict[str, float] = {}
    transfer_fcs = [
        fc for fc in active_fcs
        if fc.cost_type == "transfer"
        and fc.to_account_id is not None
        and fc.to_account_id in savings_acc_ids_y
    ]
    for m in range(1, 13):
        month_key = f"{m:02d}"
        if month_key in savings_by_month:
            continue  # already have actual data
        total = sum(
            float(fc.amount)
            for fc in transfer_fcs
            if _fc_active_in_month(fc, year, m) and _fc_bills_in_month(fc, year, m)
        )
        if total > 0:
            savings_planned_by_month[month_key] = total


    return YearViewResponse(
        year=year,
        categories=category_rows,
        monthly_income=monthly_income,
        monthly_expense=monthly_expense,
        monthly_balance=monthly_balance,
        planned_from=planned_from,
        savings_by_month=savings_by_month,
        savings_planned_by_month=savings_planned_by_month,
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

    today = date_type.today()
    is_future_month = date_type(year, month, 1) > today.replace(day=1)

    cats = db.query(Category).filter(
        Category.household_id == hh_id,
        Category.archived.is_(False),
    ).all()

    if is_future_month:
        month_start = date_type(year, month, 1)
        month_end = date_type(year, month, _calendar.monthrange(year, month)[1])
        active_fcs = db.query(FixedCost).filter(
            FixedCost.household_id == hh_id,
            FixedCost.is_active.is_(True),
            FixedCost.start_date <= month_end,
            or_(FixedCost.end_date.is_(None), FixedCost.end_date >= month_start),
        ).all()

        sections = []
        for section_type in ["income", "fixed", "variable"]:
            section_cats = [c for c in cats if c.category_type == section_type]
            rows = []
            for cat in section_cats:
                ist = _fc_planned_amount(active_fcs, cat.id, year, month)
                rows.append(MonthCategoryRow(category_id=cat.id, name=cat.name, ist=ist))
            sections.append(MonthSection(
                type=section_type,
                rows=rows,
                total_ist=sum(r.ist for r in rows),
            ))

        total_income = sections[0].total_ist if sections else 0.0
        total_expense = (sections[1].total_ist + sections[2].total_ist) if len(sections) > 1 else 0.0

        savings_acc_ids = [
            a.id for a in db.query(Account).filter(
                Account.household_id == hh_id,
                Account.account_role == "savings",
                Account.archived.is_(False),
            ).all()
        ]
        savings_rows = [
            SavingsRow(
                description=fc.name,
                amount=float(fc.amount),
                date=f"{year}-{month:02d}-01",
            )
            for fc in active_fcs
            if fc.cost_type == "transfer"
            and fc.to_account_id in savings_acc_ids
            and _fc_bills_in_month(fc, year, month)
        ]
        transfer_savings = sum(r.amount for r in savings_rows)

        savings_cat_ids = [
            c.id for c in db.query(Category).filter(
                Category.household_id == hh_id,
                Category.is_savings.is_(True),
            ).all()
        ]
        category_savings = sum(
            _fc_planned_amount(active_fcs, cat_id, year, month)
            for cat_id in savings_cat_ids
        )
        savings_amount = transfer_savings + category_savings
        real_savings_rate = (savings_amount / total_income * 100) if total_income > 0 else 0.0

        variable_acc_ids = [
            a.id for a in db.query(Account).filter(
                Account.household_id == hh_id,
                Account.account_role == "variable",
                Account.archived.is_(False),
            ).all()
        ]
        distribution_rows = [
            DistributionRow(
                description=fc.name,
                amount=float(fc.amount),
                date=f"{year}-{month:02d}-01",
            )
            for fc in active_fcs
            if fc.cost_type == "distribution"
            and fc.to_account_id in variable_acc_ids
            and _fc_bills_in_month(fc, year, month)
        ]

    else:
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
                ist = tx_map.get(cat.id, 0.0)
                rows.append(MonthCategoryRow(
                    category_id=cat.id,
                    name=cat.name,
                    ist=ist,
                ))
            sections.append(MonthSection(
                type=section_type,
                rows=rows,
                total_ist=sum(r.ist for r in rows),
            ))

        total_income = sum(r.ist for r in sections[0].rows) if sections else 0.0
        total_expense = (
            sum(r.ist for r in sections[1].rows) + sum(r.ist for r in sections[2].rows)
            if len(sections) > 1
            else 0.0
        )
        # Real savings rate: transfers INTO savings accounts + expenses in is_savings categories
        savings_acc_ids = [
            a.id for a in db.query(Account).filter(
                Account.household_id == hh_id,
                Account.account_role == "savings",
                Account.archived.is_(False),
            ).all()
        ]
        real_savings = 0.0
        transfer_savings = 0.0
        if savings_acc_ids:
            rs = db.query(func.sum(Transaction.amount)).filter(
                Transaction.household_id == hh_id,
                Transaction.account_id.in_(savings_acc_ids),
                Transaction.transaction_type == "transfer",
                Transaction.amount > 0,
                func.strftime("%Y", Transaction.date) == year_str,
                func.strftime("%m", Transaction.date) == month_str,
            ).scalar() or 0.0
            transfer_savings = float(rs)
            real_savings += transfer_savings

        savings_cat_ids = [
            c.id for c in db.query(Category).filter(
                Category.household_id == hh_id,
                Category.is_savings.is_(True),
            ).all()
        ]
        if savings_cat_ids:
            sc = db.query(func.sum(func.abs(Transaction.amount))).filter(
                Transaction.household_id == hh_id,
                Transaction.category_id.in_(savings_cat_ids),
                Transaction.transaction_type.in_(["expense", "income"]),
                func.strftime("%Y", Transaction.date) == year_str,
                func.strftime("%m", Transaction.date) == month_str,
            ).scalar() or 0.0
            real_savings += float(sc)

        real_savings_rate = (real_savings / total_income * 100) if total_income > 0 else 0.0
        savings_amount = real_savings

        # savings transfer rows for the month
        savings_rows = []
        if savings_acc_ids:
            s_txs = db.query(Transaction).filter(
                Transaction.household_id == hh_id,
                Transaction.account_id.in_(savings_acc_ids),
                Transaction.transaction_type == "transfer",
                Transaction.amount > 0,
                func.strftime("%Y", Transaction.date) == year_str,
                func.strftime("%m", Transaction.date) == month_str,
            ).all()
            savings_rows = [
                SavingsRow(
                    description=t.description or "Sparüberweisung",
                    amount=float(t.amount),
                    date=str(t.date),
                )
                for t in s_txs
            ]

        # distribution rows: positive transfers INTO variable accounts
        variable_acc_ids = [
            a.id for a in db.query(Account).filter(
                Account.household_id == hh_id,
                Account.account_role == "variable",
                Account.archived.is_(False),
            ).all()
        ]
        distribution_rows = []
        if variable_acc_ids:
            d_txs = db.query(Transaction).filter(
                Transaction.household_id == hh_id,
                Transaction.account_id.in_(variable_acc_ids),
                Transaction.transaction_type == "transfer",
                Transaction.amount > 0,
                func.strftime("%Y", Transaction.date) == year_str,
                func.strftime("%m", Transaction.date) == month_str,
            ).all()
            distribution_rows = [
                DistributionRow(
                    description=t.description or "Kontoverteilung",
                    amount=float(t.amount),
                    date=str(t.date),
                )
                for t in d_txs
            ]

    # Kreditlastquote: monthly payments / income
    active_loans = db.query(Loan).filter(
        Loan.household_id == hh_id,
        Loan.status == "active",
    ).all()
    total_monthly_debt = sum(float(loan.monthly_payment) for loan in active_loans) if active_loans else 0.0
    debt_to_income = (total_monthly_debt / total_income * 100) if total_income > 0 else 0.0

    # emergency_months: liquid account balances / avg monthly expenses (last 3 months)
    liquid_accounts = db.query(Account).filter(
        Account.household_id == hh_id,
        Account.account_role.in_(["fixed_costs", "variable", "savings"]),
        Account.archived.is_(False),
    ).all()
    liquid_ids = [a.id for a in liquid_accounts]
    liquid_balance = sum(float(a.starting_balance or 0) for a in liquid_accounts)
    if liquid_ids:
        tx_sum = db.query(func.sum(Transaction.amount)).filter(
            Transaction.household_id == hh_id,
            Transaction.account_id.in_(liquid_ids),
        ).scalar() or 0.0
        liquid_balance += float(tx_sum or 0)

    # avg expense over 3 months prior to selected month
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
    if avg_expense == 0.0:
        cur_expense = db.query(func.sum(func.abs(Transaction.amount))).filter(
            Transaction.household_id == hh_id,
            Transaction.transaction_type == "expense",
            func.strftime("%Y", Transaction.date) == year_str,
            func.strftime("%m", Transaction.date) == month_str,
        ).scalar() or 0.0
        avg_expense = float(cur_expense)
    emergency_months = max(0.0, liquid_balance / avg_expense) if avg_expense > 0 else 0.0

    return MonthViewResponse(
        year=year,
        month=month,
        sections=sections,
        summary=MonthSummary(
            total_income=total_income,
            total_expense=total_expense,
            savings_rate=real_savings_rate,
            savings_amount=savings_amount,
            debt_to_income=debt_to_income,
            emergency_months=emergency_months,
        ),
        savings_rows=savings_rows,
        distribution_rows=distribution_rows,
        is_planned=is_future_month,
    )
