from datetime import date as date_type, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.recurring import RecurringTemplate
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.recurring import (
    RecurringTemplateCreate,
    RecurringTemplateResponse,
    RecurringTemplateUpdate,
)
from app.services.loan_calc import _add_months

router = APIRouter(prefix="/recurring")

MONTHS_MAP = {"quarterly": 3, "semi_annual": 6, "annual": 12}


def _require_active_hh(user: User) -> int:
    if user.active_household_id is None:
        raise HTTPException(status_code=400, detail="no_active_household")
    return user.active_household_id


def _get_template(template_id: int, hh_id: int, db: Session) -> RecurringTemplate:
    tmpl = db.get(RecurringTemplate, template_id)
    if tmpl is None or tmpl.household_id != hh_id:
        raise HTTPException(status_code=404, detail="not_found")
    return tmpl


@router.get("", response_model=list[RecurringTemplateResponse])
async def list_templates(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    return (
        db.query(RecurringTemplate)
        .filter(
            RecurringTemplate.household_id == hh_id,
            RecurringTemplate.is_active.is_(True),
        )
        .all()
    )


@router.get("/soll-map")
async def soll_map(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    templates = (
        db.query(RecurringTemplate)
        .filter(
            RecurringTemplate.household_id == hh_id,
            RecurringTemplate.is_active.is_(True),
            RecurringTemplate.category_id.isnot(None),
        )
        .all()
    )
    return {str(tmpl.category_id): float(tmpl.amount) for tmpl in templates}


@router.post("", response_model=RecurringTemplateResponse, status_code=201)
async def create_template(
    body: RecurringTemplateCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    tmpl = RecurringTemplate(
        household_id=hh_id,
        name=body.name,
        amount=body.amount,
        category_id=body.category_id,
        account_id=body.account_id,
        interval=body.interval,
        day_of_month=body.day_of_month,
        next_date=body.next_date,
        show_as_monthly=body.show_as_monthly,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


@router.patch("/{template_id}", response_model=RecurringTemplateResponse)
async def update_template(
    template_id: int,
    body: RecurringTemplateUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    tmpl = _get_template(template_id, hh_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tmpl, field, value)
    db.commit()
    db.refresh(tmpl)
    return tmpl


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    tmpl = _get_template(template_id, hh_id, db)
    db.delete(tmpl)
    db.commit()


@router.post("/trigger")
async def trigger_due(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    today = date_type.today()
    due = (
        db.query(RecurringTemplate)
        .filter(
            RecurringTemplate.household_id == hh_id,
            RecurringTemplate.is_active.is_(True),
            RecurringTemplate.next_date <= today,
        )
        .all()
    )
    count = 0
    now = datetime.now(timezone.utc)
    for tmpl in due:
        if tmpl.account_id is not None:
            tx = Transaction(
                household_id=hh_id,
                account_id=tmpl.account_id,
                category_id=tmpl.category_id,
                amount=-abs(tmpl.amount),
                date=tmpl.next_date,
                description=tmpl.name,
                transaction_type="expense",
                is_auto_generated=True,
                created_at=now,
                updated_at=now,
            )
            db.add(tx)
            count += 1
            months = MONTHS_MAP.get(tmpl.interval, 1)
            tmpl.next_date = _add_months(tmpl.next_date, months)
    db.commit()
    return {"status": "triggered", "count": count}


@router.get("/monthly-reserve")
async def monthly_reserve(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    templates = (
        db.query(RecurringTemplate)
        .filter(
            RecurringTemplate.household_id == hh_id,
            RecurringTemplate.is_active.is_(True),
            RecurringTemplate.show_as_monthly.is_(True),
            RecurringTemplate.interval != "monthly",
        )
        .all()
    )
    items = []
    total = 0.0
    for tmpl in templates:
        months = MONTHS_MAP.get(tmpl.interval, 1)
        monthly_equiv = float(tmpl.amount) / months
        total += monthly_equiv
        items.append(
            {
                "name": tmpl.name,
                "amount": float(tmpl.amount),
                "interval": tmpl.interval,
                "monthly_equiv": round(monthly_equiv, 2),
            }
        )
    return {"total": round(total, 2), "items": items}
