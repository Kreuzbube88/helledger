from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate, TransferCreate, TransactionUpdate,
    TransactionResponse, SummaryResponse,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _require_active_hh(user: User) -> int:
    if user.active_household_id is None:
        raise HTTPException(status_code=400, detail="no_active_household")
    return user.active_household_id


def _apply_sign(amount: Decimal, transaction_type: str) -> Decimal:
    if transaction_type == "expense":
        return -abs(amount)
    return abs(amount)


def _get_tx(db: Session, tx_id: int, hh_id: int) -> Transaction:
    tx = db.get(Transaction, tx_id)
    if tx is None or tx.household_id != hh_id:
        raise HTTPException(status_code=404, detail="not_found")
    return tx


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    year: int = Query(...),
    month: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    base = db.query(Transaction).filter(
        Transaction.household_id == hh_id,
        extract("year", Transaction.date) == year,
        extract("month", Transaction.date) == month,
    )
    income = base.filter(Transaction.transaction_type == "income").with_entities(
        func.sum(Transaction.amount)
    ).scalar() or Decimal("0")
    expenses = base.filter(Transaction.transaction_type == "expense").with_entities(
        func.sum(Transaction.amount)
    ).scalar() or Decimal("0")
    return SummaryResponse(
        income=f"{income:.2f}",
        expenses=f"{expenses:.2f}",
        balance=f"{income + expenses:.2f}",
    )


@router.post("/transfer", response_model=list[TransactionResponse], status_code=status.HTTP_201_CREATED)
async def create_transfer(
    body: TransferCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    now = datetime.now(timezone.utc)
    debit = Transaction(
        household_id=hh_id, account_id=body.from_account_id, category_id=None,
        amount=-abs(body.amount), date=body.date, description=body.description,
        transaction_type="transfer", created_at=now, updated_at=now,
    )
    credit = Transaction(
        household_id=hh_id, account_id=body.to_account_id, category_id=None,
        amount=abs(body.amount), date=body.date, description=body.description,
        transaction_type="transfer", created_at=now, updated_at=now,
    )
    db.add(debit)
    db.add(credit)
    db.flush()
    debit.transfer_peer_id = credit.id
    credit.transfer_peer_id = debit.id
    db.commit()
    db.refresh(debit)
    db.refresh(credit)
    return [debit, credit]


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    year: int = Query(...),
    month: int = Query(...),
    account_id: int | None = Query(default=None),
    category_id: int | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    q = db.query(Transaction).filter(
        Transaction.household_id == hh_id,
        extract("year", Transaction.date) == year,
        extract("month", Transaction.date) == month,
    )
    if account_id is not None:
        q = q.filter(Transaction.account_id == account_id)
    if category_id is not None:
        q = q.filter(Transaction.category_id == category_id)
    return q.order_by(Transaction.date.desc(), Transaction.id.desc()).all()


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    now = datetime.now(timezone.utc)
    tx = Transaction(
        household_id=hh_id, account_id=body.account_id, category_id=body.category_id,
        amount=_apply_sign(body.amount, body.transaction_type),
        date=body.date, description=body.description,
        transaction_type=body.transaction_type, created_at=now, updated_at=now,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/{tx_id}", response_model=TransactionResponse)
async def get_transaction(
    tx_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    return _get_tx(db, tx_id, hh_id)


@router.patch("/{tx_id}", response_model=TransactionResponse)
async def update_transaction(
    tx_id: int,
    body: TransactionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    tx = _get_tx(db, tx_id, hh_id)
    if tx.transaction_type == "transfer":
        raise HTTPException(status_code=405, detail="cannot_patch_transfer")
    for field, val in body.model_dump(exclude_unset=True).items():
        if field == "amount" and val is not None:
            val = _apply_sign(val, tx.transaction_type)
        setattr(tx, field, val)
    tx.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    tx_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    tx = _get_tx(db, tx_id, hh_id)
    if tx.transfer_peer_id is not None:
        peer = db.get(Transaction, tx.transfer_peer_id)
        if peer:
            db.delete(peer)
    db.delete(tx)
    db.commit()
