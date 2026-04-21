from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.household import Category, ExpectedValue
from app.schemas.expected_values import (
    ExpectedValueCreate, ExpectedValueUpdate, ExpectedValueResponse
)

router = APIRouter(prefix="/expected-values")


def _require_active_hh(user: User) -> int:
    if user.active_household_id is None:
        raise HTTPException(status_code=400, detail="no_active_household")
    return user.active_household_id


@router.get("", response_model=list[ExpectedValueResponse])
async def list_expected_values(
    category_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    q = db.query(ExpectedValue).filter(ExpectedValue.household_id == hh_id)
    if category_id is not None:
        q = q.filter(ExpectedValue.category_id == category_id)
    return q.all()


@router.post("", response_model=ExpectedValueResponse, status_code=201)
async def create_expected_value(
    body: ExpectedValueCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    cat = db.get(Category, body.category_id)
    if cat is None or cat.household_id != hh_id:
        raise HTTPException(status_code=404, detail="category_not_found")

    open_ev = db.query(ExpectedValue).filter(
        ExpectedValue.category_id == body.category_id,
        ExpectedValue.valid_until.is_(None),
    ).first()
    if open_ev:
        open_ev.valid_until = body.valid_from - timedelta(days=1)

    ev = ExpectedValue(
        household_id=hh_id,
        category_id=body.category_id,
        amount=body.amount,
        valid_from=body.valid_from,
        valid_until=None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


@router.patch("/{ev_id}", response_model=ExpectedValueResponse)
async def update_expected_value(
    ev_id: int,
    body: ExpectedValueUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    ev = db.get(ExpectedValue, ev_id)
    if ev is None or ev.household_id != hh_id:
        raise HTTPException(status_code=404, detail="not_found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(ev, field, value)
    db.commit()
    db.refresh(ev)
    return ev


@router.delete("/{ev_id}", status_code=204)
async def delete_expected_value(
    ev_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    ev = db.get(ExpectedValue, ev_id)
    if ev is None or ev.household_id != hh_id:
        raise HTTPException(status_code=404, detail="not_found")
    db.delete(ev)
    db.commit()
