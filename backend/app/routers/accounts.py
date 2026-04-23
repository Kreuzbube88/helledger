from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.household import Account
from app.models.transaction import Transaction
from app.schemas.accounts import AccountCreate, AccountUpdate, AccountResponse
from app.schemas.transaction import BalanceResponse

router = APIRouter(prefix="/accounts")


def _require_active_hh(user: User) -> int:
    if user.active_household_id is None:
        raise HTTPException(status_code=400, detail="no_active_household")
    return user.active_household_id


def _get_account(account_id: int, hh_id: int, db: Session) -> Account:
    acc = db.get(Account, account_id)
    if acc is None or acc.household_id != hh_id:
        raise HTTPException(status_code=404, detail="not_found")
    return acc


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    include_archived: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    q = db.query(Account).filter(Account.household_id == hh_id)
    if not include_archived:
        q = q.filter(Account.archived.is_(False))
    return q.all()


@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(
    body: AccountCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    now = datetime.now(timezone.utc)
    acc = Account(
        household_id=hh_id,
        name=body.name,
        account_type=body.account_type,
        starting_balance=body.starting_balance,
        currency=body.currency,
        created_at=now,
        updated_at=now,
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


@router.get("/balances", response_model=list[BalanceResponse])
async def get_balances(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    accounts = db.query(Account).filter(Account.household_id == hh_id).all()

    tx_sums = (
        db.query(Transaction.account_id, func.sum(Transaction.amount))
        .filter(Transaction.household_id == hh_id)
        .group_by(Transaction.account_id)
        .all()
    )
    sum_map: dict[int, Decimal] = {acc_id: amt for acc_id, amt in tx_sums}

    result = []
    for acc in accounts:
        tx_total = sum_map.get(acc.id, Decimal("0"))
        balance = (acc.starting_balance or Decimal("0")) + tx_total
        result.append(BalanceResponse(
            id=acc.id, name=acc.name, account_type=acc.account_type,
            account_role=acc.account_role,
            balance=f"{balance:.2f}", currency=acc.currency, archived=acc.archived,
        ))
    return result


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    return _get_account(account_id, hh_id, db)


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    body: AccountUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    acc = _get_account(account_id, hh_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(acc, field, value)
    acc.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(acc)
    return acc


@router.delete("/{account_id}", status_code=204)
async def archive_account(
    account_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    acc = _get_account(account_id, hh_id, db)
    acc.archived = True
    acc.updated_at = datetime.now(timezone.utc)
    db.commit()
