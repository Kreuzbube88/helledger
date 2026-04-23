from datetime import date as date_type, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, extract, false, func, literal, or_
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.household import Account, Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.reports import BalanceHistoryItem, ExpensesByCategoryItem, MonthlyTrendItem

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

    savings_acc_ids = [
        a.id for a in db.query(Account).filter(
            Account.household_id == hh_id,
            Account.account_role == "savings",
            Account.archived.is_(False),
        ).all()
    ]

    income_col = func.sum(
        case((Transaction.transaction_type == "income", Transaction.amount), else_=0)
    )
    expense_col = func.abs(
        func.sum(
            case((Transaction.transaction_type == "expense", Transaction.amount), else_=0)
        )
    )
    savings_col = func.sum(case(
        (
            and_(
                Transaction.transaction_type == "transfer",
                Transaction.account_id.in_(savings_acc_ids) if savings_acc_ids else false(),
                Transaction.amount > 0,
            ),
            Transaction.amount,
        ),
        else_=literal(0),
    ))

    q = (
        db.query(
            extract("year", Transaction.date).label("year"),
            extract("month", Transaction.date).label("month"),
            income_col.label("income"),
            expense_col.label("expenses"),
            savings_col.label("savings"),
        )
        .filter(
            Transaction.household_id == hh_id,
            Transaction.date >= from_date,
            Transaction.date <= to_date,
            Transaction.transaction_type.in_(["income", "expense", "transfer"]),
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
            savings=f"{float(r.savings or 0):.2f}",
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


