import calendar
from datetime import date as date_type
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.fixed_cost import FixedCost
from app.models.household import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.forecast import AccountForecastBalance, ForecastMonth, ForecastResponse

router = APIRouter(prefix="/forecast", tags=["forecast"])


def _fc_fires_in_month(fc: FixedCost, target_year: int, target_month: int) -> bool:
    target_first = date_type(target_year, target_month, 1)
    if fc.start_date > date_type(target_year, target_month, calendar.monthrange(target_year, target_month)[1]):
        return False
    if fc.end_date is not None and fc.end_date < target_first:
        return False
    months_diff = (target_year - fc.start_date.year) * 12 + (target_month - fc.start_date.month)
    return months_diff >= 0 and months_diff % fc.interval_months == 0


@router.get("", response_model=ForecastResponse)
def get_forecast(
    months: int = Query(12, ge=1, le=60),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")

    hh_id = user.active_household_id
    today = date_type.today()

    # Live balances per account
    accounts = db.query(Account).filter(
        Account.household_id == hh_id,
        Account.archived.is_(False),
    ).all()

    balances: dict[int, float] = {}
    savings_acc_ids = {acc.id for acc in accounts if acc.account_role == "savings"}
    for acc in accounts:
        tx_sum = db.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == acc.id,
        ).scalar() or Decimal("0")
        balances[acc.id] = float((acc.starting_balance or Decimal("0")) + tx_sum)

    # Active fixed costs
    active_fcs = db.query(FixedCost).filter(
        FixedCost.household_id == hh_id,
        FixedCost.is_active.is_(True),
        or_(FixedCost.end_date.is_(None), FixedCost.end_date >= today),
    ).all()

    result_months: list[ForecastMonth] = []

    for i in range(months):
        # Compute target year/month
        total_months = today.month + i
        target_year = today.year + (total_months - 1) // 12
        target_month = (total_months - 1) % 12 + 1

        month_income = 0.0
        month_fixed_expenses = 0.0
        month_savings = 0.0

        for fc in active_fcs:
            if not _fc_fires_in_month(fc, target_year, target_month):
                continue
            amount = float(fc.amount)
            if fc.cost_type == "income":
                month_income += amount
                if fc.account_id is not None and fc.account_id in balances:
                    balances[fc.account_id] = balances.get(fc.account_id, 0.0) + amount
            elif fc.cost_type == "expense":
                month_fixed_expenses += amount
                if fc.account_id is not None and fc.account_id in balances:
                    balances[fc.account_id] = balances.get(fc.account_id, 0.0) - amount
            elif fc.cost_type == "transfer":
                # debit from account_id, credit to to_account_id
                if fc.account_id is not None and fc.account_id in balances:
                    balances[fc.account_id] = balances.get(fc.account_id, 0.0) - amount
                if fc.to_account_id is not None and fc.to_account_id in balances:
                    if fc.to_account_id in savings_acc_ids:
                        month_savings += amount
                    balances[fc.to_account_id] = balances.get(fc.to_account_id, 0.0) + amount

        total_balance = sum(balances.values())

        account_snapshots = [
            AccountForecastBalance(
                account_id=acc.id,
                account_name=acc.name,
                account_role=acc.account_role,
                balance=balances.get(acc.id, 0.0),
            )
            for acc in accounts
        ]

        result_months.append(ForecastMonth(
            month=f"{target_year}-{target_month:02d}",
            income=month_income,
            fixed_expenses=month_fixed_expenses,
            savings_transfers=month_savings,
            total_balance=total_balance,
            accounts=account_snapshots,
        ))

    return ForecastResponse(months=result_months)
