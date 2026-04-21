from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.household import Category, Budget
from app.schemas.budgets import BudgetCreate, BudgetUpdate, BudgetResponse

router = APIRouter(prefix="/budgets")


def _require_active_hh(user: User) -> int:
    if user.active_household_id is None:
        raise HTTPException(status_code=400, detail="no_active_household")
    return user.active_household_id


@router.get("", response_model=list[BudgetResponse])
async def list_budgets(
    category_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    q = db.query(Budget).filter(Budget.household_id == hh_id)
    if category_id is not None:
        q = q.filter(Budget.category_id == category_id)
    return q.all()


@router.post("", response_model=BudgetResponse, status_code=201)
async def create_budget(
    body: BudgetCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    cat = db.get(Category, body.category_id)
    if cat is None or cat.household_id != hh_id:
        raise HTTPException(status_code=404, detail="category_not_found")

    open_b = db.query(Budget).filter(
        Budget.category_id == body.category_id,
        Budget.valid_until.is_(None),
    ).first()
    if open_b:
        open_b.valid_until = body.valid_from - timedelta(days=1)

    b = Budget(
        household_id=hh_id,
        category_id=body.category_id,
        amount=body.amount,
        valid_from=body.valid_from,
        valid_until=None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@router.patch("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    body: BudgetUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    b = db.get(Budget, budget_id)
    if b is None or b.household_id != hh_id:
        raise HTTPException(status_code=404, detail="not_found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(b, field, value)
    db.commit()
    db.refresh(b)
    return b


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    b = db.get(Budget, budget_id)
    if b is None or b.household_id != hh_id:
        raise HTTPException(status_code=404, detail="not_found")
    db.delete(b)
    db.commit()
