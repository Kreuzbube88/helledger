from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.household import Account
from app.models.savings_goal import SavingsGoal
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.savings_goals import SavingsGoalCreate, SavingsGoalResponse, SavingsGoalUpdate

router = APIRouter(prefix="/goals", tags=["savings-goals"])


def _calc_balance(account_id: int, hh_id: int, db: Session) -> float:
    account = db.get(Account, account_id)
    if not account or account.household_id != hh_id:
        return 0.0
    tx_sum = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.household_id == hh_id,
            Transaction.account_id == account_id,
            Transaction.transaction_type.in_(["income", "expense", "transfer"]),
        )
        .scalar()
        or Decimal("0")
    )
    return float(account.starting_balance + tx_sum)


def _build_response(goal: SavingsGoal, hh_id: int, db: Session) -> SavingsGoalResponse:
    if goal.account_id:
        current_amount = _calc_balance(goal.account_id, hh_id, db)
    else:
        current_amount = 0.0
    target = float(goal.target_amount)
    progress_pct = min(current_amount / target * 100, 100.0) if target > 0 else 0.0
    resp = SavingsGoalResponse.model_validate(goal)
    resp.current_amount = current_amount
    resp.progress_pct = progress_pct
    return resp


@router.get("", response_model=list[SavingsGoalResponse])
def list_goals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    hh_id = user.active_household_id
    goals = (
        db.query(SavingsGoal)
        .filter(SavingsGoal.household_id == hh_id)
        .order_by(SavingsGoal.created_at.asc())
        .all()
    )
    return [_build_response(g, hh_id, db) for g in goals]


@router.post("", response_model=SavingsGoalResponse, status_code=201)
def create_goal(
    body: SavingsGoalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    hh_id = user.active_household_id
    goal = SavingsGoal(
        household_id=hh_id,
        name=body.name,
        target_amount=body.target_amount,
        target_date=body.target_date,
        account_id=body.account_id,
        color=body.color,
        notes=body.notes,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _build_response(goal, hh_id, db)


@router.patch("/{goal_id}", response_model=SavingsGoalResponse)
def update_goal(
    goal_id: int,
    body: SavingsGoalUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    hh_id = user.active_household_id
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.household_id == hh_id,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="not_found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return _build_response(goal, hh_id, db)


@router.delete("/{goal_id}", status_code=204)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    hh_id = user.active_household_id
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.household_id == hh_id,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="not_found")
    db.delete(goal)
    db.commit()
