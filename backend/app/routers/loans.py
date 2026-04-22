import io
import csv
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.loan import Loan, LoanExtraPayment
from app.models.household import Category, ExpectedValue
from app.schemas.loans import (
    LoanCreate, LoanUpdate, LoanResponse, LoanStatsResponse,
    ExtraPaymentCreate, ExtraPaymentResponse, LoanNetWorthSummary,
)
from app.services.loan_calc import (
    calc_payment, calc_term, calc_principal, calc_rate_newton,
    calc_amortization, calc_stats,
)

router = APIRouter(prefix="/loans")


def _require_active_hh(user: User) -> int:
    if user.active_household_id is None:
        raise HTTPException(status_code=400, detail="no_active_household")
    return user.active_household_id


def _get_loan(loan_id: int, hh_id: int, db: Session) -> Loan:
    loan = db.get(Loan, loan_id)
    if loan is None or loan.household_id != hh_id:
        raise HTTPException(status_code=404, detail="not_found")
    return loan


def _extra_payments_for(loan_id: int, db: Session) -> list[dict]:
    rows = db.query(LoanExtraPayment).filter(LoanExtraPayment.loan_id == loan_id).all()
    return [
        {"payment_date": ep.payment_date, "amount": float(ep.amount), "effect": ep.effect}
        for ep in rows
    ]


def _build_response(loan: Loan, db: Session) -> LoanResponse:
    extra_payments = _extra_payments_for(loan.id, db)
    monthly_extra = float(loan.monthly_extra) if loan.monthly_extra else 0.0
    stats = calc_stats(
        float(loan.principal), float(loan.interest_rate),
        float(loan.monthly_payment), loan.term_months,
        loan.start_date, extra_payments, monthly_extra,
    )
    ltv = None
    if loan.property_value and loan.property_value > 0:
        ltv = round(float(loan.principal) / float(loan.property_value) * 100, 2)
    expiring_soon = False
    if loan.fixed_rate_until:
        expiring_soon = loan.fixed_rate_until <= date.today() + timedelta(days=365)
    return LoanResponse(
        id=loan.id,
        household_id=loan.household_id,
        name=loan.name,
        loan_type=loan.loan_type,
        lender=loan.lender,
        principal=loan.principal,
        interest_rate=loan.interest_rate,
        monthly_payment=loan.monthly_payment,
        term_months=loan.term_months,
        start_date=loan.start_date,
        is_existing=loan.is_existing,
        monthly_extra=loan.monthly_extra,
        status=loan.status,
        paid_off_date=loan.paid_off_date,
        category_id=loan.category_id,
        include_in_net_worth=loan.include_in_net_worth,
        current_balance=stats["current_balance"],
        payoff_date=stats["payoff_date"],
        purchase_price=loan.purchase_price,
        equity=loan.equity,
        property_value=loan.property_value,
        fixed_rate_until=loan.fixed_rate_until,
        land_charge=loan.land_charge,
        ltv=ltv,
        fixed_rate_expiring_soon=expiring_soon,
    )


def _resolve_loan_fields(body: LoanCreate) -> tuple[Decimal, Decimal, Decimal, int]:
    """Resolve the missing 3-of-4 field and return (principal, rate, payment, term)."""
    p = float(body.principal) if body.principal is not None else None
    r = float(body.interest_rate) if body.interest_rate is not None else None
    pmt = float(body.monthly_payment) if body.monthly_payment is not None else None
    n = body.term_months

    try:
        if p is None:
            p = calc_principal(pmt, r, n)
        elif r is None:
            r = calc_rate_newton(p, pmt, n)
        elif pmt is None:
            pmt = calc_payment(p, r, n)
        elif n is None:
            n = calc_term(p, r, pmt)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return Decimal(str(round(p, 2))), Decimal(str(round(r, 6))), Decimal(str(round(pmt, 2))), int(n)


