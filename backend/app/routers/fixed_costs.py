from datetime import date as date_type, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.fixed_cost import FixedCost
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.fixed_costs import (
    FixedCostAmountChange, FixedCostCreate, FixedCostResponse,
    FixedCostUpdate, ReserveResponse, ReserveItem,
)

router = APIRouter(prefix="/fixed-costs", tags=["fixed-costs"])


def _add_months(d: date_type, months: int) -> date_type:
    import calendar
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date_type(year, month, day)


def _get_fc(fc_id: int, hh_id: int, db: Session) -> FixedCost:
    fc = db.query(FixedCost).filter(
        FixedCost.id == fc_id, FixedCost.household_id == hh_id
    ).first()
    if not fc:
        raise HTTPException(status_code=404, detail="not_found")
    return fc


# ── List ──────────────────────────────────────────────────────────────
@router.get("", response_model=list[FixedCostResponse])
def list_fixed_costs(
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    q = db.query(FixedCost).filter(FixedCost.household_id == user.active_household_id)
    if not include_inactive:
        today = date_type.today()
        q = q.filter(
            FixedCost.is_active.is_(True),
            or_(FixedCost.end_date.is_(None), FixedCost.end_date >= today),
        )
    return q.order_by(FixedCost.cost_type, FixedCost.name).all()


# ── Create ─────────────────────────────────────────────────────────────
@router.post("", response_model=FixedCostResponse, status_code=201)
def create_fixed_cost(
    body: FixedCostCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    data = body.model_dump()
    if data.get("next_date") is None:
        data["next_date"] = data["start_date"]
    fc = FixedCost(
        household_id=user.active_household_id,
        **data,
    )
    db.add(fc)
    db.commit()
    db.refresh(fc)
    return fc


# ── Trigger ────────────────────────────────────────────────────────────
@router.post("/trigger", status_code=200)
def trigger_due(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    hh_id = user.active_household_id
    today = date_type.today()
    due = db.query(FixedCost).filter(
        FixedCost.household_id == hh_id,
        FixedCost.next_date <= today,
        FixedCost.is_active.is_(True),
        FixedCost.account_id.isnot(None),
        or_(FixedCost.end_date.is_(None), FixedCost.end_date >= today),
    ).all()
    count = 0
    for fc in due:
        if fc.cost_type == 'transfer':
            debit = Transaction(
                household_id=hh_id,
                account_id=fc.account_id,
                amount=-abs(fc.amount),
                date=fc.next_date,
                description=fc.name,
                transaction_type='transfer',
                is_auto_generated=True,
            )
            db.add(debit)
            db.flush()
            credit = Transaction(
                household_id=hh_id,
                account_id=fc.to_account_id,
                amount=abs(fc.amount),
                date=fc.next_date,
                description=fc.name,
                transaction_type='transfer',
                is_auto_generated=True,
                transfer_peer_id=debit.id,
            )
            db.add(credit)
            db.flush()
            debit.transfer_peer_id = credit.id
        else:
            sign = Decimal("1") if fc.cost_type == "income" else Decimal("-1")
            db.add(Transaction(
                household_id=hh_id,
                account_id=fc.account_id,
                category_id=fc.category_id,
                amount=sign * abs(fc.amount),
                date=fc.next_date,
                description=fc.name,
                transaction_type=fc.cost_type,
                is_auto_generated=True,
            ))
        fc.next_date = _add_months(fc.next_date, fc.interval_months)
        count += 1
    db.commit()
    return {"status": "triggered", "count": count}


# ── Reserve ────────────────────────────────────────────────────────────
@router.get("/reserve", response_model=ReserveResponse)
def get_reserve(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    hh_id = user.active_household_id
    today = date_type.today()
    active_fcs = db.query(FixedCost).filter(
        FixedCost.household_id == hh_id,
        FixedCost.is_active.is_(True),
        FixedCost.cost_type == "expense",
        FixedCost.interval_months > 1,
        or_(FixedCost.end_date.is_(None), FixedCost.end_date >= today),
    ).all()
    items = [
        ReserveItem(
            id=fc.id,
            name=fc.name,
            full_amount=float(fc.amount),
            interval_months=fc.interval_months,
            monthly_share=float(fc.amount) / fc.interval_months,
            next_billing=fc.next_date.isoformat(),
        )
        for fc in active_fcs
    ]
    return ReserveResponse(
        total_monthly=sum(i.monthly_share for i in items),
        items=items,
    )


# ── Expiring soon ──────────────────────────────────────────────────────
@router.get("/expiring-soon")
def expiring_soon(
    days: int = Query(30),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    hh_id = user.active_household_id
    today = date_type.today()
    cutoff = today + timedelta(days=days)
    fcs = db.query(FixedCost).filter(
        FixedCost.household_id == hh_id,
        FixedCost.is_active.is_(True),
        FixedCost.end_date.isnot(None),
        FixedCost.end_date >= today,
        FixedCost.end_date <= cutoff,
    ).order_by(FixedCost.end_date).all()
    return [
        {
            "id": fc.id,
            "name": fc.name,
            "end_date": fc.end_date.isoformat(),
            "days_left": (fc.end_date - today).days,
        }
        for fc in fcs
    ]


# ── Update ─────────────────────────────────────────────────────────────
@router.patch("/{fc_id}", response_model=FixedCostResponse)
def update_fixed_cost(
    fc_id: int,
    body: FixedCostUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    fc = _get_fc(fc_id, user.active_household_id, db)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(fc, k, v)
    db.commit()
    db.refresh(fc)
    return fc


# ── Amount change (versioning) ─────────────────────────────────────────
@router.patch("/{fc_id}/amount", response_model=FixedCostResponse)
def change_amount(
    fc_id: int,
    body: FixedCostAmountChange,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    fc = _get_fc(fc_id, user.active_household_id, db)
    # Close current entry
    fc.end_date = body.valid_from - timedelta(days=1)
    fc.is_active = False
    # Calculate next_date for new entry: first occurrence >= valid_from
    new_next = fc.start_date
    while new_next < body.valid_from:
        new_next = _add_months(new_next, fc.interval_months)
    new_fc = FixedCost(
        household_id=fc.household_id,
        name=fc.name,
        amount=body.new_amount,
        cost_type=fc.cost_type,
        category_id=fc.category_id,
        account_id=fc.account_id,
        to_account_id=fc.to_account_id,
        interval_months=fc.interval_months,
        show_split=fc.show_split,
        start_date=body.valid_from,
        end_date=None,
        next_date=new_next,
        loan_id=fc.loan_id,
        is_active=True,
    )
    db.add(new_fc)
    db.commit()
    db.refresh(new_fc)
    return new_fc


# ── Deactivate ─────────────────────────────────────────────────────────
@router.delete("/{fc_id}", status_code=204)
def deactivate_fixed_cost(
    fc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    fc = _get_fc(fc_id, user.active_household_id, db)
    fc.is_active = False
    fc.end_date = date_type.today()
    db.commit()
