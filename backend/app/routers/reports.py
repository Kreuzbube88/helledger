from datetime import date as date_type, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, extract, func, or_
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.household import Account, Budget, Category, ExpectedValue
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.reports import BalanceHistoryItem, ExpensesByCategoryItem, MonthlyTrendItem
from app.schemas.transaction import SollIstNode

router = APIRouter(prefix="/reports", tags=["reports"])


def _require_active_hh(user: User) -> int:
    if user.active_household_id is None:
        raise HTTPException(status_code=400, detail="no_active_household")
    return user.active_household_id


def _validate_dates(from_date: date_type, to_date: date_type) -> None:
    if from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date_after_to_date")


@router.get("/expenses-by-category", response_model=list[ExpensesByCategoryItem])
async def expenses_by_category(
    from_date: date_type = Query(...),
    to_date: date_type = Query(...),
    account_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    _validate_dates(from_date, to_date)
    q = (
        db.query(
            Transaction.category_id,
            Category.name.label("category_name"),
            func.abs(func.sum(Transaction.amount)).label("total"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.household_id == hh_id,
            Transaction.date >= from_date,
            Transaction.date <= to_date,
            Transaction.transaction_type == "expense",
        )
    )
    if account_id is not None:
        acc = db.get(Account, account_id)
        if acc is None:
            raise HTTPException(status_code=404, detail="not_found")
        if acc.household_id != hh_id:
            raise HTTPException(status_code=403, detail="forbidden")
        q = q.filter(Transaction.account_id == account_id)
    rows = (
        q.group_by(Transaction.category_id, Category.name)
        .order_by(func.abs(func.sum(Transaction.amount)).desc())
        .all()
    )
    return [
        ExpensesByCategoryItem(
            category_id=r.category_id,
            category_name=r.category_name,
            total=f"{r.total:.2f}",
        )
        for r in rows
    ]


@router.get("/monthly-trend", response_model=list[MonthlyTrendItem])
async def monthly_trend(
    from_date: date_type = Query(...),
    to_date: date_type = Query(...),
    account_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    _validate_dates(from_date, to_date)
    income_col = func.sum(
        case((Transaction.transaction_type == "income", Transaction.amount), else_=0)
    )
    expense_col = func.abs(
        func.sum(
            case((Transaction.transaction_type == "expense", Transaction.amount), else_=0)
        )
    )
    q = (
        db.query(
            extract("year", Transaction.date).label("year"),
            extract("month", Transaction.date).label("month"),
            income_col.label("income"),
            expense_col.label("expenses"),
        )
        .filter(
            Transaction.household_id == hh_id,
            Transaction.date >= from_date,
            Transaction.date <= to_date,
            Transaction.transaction_type.in_(["income", "expense"]),
        )
    )
    if account_id is not None:
        acc = db.get(Account, account_id)
        if acc is None:
            raise HTTPException(status_code=404, detail="not_found")
        if acc.household_id != hh_id:
            raise HTTPException(status_code=403, detail="forbidden")
        q = q.filter(Transaction.account_id == account_id)
    rows = q.group_by("year", "month").order_by("year", "month").all()
    return [
        MonthlyTrendItem(
            year=int(r.year),
            month=int(r.month),
            income=f"{r.income or Decimal('0'):.2f}",
            expenses=f"{r.expenses or Decimal('0'):.2f}",
        )
        for r in rows
    ]


@router.get("/balance-history", response_model=list[BalanceHistoryItem])
async def balance_history(
    from_date: date_type = Query(...),
    to_date: date_type = Query(...),
    account_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    _validate_dates(from_date, to_date)
    acc = db.get(Account, account_id)
    if acc is None:
        raise HTTPException(status_code=404, detail="not_found")
    if acc.household_id != hh_id:
        raise HTTPException(status_code=403, detail="forbidden")

    pre_sum = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.account_id == account_id, Transaction.date < from_date)
        .scalar()
    ) or Decimal("0")
    running = (acc.starting_balance or Decimal("0")) + pre_sum

    use_weekly = (to_date - from_date).days > 365

    if use_weekly:
        rows = (
            db.query(
                func.strftime("%Y-%W", Transaction.date).label("week"),
                func.sum(Transaction.amount).label("total"),
            )
            .filter(
                Transaction.account_id == account_id,
                Transaction.date >= from_date,
                Transaction.date <= to_date,
            )
            .group_by("week")
            .order_by("week")
            .all()
        )
        result = []
        for r in rows:
            running += r.total or Decimal("0")
            result.append(BalanceHistoryItem(date=r.week, balance=f"{running:.2f}"))
        return result

    tx_rows = (
        db.query(
            Transaction.date.label("day"),
            func.sum(Transaction.amount).label("total"),
        )
        .filter(
            Transaction.account_id == account_id,
            Transaction.date >= from_date,
            Transaction.date <= to_date,
        )
        .group_by(Transaction.date)
        .order_by(Transaction.date)
        .all()
    )
    tx_map: dict[str, Decimal] = {
        str(r.day): r.total or Decimal("0") for r in tx_rows
    }
    result = []
    current = from_date
    while current <= to_date:
        running += tx_map.get(str(current), Decimal("0"))
        result.append(BalanceHistoryItem(date=str(current), balance=f"{running:.2f}"))
        current += timedelta(days=1)
    return result


@router.get("/soll-ist", response_model=list[SollIstNode])
async def reports_soll_ist(
    from_date: date_type = Query(...),
    to_date: date_type = Query(...),
    account_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    _validate_dates(from_date, to_date)
    months_in_range = (
        (to_date.year - from_date.year) * 12 + to_date.month - from_date.month + 1
    )
    cats = db.query(Category).filter(
        Category.household_id == hh_id,
        Category.archived.is_(False),
    ).all()
    if not cats:
        return []
    cat_ids = [c.id for c in cats]

    tx_q = (
        db.query(Transaction.category_id, func.sum(Transaction.amount))
        .filter(
            Transaction.household_id == hh_id,
            Transaction.date >= from_date,
            Transaction.date <= to_date,
            Transaction.transaction_type.in_(["income", "expense"]),
            Transaction.category_id.isnot(None),
        )
    )
    if account_id is not None:
        acc = db.get(Account, account_id)
        if acc is None:
            raise HTTPException(status_code=404, detail="not_found")
        if acc.household_id != hh_id:
            raise HTTPException(status_code=403, detail="forbidden")
        tx_q = tx_q.filter(Transaction.account_id == account_id)
    tx_map: dict[int, Decimal] = {
        cat_id: amt for cat_id, amt in tx_q.group_by(Transaction.category_id).all()
    }

    ev_rows = db.query(ExpectedValue).filter(
        ExpectedValue.category_id.in_(cat_ids),
        ExpectedValue.valid_from <= from_date,
        or_(ExpectedValue.valid_until.is_(None), ExpectedValue.valid_until >= from_date),
    ).all()
    ev_map: dict[int, Decimal] = {ev.category_id: ev.amount for ev in ev_rows}

    budget_rows = db.query(Budget).filter(
        Budget.category_id.in_(cat_ids),
        Budget.valid_from <= from_date,
        or_(Budget.valid_until.is_(None), Budget.valid_until >= from_date),
    ).all()
    budget_map: dict[int, Decimal] = {b.category_id: b.amount for b in budget_rows}

    def _build(parent_id: int | None) -> list[SollIstNode]:
        result = []
        for cat in cats:
            if cat.parent_id != parent_id:
                continue
            children = _build(cat.id)
            ist_self = tx_map.get(cat.id, Decimal("0"))
            ist_children = sum(Decimal(c.ist) for c in children)
            ist = ist_self + ist_children
            monthly_soll = ev_map.get(cat.id) or budget_map.get(cat.id) or Decimal("0")
            soll_self = monthly_soll * months_in_range
            soll_children = sum(Decimal(c.soll) for c in children)
            soll = soll_self if soll_self > Decimal("0") else soll_children
            result.append(
                SollIstNode(
                    id=cat.id,
                    name=cat.name,
                    category_type=cat.category_type,
                    soll=f"{soll:.2f}",
                    ist=f"{ist:.2f}",
                    diff=f"{soll - ist:.2f}",
                    children=children,
                )
            )
        return result

    return _build(None)