@router.get("", response_model=list[LoanResponse])
async def list_loans(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    loans = db.query(Loan).filter(Loan.household_id == hh_id).all()
    return [_build_response(loan, db) for loan in loans]


@router.get("/net-worth-summary", response_model=LoanNetWorthSummary)
async def net_worth_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    loans = (
        db.query(Loan)
        .filter(Loan.household_id == hh_id, Loan.include_in_net_worth.is_(True), Loan.status == "active")
        .all()
    )
    items = []
    total = 0.0
    for loan in loans:
        extra_payments = _extra_payments_for(loan.id, db)
        monthly_extra = float(loan.monthly_extra) if loan.monthly_extra else 0.0
        stats = calc_stats(
            float(loan.principal), float(loan.interest_rate),
            float(loan.monthly_payment), loan.term_months,
            loan.start_date, extra_payments, monthly_extra,
        )
        bal = stats["current_balance"]
        total += bal
        items.append({"id": loan.id, "name": loan.name, "current_balance": round(bal, 2)})
    return LoanNetWorthSummary(total_liability=round(total, 2), loans=items)


@router.post("", response_model=LoanResponse, status_code=201)
async def create_loan(
    body: LoanCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    principal, interest_rate, monthly_payment, term_months = _resolve_loan_fields(body)
    now = datetime.now(timezone.utc)

    loan = Loan(
        household_id=hh_id,
        name=body.name,
        loan_type=body.loan_type,
        lender=body.lender,
        principal=principal,
        interest_rate=interest_rate,
        monthly_payment=monthly_payment,
        term_months=term_months,
        start_date=body.start_date,
        is_existing=body.is_existing,
        monthly_extra=body.monthly_extra,
        include_in_net_worth=body.include_in_net_worth,
        purchase_price=body.purchase_price,
        equity=body.equity,
        property_value=body.property_value,
        fixed_rate_until=body.fixed_rate_until,
        land_charge=body.land_charge,
        created_at=now,
        updated_at=now,
    )
    db.add(loan)
    db.flush()

    # Auto-create Fixkosten category
    cat = Category(
        household_id=hh_id,
        name=f"Kreditrate: {loan.name}",
        category_type="fixed",
        color="#8b5cf6",
        created_at=now,
        updated_at=now,
    )
    db.add(cat)
    db.flush()
    loan.category_id = cat.id

    effective_payment = monthly_payment + (body.monthly_extra or Decimal("0"))
    ev = ExpectedValue(
        household_id=hh_id,
        category_id=cat.id,
        amount=effective_payment,
        valid_from=body.start_date,
        created_at=now,
    )
    db.add(ev)
    db.commit()
    db.refresh(loan)
    return _build_response(loan, db)


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(
    loan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    loan = _get_loan(loan_id, hh_id, db)
    return _build_response(loan, db)


@router.patch("/{loan_id}", response_model=LoanResponse)
async def update_loan(
    loan_id: int,
    body: LoanUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    loan = _get_loan(loan_id, hh_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(loan, field, value)
    loan.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(loan)
    return _build_response(loan, db)


@router.delete("/{loan_id}", status_code=204)
async def delete_loan(
    loan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    loan = _get_loan(loan_id, hh_id, db)
    now = datetime.now(timezone.utc)
    if loan.category_id:
        cat = db.get(Category, loan.category_id)
        if cat:
            cat.archived = True
            cat.updated_at = now
            ev = (
                db.query(ExpectedValue)
                .filter(ExpectedValue.category_id == cat.id, ExpectedValue.valid_until.is_(None))
                .first()
            )
            if ev:
                ev.valid_until = date.today()
    db.delete(loan)
    db.commit()


@router.get("/{loan_id}/amortization")
async def get_amortization(
    loan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    loan = _get_loan(loan_id, hh_id, db)
    extra_payments = _extra_payments_for(loan_id, db)
    monthly_extra = float(loan.monthly_extra) if loan.monthly_extra else 0.0
    rows = calc_amortization(
        float(loan.principal), float(loan.interest_rate),
        float(loan.monthly_payment), loan.term_months,
        loan.start_date, extra_payments, monthly_extra,
    )
    return rows


@router.get("/{loan_id}/amortization/csv")
async def get_amortization_csv(
    loan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    loan = _get_loan(loan_id, hh_id, db)
    extra_payments = _extra_payments_for(loan_id, db)
    monthly_extra = float(loan.monthly_extra) if loan.monthly_extra else 0.0
    rows = calc_amortization(
        float(loan.principal), float(loan.interest_rate),
        float(loan.monthly_payment), loan.term_months,
        loan.start_date, extra_payments, monthly_extra,
    )

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    output.seek(0)
    filename = f"tilgungsplan-{loan.name.replace(' ', '-')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{loan_id}/stats", response_model=LoanStatsResponse)
async def get_stats(
    loan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    loan = _get_loan(loan_id, hh_id, db)
    extra_payments = _extra_payments_for(loan_id, db)
    monthly_extra = float(loan.monthly_extra) if loan.monthly_extra else 0.0
    stats = calc_stats(
        float(loan.principal), float(loan.interest_rate),
        float(loan.monthly_payment), loan.term_months,
        loan.start_date, extra_payments, monthly_extra,
    )
    return LoanStatsResponse(**stats)


@router.post("/{loan_id}/extra-payments", response_model=ExtraPaymentResponse, status_code=201)
async def add_extra_payment(
    loan_id: int,
    body: ExtraPaymentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    loan = _get_loan(loan_id, hh_id, db)
    now = datetime.now(timezone.utc)

    ep = LoanExtraPayment(
        loan_id=loan_id,
        payment_date=body.payment_date,
        amount=body.amount,
        effect=body.effect,
        notes=body.notes,
        created_at=now,
    )
    db.add(ep)
    db.flush()

    # If reduce_payment: recalculate monthly_payment and update ExpectedValue
    if body.effect == "reduce_payment" and loan.category_id:
        # db.flush() already made ep queryable — no append needed
        all_eps = _extra_payments_for(loan_id, db)
        monthly_extra = float(loan.monthly_extra) if loan.monthly_extra else 0.0
        rows = calc_amortization(
            float(loan.principal), float(loan.interest_rate),
            float(loan.monthly_payment), loan.term_months,
            loan.start_date, all_eps, monthly_extra,
        )
        # Find balance just before the extra payment date
        new_balance = None
        for row in rows:
            if row["date"] >= body.payment_date.isoformat():
                new_balance = row["balance"]
                break
        if new_balance is not None and new_balance > 0:
            remaining = len([r for r in rows if r["date"] >= body.payment_date.isoformat()])
            if remaining > 0:
                new_pmt = calc_payment(new_balance, float(loan.interest_rate), remaining)
                loan.monthly_payment = Decimal(str(round(new_pmt, 2)))

                # Close existing ExpectedValue, create new one
                old_ev = (
                    db.query(ExpectedValue)
                    .filter(ExpectedValue.category_id == loan.category_id, ExpectedValue.valid_until.is_(None))
                    .first()
                )
                if old_ev:
                    old_ev.valid_until = body.payment_date - timedelta(days=1)
                new_ev = ExpectedValue(
                    household_id=hh_id,
                    category_id=loan.category_id,
                    amount=Decimal(str(round(new_pmt + monthly_extra, 2))),
                    valid_from=body.payment_date,
                    created_at=now,
                )
                db.add(new_ev)

    loan.updated_at = now
    db.commit()
    db.refresh(ep)
    return ep


@router.delete("/{loan_id}/extra-payments/{ep_id}", status_code=204)
async def delete_extra_payment(
    loan_id: int,
    ep_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    _get_loan(loan_id, hh_id, db)
    ep = db.get(LoanExtraPayment, ep_id)
    if ep is None or ep.loan_id != loan_id:
        raise HTTPException(status_code=404, detail="not_found")
    db.delete(ep)
    db.commit()


@router.get("/{loan_id}/extra-payments", response_model=list[ExtraPaymentResponse])
async def list_extra_payments(
    loan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    _get_loan(loan_id, hh_id, db)
    return db.query(LoanExtraPayment).filter(LoanExtraPayment.loan_id == loan_id).all()


@router.patch("/{loan_id}/mark-paid-off", response_model=LoanResponse)
async def mark_paid_off(
    loan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    loan = _get_loan(loan_id, hh_id, db)
    now = datetime.now(timezone.utc)
    loan.status = "paid_off"
    loan.paid_off_date = date.today()
    loan.updated_at = now
    if loan.category_id:
        cat = db.get(Category, loan.category_id)
        if cat:
            cat.archived = True
            cat.updated_at = now
            ev = (
                db.query(ExpectedValue)
                .filter(ExpectedValue.category_id == cat.id, ExpectedValue.valid_until.is_(None))
                .first()
            )
            if ev:
                ev.valid_until = date.today()
    db.commit()
    db.refresh(loan)
    return _build_response(loan, db)
