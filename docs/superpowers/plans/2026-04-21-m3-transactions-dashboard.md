# M3: Transactions + Monthly Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement M3 — transaction CRUD with transfer support, monthly Soll/Ist dashboard, and Cinema Dark + Glassmorphism WOW-design frontend. Zero browser dialogs (alert/confirm/prompt). Toast always bottom-right.

**Architecture:** Backend: Transaction model + migration, transactions router (CRUD + transfer), soll-ist on categories router, balances on accounts router. Frontend: CSS design tokens in index.html, toast.js + animations.js utilities, rewrite dashboard.js, new transactions.js. All views built via DOM API (createElement + appendChild), no innerHTML assignments.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Decimal. Frontend: Vanilla JS modules, Tailwind CDN, custom CSS vars.

**Spec:** `docs/superpowers/specs/2026-04-21-m3-transactions-dashboard-design.md`

---

## Context

M2 complete. M3 adds the transaction layer. Key decisions locked in spec:
- Transfers = two linked rows, self-referential `transfer_peer_id` FK
- Transfers exempt from `category_id`; income/expense must have it
- PATCH on transfer rows → HTTP 405; DELETE → deletes peer too
- Signed amounts: income=+, expense=-, transfer: -amount source / +amount target
- Three dashboard endpoints: `/transactions/summary`, `/categories/soll-ist`, `/accounts/balances`
- WOW design: Cinema Dark + Glassmorphism, spring animations, count-up numbers
- No `window.alert/confirm/prompt` anywhere — use `toast()` and `confirmDialog()`

---

## File Structure

**Create:**
- `backend/app/models/transaction.py`
- `backend/app/schemas/transaction.py`
- `backend/app/routers/transactions.py`
- `backend/alembic/versions/003_transactions.py`
- `backend/tests/test_transactions.py`
- `frontend/js/toast.js`
- `frontend/js/animations.js`
- `frontend/js/views/transactions.js`

**Modify:**
- `backend/app/models/__init__.py`
- `backend/app/routers/categories.py` (add soll-ist endpoint before `/{category_id}`)
- `backend/app/routers/accounts.py` (add balances endpoint before `/{account_id}`)
- `backend/app/main.py` (include transactions router)
- `frontend/index.html` (design tokens, ambient blobs, register transactions route)
- `frontend/js/nav.js` (add transactions link)
- `frontend/js/views/dashboard.js` (full rewrite)
- `frontend/locales/de.json`
- `frontend/locales/en.json`

---

## Task 1: Transaction Model + Migration

**Files:**
- Create: `backend/app/models/transaction.py`
- Create: `backend/alembic/versions/003_transactions.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write `backend/app/models/transaction.py`**

```python
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Numeric, String, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import mapped_column, Mapped
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), index=True, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    date: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str] = mapped_column(String(255))
    transaction_type: Mapped[str] = mapped_column(String(20))
    transfer_peer_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
```

- [ ] **Step 2: Update `backend/app/models/__init__.py`**

```python
from app.models.user import User, RefreshToken
from app.models.household import Household, HouseholdMember
from app.models.account import Account
from app.models.category import Category, ExpectedValue, Budget
from app.models.transaction import Transaction

__all__ = ["User", "RefreshToken", "Household", "HouseholdMember", "Account", "Category", "ExpectedValue", "Budget", "Transaction"]
```

- [ ] **Step 3: Write `backend/alembic/versions/003_transactions.py`**

```python
"""transactions table

Revision ID: 003
Revises: 002
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("transaction_type", sa.String(20), nullable=False),
        sa.Column("transfer_peer_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transfer_peer_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_household_id", "transactions", ["household_id"])
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_index("ix_transactions_category_id", "transactions", ["category_id"])
    op.create_index("ix_transactions_date", "transactions", ["date"])


def downgrade() -> None:
    op.drop_index("ix_transactions_date", table_name="transactions")
    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_index("ix_transactions_account_id", table_name="transactions")
    op.drop_index("ix_transactions_household_id", table_name="transactions")
    op.drop_table("transactions")
```

- [ ] **Step 4: Run migration**

```bash
cd backend
SECRET_KEY=test alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade 002 -> 003`

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/transaction.py backend/app/models/__init__.py backend/alembic/versions/003_transactions.py
git commit -m "feat: add transaction model and migration"
```

---

## Task 2: Transaction Schemas

**Files:**
- Create: `backend/app/schemas/transaction.py`

- [ ] **Step 1: Write `backend/app/schemas/transaction.py`**

```python
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, model_validator, field_serializer


class TransactionCreate(BaseModel):
    account_id: int
    category_id: int | None = None
    amount: Decimal
    date: date
    description: str
    transaction_type: str

    @model_validator(mode="after")
    def validate_category(self) -> "TransactionCreate":
        if self.transaction_type in ("income", "expense") and self.category_id is None:
            raise ValueError("category_id required for income and expense transactions")
        return self


class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal
    date: date
    description: str


class TransactionUpdate(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    amount: Decimal | None = None
    date: date | None = None
    description: str | None = None
    transaction_type: str | None = None


class TransactionResponse(BaseModel):
    id: int
    household_id: int
    account_id: int
    category_id: int | None
    amount: Decimal
    date: date
    description: str
    transaction_type: str
    transfer_peer_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal) -> str:
        return f"{v:.2f}"


class SummaryResponse(BaseModel):
    income: str
    expenses: str
    balance: str


class BalanceResponse(BaseModel):
    id: int
    name: str
    account_type: str
    balance: str
    currency: str
    archived: bool


class SollIstNode(BaseModel):
    id: int
    name: str
    category_type: str
    soll: str
    ist: str
    diff: str
    children: list["SollIstNode"] = []


SollIstNode.model_rebuild()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/transaction.py
git commit -m "feat: add transaction schemas"
```

---

## Task 3: Transaction Router + Tests

**Files:**
- Create: `backend/tests/test_transactions.py`
- Create: `backend/app/routers/transactions.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write `backend/tests/test_transactions.py`**

```python
import pytest


def _acc(client, name="Checking", account_type="checking"):
    return client.post("/api/accounts", json={
        "name": name, "account_type": account_type,
        "initial_balance": "0.00", "currency": "EUR",
    }).json()


def _cat(client, name="Food", category_type="variable"):
    return client.post("/api/categories", json={"name": name, "category_type": category_type}).json()


def _tx(client, **kwargs):
    defaults = {
        "account_id": None, "category_id": None,
        "amount": "50.00", "date": "2026-04-01",
        "description": "Test", "transaction_type": "expense",
    }
    defaults.update(kwargs)
    return client.post("/api/transactions", json=defaults)


def test_create_expense(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client)
    r = _tx(registered_client, account_id=acc["id"], category_id=cat["id"])
    assert r.status_code == 201
    body = r.json()
    assert body["amount"] == "-50.00"
    assert body["transaction_type"] == "expense"


def test_create_income(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client, category_type="income")
    r = _tx(registered_client, account_id=acc["id"], category_id=cat["id"], transaction_type="income")
    assert r.status_code == 201
    assert r.json()["amount"] == "50.00"


def test_expense_requires_category(registered_client):
    acc = _acc(registered_client)
    r = _tx(registered_client, account_id=acc["id"], category_id=None, transaction_type="expense")
    assert r.status_code == 422


def test_create_transfer(registered_client):
    acc1 = _acc(registered_client, "Acc1")
    acc2 = _acc(registered_client, "Acc2")
    r = registered_client.post("/api/transactions/transfer", json={
        "from_account_id": acc1["id"], "to_account_id": acc2["id"],
        "amount": "100.00", "date": "2026-04-01", "description": "Transfer",
    })
    assert r.status_code == 201
    rows = r.json()
    assert len(rows) == 2
    debit = next(x for x in rows if x["account_id"] == acc1["id"])
    credit = next(x for x in rows if x["account_id"] == acc2["id"])
    assert debit["amount"] == "-100.00"
    assert credit["amount"] == "100.00"
    assert debit["transfer_peer_id"] == credit["id"]
    assert credit["transfer_peer_id"] == debit["id"]


def test_patch_transfer_is_405(registered_client):
    acc1 = _acc(registered_client, "A1")
    acc2 = _acc(registered_client, "A2")
    rows = registered_client.post("/api/transactions/transfer", json={
        "from_account_id": acc1["id"], "to_account_id": acc2["id"],
        "amount": "50.00", "date": "2026-04-01", "description": "x",
    }).json()
    tx_id = rows[0]["id"]
    r = registered_client.patch(f"/api/transactions/{tx_id}", json={"description": "new"})
    assert r.status_code == 405


def test_delete_transfer_removes_both(registered_client):
    acc1 = _acc(registered_client, "A1")
    acc2 = _acc(registered_client, "A2")
    rows = registered_client.post("/api/transactions/transfer", json={
        "from_account_id": acc1["id"], "to_account_id": acc2["id"],
        "amount": "50.00", "date": "2026-04-01", "description": "x",
    }).json()
    tx_id = rows[0]["id"]
    peer_id = rows[0]["transfer_peer_id"]
    r = registered_client.delete(f"/api/transactions/{tx_id}")
    assert r.status_code == 204
    assert registered_client.get(f"/api/transactions/{peer_id}").status_code == 404


def test_list_transactions_month_filter(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client)
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"], date="2026-04-01")
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"], date="2026-03-15")
    r = registered_client.get("/api/transactions?year=2026&month=4")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_summary(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client)
    inc_cat = _cat(registered_client, "Salary", "income")
    _tx(registered_client, account_id=acc["id"], category_id=inc_cat["id"],
        amount="1000.00", transaction_type="income", date="2026-04-10")
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="200.00", transaction_type="expense", date="2026-04-15")
    r = registered_client.get("/api/transactions/summary?year=2026&month=4")
    assert r.status_code == 200
    body = r.json()
    assert body["income"] == "1000.00"
    assert body["expenses"] == "-200.00"
    assert body["balance"] == "800.00"


def test_soll_ist(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client, "Lebensmittel", "variable")
    registered_client.post(f"/api/categories/{cat['id']}/budget",
        json={"amount": "300.00", "valid_from": "2026-01-01"})
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="120.00", transaction_type="expense", date="2026-04-05")
    r = registered_client.get("/api/categories/soll-ist?year=2026&month=4")
    assert r.status_code == 200
    nodes = r.json()
    node = next(n for n in nodes if n["id"] == cat["id"])
    assert node["soll"] == "300.00"
    assert node["ist"] == "-120.00"


def test_balances(registered_client):
    acc = _acc(registered_client, "Main")
    cat = _cat(registered_client)
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="100.00", transaction_type="expense", date="2026-04-01")
    r = registered_client.get("/api/accounts/balances")
    assert r.status_code == 200
    balances = r.json()
    acc_bal = next(b for b in balances if b["id"] == acc["id"])
    assert acc_bal["balance"] == "-100.00"
```

- [ ] **Step 2: Run — expect failure**

```bash
cd backend && pytest tests/test_transactions.py -v
```

Expected: ERRORS — router not registered

- [ ] **Step 3: Write `backend/app/routers/transactions.py`**

```python
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
```

- [ ] **Step 4: Register router in `backend/app/main.py`**

Add after existing router includes (before the static mount):
```python
from app.routers import transactions as tx_router
app.include_router(tx_router.router, prefix="/api")
```

- [ ] **Step 5: Run tests**

```bash
cd backend && pytest tests/test_transactions.py -v
```

Expected: all PASSED (skip soll-ist and balances tests — those need Task 4)

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/transactions.py backend/tests/test_transactions.py backend/app/main.py
git commit -m "feat: add transaction router with CRUD and transfer support"
```

---

## Task 4: Dashboard API Endpoints (Soll/Ist + Balances)

**Files:**
- Modify: `backend/app/routers/categories.py` (add soll-ist before `/{category_id}`)
- Modify: `backend/app/routers/accounts.py` (add balances before `/{account_id}`)

- [ ] **Step 1: Add imports to `backend/app/routers/categories.py`**

Add at top of the file alongside existing imports:
```python
import calendar
from decimal import Decimal
from datetime import date as date_type
from sqlalchemy import extract, or_, func
from fastapi import Query
from app.models.transaction import Transaction
from app.models.category import ExpectedValue, Budget
from app.schemas.transaction import SollIstNode
```

- [ ] **Step 2: Add soll-ist endpoint to `backend/app/routers/categories.py`**

Insert this route BEFORE any `/{category_id}` routes (FastAPI matches literal paths before parameterized ones):

```python
@router.get("/soll-ist", response_model=list[SollIstNode])
async def get_soll_ist(
    year: int = Query(...),
    month: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    first_day = date_type(year, month, 1)

    cats = db.query(Category).filter(
        Category.household_id == hh_id,
        Category.archived.is_(False),
    ).all()

    cat_ids = [c.id for c in cats]

    tx_rows = (
        db.query(Transaction.category_id, func.sum(Transaction.amount))
        .filter(
            Transaction.household_id == hh_id,
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == month,
            Transaction.transaction_type.in_(["income", "expense"]),
            Transaction.category_id.isnot(None),
        )
        .group_by(Transaction.category_id)
        .all()
    )
    tx_map: dict[int, Decimal] = {cat_id: amt for cat_id, amt in tx_rows}

    ev_rows = db.query(ExpectedValue).filter(
        ExpectedValue.category_id.in_(cat_ids),
        ExpectedValue.valid_from <= first_day,
        or_(ExpectedValue.valid_until.is_(None), ExpectedValue.valid_until >= first_day),
    ).all()
    ev_map: dict[int, Decimal] = {ev.category_id: ev.monthly_amount for ev in ev_rows}

    budget_rows = db.query(Budget).filter(
        Budget.category_id.in_(cat_ids),
        Budget.valid_from <= first_day,
        or_(Budget.valid_until.is_(None), Budget.valid_until >= first_day),
    ).all()
    budget_map: dict[int, Decimal] = {b.category_id: b.amount for b in budget_rows}

    def _build(parent_id: int | None) -> list[SollIstNode]:
        result = []
        for cat in cats:
            if cat.parent_id != parent_id:
                continue
            children = _build(cat.id)
            ist_self = tx_map.get(cat.id, Decimal("0"))
            ist_children = sum(Decimal(c.ist) for c in children)
            ist = ist_self + ist_children
            soll_self = ev_map.get(cat.id) or budget_map.get(cat.id) or Decimal("0")
            soll_children = sum(Decimal(c.soll) for c in children)
            soll = soll_self if soll_self > Decimal("0") else soll_children
            result.append(SollIstNode(
                id=cat.id, name=cat.name, category_type=cat.category_type,
                soll=f"{soll:.2f}", ist=f"{ist:.2f}", diff=f"{soll - ist:.2f}",
                children=children,
            ))
        return result

    return _build(None)
```

- [ ] **Step 3: Add imports to `backend/app/routers/accounts.py`**

Add alongside existing imports:
```python
from decimal import Decimal
from sqlalchemy import func
from app.models.transaction import Transaction
from app.schemas.transaction import BalanceResponse
```

- [ ] **Step 4: Add balances endpoint to `backend/app/routers/accounts.py`**

Insert BEFORE any `/{account_id}` routes:

```python
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
        balance = (acc.initial_balance or Decimal("0")) + tx_total
        result.append(BalanceResponse(
            id=acc.id, name=acc.name, account_type=acc.account_type,
            balance=f"{balance:.2f}", currency=acc.currency, archived=acc.archived,
        ))
    return result
```

- [ ] **Step 5: Run all tests**

```bash
cd backend && pytest -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/categories.py backend/app/routers/accounts.py
git commit -m "feat: add soll-ist and account balances dashboard endpoints"
```

---

## Task 5: Locale Keys

**Files:**
- Modify: `frontend/locales/de.json`
- Modify: `frontend/locales/en.json`

- [ ] **Step 1: Replace `frontend/locales/de.json`**

```json
{
  "app": { "name": "HELLEDGER", "tagline": "Dein persönlicher Finanz-Tracker" },
  "nav": {
    "dashboard": "Dashboard",
    "accounts": "Konten",
    "categories": "Kategorien",
    "transactions": "Transaktionen",
    "settings": "Einstellungen",
    "logout": "Abmelden"
  },
  "auth": {
    "login": "Anmelden", "register": "Registrieren",
    "email": "E-Mail-Adresse", "password": "Passwort",
    "name": "Name", "noAccount": "Noch kein Konto?",
    "hasAccount": "Bereits ein Konto?",
    "loginTitle": "Willkommen zurück",
    "registerTitle": "Konto erstellen",
    "passwordHint": "Mindestens 12 Zeichen",
    "switchToRegister": "Registrieren",
    "switchToLogin": "Anmelden"
  },
  "errors": {
    "email_taken": "Diese E-Mail-Adresse ist bereits vergeben.",
    "invalid_credentials": "E-Mail oder Passwort falsch.",
    "registration_disabled": "Registrierung ist deaktiviert.",
    "generic": "Ein Fehler ist aufgetreten. Bitte versuche es erneut."
  },
  "dashboard": {
    "welcome": "Willkommen, {{name}}!",
    "empty": "Dein Dashboard ist noch leer.",
    "income": "Einnahmen",
    "expenses": "Ausgaben",
    "balance": "Bilanz",
    "sollIst": "Soll / Ist",
    "accounts": "Kontenübersicht",
    "noData": "Keine Daten für diesen Monat.",
    "addTransaction": "Transaktion hinzufügen",
    "soll": "Soll",
    "ist": "Ist",
    "diff": "Differenz"
  },
  "transactions": {
    "title": "Transaktionen",
    "add": "Transaktion hinzufügen",
    "addTransfer": "Umbuchung",
    "date": "Datum",
    "description": "Beschreibung",
    "account": "Konto",
    "category": "Kategorie",
    "amount": "Betrag",
    "type": "Typ",
    "income": "Einnahme",
    "expense": "Ausgabe",
    "transfer": "Umbuchung",
    "fromAccount": "Von Konto",
    "toAccount": "Zu Konto",
    "save": "Speichern",
    "cancel": "Abbrechen",
    "edit": "Bearbeiten",
    "delete": "Löschen",
    "confirmDelete": "Transaktion wirklich löschen?",
    "noData": "Keine Transaktionen gefunden.",
    "filterAccount": "Konto (alle)",
    "filterCategory": "Kategorie (alle)"
  },
  "accounts": {
    "title": "Konten", "add": "Konto hinzufügen",
    "name": "Name", "type": "Typ", "balance": "Startguthaben",
    "currency": "Währung", "status": "Status",
    "active": "Aktiv", "archived": "Archiviert",
    "archive": "Archivieren", "edit": "Bearbeiten",
    "save": "Speichern", "cancel": "Abbrechen",
    "types": { "checking": "Girokonto", "savings": "Sparkonto", "credit": "Kreditkonto" }
  },
  "categories": {
    "title": "Kategorien", "add": "Kategorie hinzufügen", "addSub": "Sub-Kategorie",
    "name": "Name", "type": "Typ", "color": "Farbe",
    "archive": "Archivieren", "edit": "Bearbeiten",
    "save": "Speichern", "cancel": "Abbrechen",
    "expectedValue": "Sollwert", "budget": "Budget",
    "newExpectedValue": "Neuen Sollwert setzen", "newBudget": "Neues Budget setzen",
    "amount": "Betrag", "validFrom": "Gültig ab", "noLimit": "Unbegrenzt",
    "sections": { "income": "Einnahmen", "fixed": "Fixkosten", "variable": "Variable Ausgaben" },
    "types": { "income": "Einnahme", "fixed": "Fixkosten", "variable": "Variable" }
  },
  "settings": {
    "title": "Einstellungen", "household": "Haushalt",
    "householdName": "Haushaltsname", "members": "Mitglieder",
    "addMember": "Mitglied hinzufügen", "memberEmail": "E-Mail-Adresse",
    "add": "Hinzufügen", "remove": "Entfernen",
    "roles": { "owner": "Eigentümer", "member": "Mitglied" },
    "save": "Speichern"
  },
  "lang": { "de": "Deutsch", "en": "English" }
}
```

- [ ] **Step 2: Replace `frontend/locales/en.json`**

```json
{
  "app": { "name": "HELLEDGER", "tagline": "Your personal finance tracker" },
  "nav": {
    "dashboard": "Dashboard",
    "accounts": "Accounts",
    "categories": "Categories",
    "transactions": "Transactions",
    "settings": "Settings",
    "logout": "Sign Out"
  },
  "auth": {
    "login": "Sign In", "register": "Create Account",
    "email": "Email address", "password": "Password",
    "name": "Full name", "noAccount": "Don't have an account?",
    "hasAccount": "Already have an account?",
    "loginTitle": "Welcome back",
    "registerTitle": "Create your account",
    "passwordHint": "At least 12 characters",
    "switchToRegister": "Create account",
    "switchToLogin": "Sign in"
  },
  "errors": {
    "email_taken": "This email address is already taken.",
    "invalid_credentials": "Invalid email or password.",
    "registration_disabled": "Registration is currently disabled.",
    "generic": "Something went wrong. Please try again."
  },
  "dashboard": {
    "welcome": "Welcome, {{name}}!",
    "empty": "Your dashboard is empty.",
    "income": "Income",
    "expenses": "Expenses",
    "balance": "Balance",
    "sollIst": "Budget vs. Actual",
    "accounts": "Account Balances",
    "noData": "No data for this month.",
    "addTransaction": "Add Transaction",
    "soll": "Budget",
    "ist": "Actual",
    "diff": "Difference"
  },
  "transactions": {
    "title": "Transactions",
    "add": "Add Transaction",
    "addTransfer": "Transfer",
    "date": "Date",
    "description": "Description",
    "account": "Account",
    "category": "Category",
    "amount": "Amount",
    "type": "Type",
    "income": "Income",
    "expense": "Expense",
    "transfer": "Transfer",
    "fromAccount": "From Account",
    "toAccount": "To Account",
    "save": "Save",
    "cancel": "Cancel",
    "edit": "Edit",
    "delete": "Delete",
    "confirmDelete": "Delete this transaction?",
    "noData": "No transactions found.",
    "filterAccount": "Account (all)",
    "filterCategory": "Category (all)"
  },
  "accounts": {
    "title": "Accounts", "add": "Add Account",
    "name": "Name", "type": "Type", "balance": "Initial Balance",
    "currency": "Currency", "status": "Status",
    "active": "Active", "archived": "Archived",
    "archive": "Archive", "edit": "Edit",
    "save": "Save", "cancel": "Cancel",
    "types": { "checking": "Checking", "savings": "Savings", "credit": "Credit" }
  },
  "categories": {
    "title": "Categories", "add": "Add Category", "addSub": "Sub-Category",
    "name": "Name", "type": "Type", "color": "Color",
    "archive": "Archive", "edit": "Edit",
    "save": "Save", "cancel": "Cancel",
    "expectedValue": "Expected Value", "budget": "Budget",
    "newExpectedValue": "Set New Expected Value", "newBudget": "Set New Budget",
    "amount": "Amount", "validFrom": "Valid From", "noLimit": "No Limit",
    "sections": { "income": "Income", "fixed": "Fixed Costs", "variable": "Variable Expenses" },
    "types": { "income": "Income", "fixed": "Fixed", "variable": "Variable" }
  },
  "settings": {
    "title": "Settings", "household": "Household",
    "householdName": "Household Name", "members": "Members",
    "addMember": "Add Member", "memberEmail": "Email address",
    "add": "Add", "remove": "Remove",
    "roles": { "owner": "Owner", "member": "Member" },
    "save": "Save"
  },
  "lang": { "de": "Deutsch", "en": "English" }
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/locales/de.json frontend/locales/en.json
git commit -m "feat: add M3 locale keys (dashboard, transactions)"
```

---

## Task 6: toast.js

**Files:**
- Create: `frontend/js/toast.js`

- [ ] **Step 1: Write `frontend/js/toast.js`**

```javascript
let _container = null;

function _ensureContainer() {
    if (_container && document.body.contains(_container)) return _container;
    _container = document.createElement("div");
    _container.id = "toast-container";
    Object.assign(_container.style, {
        position: "fixed",
        bottom: "1.5rem",
        right: "1.5rem",
        zIndex: "9999",
        display: "flex",
        flexDirection: "column",
        gap: "0.5rem",
        alignItems: "flex-end",
    });
    document.body.appendChild(_container);
    return _container;
}

export function toast(message, type = "success") {
    const container = _ensureContainer();
    const colors = {
        success: { bg: "rgba(16,185,129,0.15)", border: "rgba(16,185,129,0.4)", dot: "#10b981" },
        error:   { bg: "rgba(244,63,94,0.15)",  border: "rgba(244,63,94,0.4)",  dot: "#f43f5e" },
        info:    { bg: "rgba(99,102,241,0.15)",  border: "rgba(99,102,241,0.4)", dot: "#818cf8" },
    };
    const c = colors[type] ?? colors.info;

    const el = document.createElement("div");
    Object.assign(el.style, {
        background: c.bg,
        border: `1px solid ${c.border}`,
        color: "#e2e8f0",
        borderRadius: "0.75rem",
        padding: "0.75rem 1.25rem",
        fontSize: "0.875rem",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
        maxWidth: "22rem",
        opacity: "0",
        transform: "translateY(8px)",
        transition: "opacity 0.25s ease, transform 0.25s ease",
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        cursor: "pointer",
    });

    const dot = document.createElement("span");
    Object.assign(dot.style, {
        width: "6px", height: "6px", borderRadius: "50%",
        background: c.dot, flexShrink: "0",
    });

    const msg = document.createElement("span");
    msg.textContent = message;

    el.appendChild(dot);
    el.appendChild(msg);
    container.appendChild(el);

    requestAnimationFrame(() => {
        el.style.opacity = "1";
        el.style.transform = "translateY(0)";
    });

    const dismiss = () => {
        el.style.opacity = "0";
        el.style.transform = "translateY(8px)";
        setTimeout(() => el.remove(), 250);
    };
    el.addEventListener("click", dismiss);
    setTimeout(dismiss, 3500);
}

export function confirmDialog(message, onConfirm, confirmLabel) {
    const label = confirmLabel ?? (typeof t !== "undefined" ? t("transactions.delete") : "Löschen");

    const overlay = document.createElement("div");
    Object.assign(overlay.style, {
        position: "fixed", inset: "0",
        background: "rgba(0,0,0,0.65)",
        backdropFilter: "blur(4px)", WebkitBackdropFilter: "blur(4px)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: "10000", opacity: "0", transition: "opacity 0.2s ease",
    });

    const box = document.createElement("div");
    Object.assign(box.style, {
        background: "rgba(15,15,20,0.97)",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: "1.25rem",
        padding: "2rem",
        maxWidth: "24rem",
        width: "90%",
        transform: "scale(0.9) translateY(12px)",
        transition: "transform 0.3s cubic-bezier(0.34,1.56,0.64,1), opacity 0.2s ease",
        opacity: "0",
    });

    const msgEl = document.createElement("p");
    Object.assign(msgEl.style, {
        color: "#e2e8f0", marginBottom: "1.5rem",
        fontSize: "1rem", lineHeight: "1.5",
    });
    msgEl.textContent = message;

    const btns = document.createElement("div");
    btns.style.cssText = "display:flex;gap:0.75rem;justify-content:flex-end;";

    const cancelBtn = document.createElement("button");
    Object.assign(cancelBtn.style, {
        padding: "0.5rem 1.25rem", borderRadius: "0.5rem",
        border: "1px solid rgba(255,255,255,0.15)",
        background: "transparent", color: "#94a3b8",
        cursor: "pointer", fontSize: "0.875rem",
        transition: "background 0.15s",
    });
    cancelBtn.textContent = typeof t !== "undefined" ? t("transactions.cancel") : "Abbrechen";

    const confirmBtn = document.createElement("button");
    Object.assign(confirmBtn.style, {
        padding: "0.5rem 1.25rem", borderRadius: "0.5rem",
        border: "none", background: "rgba(244,63,94,0.9)",
        color: "white", cursor: "pointer",
        fontSize: "0.875rem", fontWeight: "500",
        transition: "background 0.15s",
    });
    confirmBtn.textContent = label;

    btns.appendChild(cancelBtn);
    btns.appendChild(confirmBtn);
    box.appendChild(msgEl);
    box.appendChild(btns);
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    requestAnimationFrame(() => {
        overlay.style.opacity = "1";
        box.style.transform = "scale(1) translateY(0)";
        box.style.opacity = "1";
    });

    const close = () => {
        overlay.style.opacity = "0";
        box.style.transform = "scale(0.95) translateY(8px)";
        box.style.opacity = "0";
        setTimeout(() => overlay.remove(), 250);
    };

    cancelBtn.addEventListener("click", close);
    overlay.addEventListener("click", (e) => { if (e.target === overlay) close(); });
    confirmBtn.addEventListener("click", () => { close(); onConfirm(); });
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/js/toast.js
git commit -m "feat: add toast and confirmDialog utilities (no browser dialogs)"
```

---

## Task 7: animations.js

**Files:**
- Create: `frontend/js/animations.js`

- [ ] **Step 1: Write `frontend/js/animations.js`**

```javascript
function expoOut(t) {
    return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
}

export function countUp(el, targetStr, duration = 700) {
    const target = parseFloat(targetStr);
    if (isNaN(target)) { el.textContent = targetStr; return; }
    const start = performance.now();
    const abs = Math.abs(target);
    const sign = target < 0 ? "-" : target > 0 ? "+" : "";

    function tick(now) {
        const p = Math.min((now - start) / duration, 1);
        const val = expoOut(p) * abs;
        el.textContent = `${sign}${val.toFixed(2).replace(".", ",")} €`;
        if (p < 1) requestAnimationFrame(tick);
        else el.textContent = `${sign}${abs.toFixed(2).replace(".", ",")} €`;
    }
    requestAnimationFrame(tick);
}

export function animateProgressBars(container) {
    const bars = container.querySelectorAll("[data-pct]");
    bars.forEach((bar, i) => {
        const pct = Math.min(parseFloat(bar.dataset.pct) || 0, 100);
        bar.style.width = "0%";
        setTimeout(() => {
            bar.style.transition = "width 0.6s cubic-bezier(0.16,1,0.3,1)";
            bar.style.width = `${pct}%`;
        }, i * 30);
    });
}

export function fadeInUp(elements, stagger = 30) {
    const els = elements instanceof NodeList ? Array.from(elements) : [elements];
    els.forEach((el, i) => {
        el.style.opacity = "0";
        el.style.transform = "translateY(12px)";
        el.style.transition = "opacity 0.35s ease, transform 0.35s ease";
        setTimeout(() => {
            el.style.opacity = "1";
            el.style.transform = "translateY(0)";
        }, i * stagger);
    });
}

export async function crossfade(el, loadFn) {
    el.style.transition = "opacity 0.18s ease, transform 0.18s ease";
    el.style.opacity = "0";
    el.style.transform = "translateY(-6px)";
    await new Promise(r => setTimeout(r, 200));
    await loadFn();
    el.style.transform = "translateY(6px)";
    requestAnimationFrame(() => {
        el.style.transition = "opacity 0.25s ease, transform 0.25s ease";
        el.style.opacity = "1";
        el.style.transform = "translateY(0)";
    });
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/js/animations.js
git commit -m "feat: add animation utilities (countUp, progressBars, fadeInUp, crossfade)"
```

---

## Task 8: index.html + nav.js Updates

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/js/nav.js`

- [ ] **Step 1: Replace `frontend/index.html`**

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HELLEDGER</title>
  <link rel="manifest" href="/manifest.json">
  <meta name="theme-color" content="#6366f1">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>tailwind.config = { darkMode: 'class', theme: { extend: {} } }</script>
  <style>
    :root {
      --surface: rgba(255,255,255,0.05);
      --border: rgba(255,255,255,0.08);
      --accent: #6366f1;
      --accent-glow: rgba(99,102,241,0.25);
      --income: #10b981;
      --expense: #f43f5e;
      --transfer: #8b5cf6;
      --easing: cubic-bezier(0.16,1,0.3,1);
      --easing-spring: cubic-bezier(0.34,1.56,0.64,1);
    }
    * { box-sizing: border-box; }
    body {
      background: linear-gradient(135deg, #020203 0%, #0a0a0f 50%, #020203 100%);
      background-attachment: fixed;
      font-variant-numeric: tabular-nums;
    }
    .blob {
      position: fixed; border-radius: 50%; pointer-events: none;
      filter: blur(60px); z-index: 0;
    }
    .glass {
      background: var(--surface);
      border: 1px solid var(--border);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }
    .glow-accent { box-shadow: 0 0 40px var(--accent-glow); }
    @keyframes blobA {
      0%   { transform: translate(0,0) scale(1); }
      100% { transform: translate(60px,40px) scale(1.1); }
    }
    @keyframes blobB {
      0%   { transform: translate(0,0) scale(1.05); }
      100% { transform: translate(-40px,60px) scale(0.95); }
    }
  </style>
</head>
<body class="bg-gray-950 antialiased min-h-dvh">
  <div class="blob" style="background:radial-gradient(circle,rgba(99,102,241,0.09),transparent 70%);width:700px;height:700px;top:-200px;left:-150px;animation:blobA 18s ease-in-out infinite alternate;"></div>
  <div class="blob" style="background:radial-gradient(circle,rgba(139,92,246,0.07),transparent 70%);width:600px;height:600px;bottom:-150px;right:-100px;animation:blobB 22s ease-in-out infinite alternate;"></div>

  <div id="app" style="position:relative;z-index:1;">
    <div class="min-h-dvh flex items-center justify-center">
      <div class="text-indigo-400 text-xl font-bold animate-pulse">HELLEDGER</div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/i18next@23.10.1/dist/umd/i18next.min.js"></script>

  <script type="module">
    import { initI18n } from "/js/i18n.js";
    import { initRouter, route } from "/js/router.js";
    import { renderLogin } from "/js/views/login.js";
    import { renderDashboard } from "/js/views/dashboard.js";
    import { renderAccounts } from "/js/views/accounts.js";
    import { renderCategories } from "/js/views/categories.js";
    import { renderSettings } from "/js/views/settings.js";
    import { renderTransactions } from "/js/views/transactions.js";

    await initI18n();

    route("#/login", renderLogin);
    route("#/register", renderLogin);
    route("#/dashboard", renderDashboard);
    route("#/accounts", renderAccounts);
    route("#/categories", renderCategories);
    route("#/settings", renderSettings);
    route("#/transactions", renderTransactions);

    initRouter();

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/service-worker.js").catch(() => {});
    }
  </script>
</body>
</html>
```

- [ ] **Step 2: Add `"transactions"` to nav pages in `frontend/js/nav.js`**

Find the navLinks array (line ~45):
```javascript
const navLinks = ["dashboard", "accounts", "categories", "settings"].map((page) => {
```

Replace with:
```javascript
const navLinks = ["dashboard", "accounts", "categories", "transactions", "settings"].map((page) => {
```

- [ ] **Step 3: Commit**

```bash
git add frontend/index.html frontend/js/nav.js
git commit -m "feat: add design tokens, ambient blobs, and transactions nav link"
```

---

## Task 9: dashboard.js Rewrite (WOW Design)

**Files:**
- Rewrite: `frontend/js/views/dashboard.js`

The dashboard uses Cinema Dark + Glassmorphism. All DOM is built via `createElement` + `appendChild`. No user data goes into HTML string templates — all user content is set via `textContent`.

- [ ] **Step 1: Replace `frontend/js/views/dashboard.js`**

```javascript
import { getCurrentUser } from "../auth.js";
import { navigate } from "../router.js";
import { renderNav } from "../nav.js";
import { api } from "../api.js";
import { toast } from "../toast.js";
import { countUp, animateProgressBars, fadeInUp, crossfade } from "../animations.js";

let _year = new Date().getFullYear();
let _month = new Date().getMonth() + 1;

function _monthLabel(year, month) {
    return new Date(year, month - 1, 1).toLocaleDateString(
        document.documentElement.lang === "de" ? "de-DE" : "en-US",
        { month: "long", year: "numeric" }
    );
}

function _buildSollIstRow(node, depth) {
    const row = document.createElement("div");
    row.style.cssText = `padding:0.75rem 1rem 0.75rem ${depth * 16 + 16}px;border-bottom:1px solid rgba(255,255,255,0.04);`;

    const pct = parseFloat(node.soll) > 0
        ? Math.min(100, Math.abs(parseFloat(node.ist) / parseFloat(node.soll) * 100))
        : 0;
    const over = pct >= 100;

    const top = document.createElement("div");
    top.style.cssText = "display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;";

    const nameEl = document.createElement("span");
    nameEl.style.cssText = "font-size:0.875rem;color:#cbd5e1;";
    nameEl.textContent = node.name;

    const vals = document.createElement("div");
    vals.style.cssText = "display:flex;gap:1.5rem;font-size:0.8rem;font-variant-numeric:tabular-nums;";

    const istEl = document.createElement("span");
    istEl.style.color = over ? "#f43f5e" : "#e2e8f0";
    istEl.textContent = `${parseFloat(node.ist).toFixed(2).replace(".", ",")} €`;

    const sollEl = document.createElement("span");
    sollEl.style.color = "#64748b";
    sollEl.textContent = `/ ${parseFloat(node.soll).toFixed(2).replace(".", ",")} €`;

    vals.appendChild(istEl);
    vals.appendChild(sollEl);
    top.appendChild(nameEl);
    top.appendChild(vals);

    const barBg = document.createElement("div");
    barBg.style.cssText = "height:3px;border-radius:2px;background:rgba(255,255,255,0.06);overflow:hidden;";
    const bar = document.createElement("div");
    bar.style.cssText = "height:100%;border-radius:2px;";
    bar.dataset.pct = String(pct);
    bar.style.background = over
        ? "linear-gradient(90deg,#f97316,#f43f5e)"
        : "linear-gradient(90deg,#6366f1,#10b981)";
    barBg.appendChild(bar);
    row.appendChild(top);
    row.appendChild(barBg);

    if (node.children && node.children.length > 0) {
        node.children.forEach(child => row.appendChild(_buildSollIstRow(child, depth + 1)));
    }
    return row;
}

async function _loadDashboard(mainEl) {
    const [summaryRes, sollIstRes, balancesRes] = await Promise.all([
        api.get(`/transactions/summary?year=${_year}&month=${_month}`),
        api.get(`/categories/soll-ist?year=${_year}&month=${_month}`),
        api.get("/accounts/balances"),
    ]);
    if (!summaryRes.ok || !sollIstRes.ok || !balancesRes.ok) {
        toast(t("errors.generic"), "error");
        return;
    }
    const summary = await summaryRes.json();
    const sollIst = await sollIstRes.json();
    const balances = await balancesRes.json();

    const monthLabel = mainEl.querySelector("#dash-month-label");
    if (monthLabel) monthLabel.textContent = _monthLabel(_year, _month);

    const incEl = mainEl.querySelector("#dash-income");
    const expEl = mainEl.querySelector("#dash-expenses");
    const balEl = mainEl.querySelector("#dash-balance");
    if (incEl) countUp(incEl, summary.income);
    if (expEl) countUp(expEl, summary.expenses);
    if (balEl) countUp(balEl, summary.balance);

    const sollIstBox = mainEl.querySelector("#dash-soll-ist");
    if (sollIstBox) {
        sollIstBox.textContent = "";
        if (sollIst.length === 0) {
            const empty = document.createElement("p");
            empty.style.cssText = "color:#475569;font-size:0.875rem;padding:1.5rem;text-align:center;";
            empty.textContent = t("dashboard.noData");
            sollIstBox.appendChild(empty);
        } else {
            sollIst.forEach(node => sollIstBox.appendChild(_buildSollIstRow(node, 0)));
            animateProgressBars(sollIstBox);
        }
    }

    const balBox = mainEl.querySelector("#dash-balances");
    if (balBox) {
        balBox.textContent = "";
        balances.forEach(acc => {
            const card = document.createElement("div");
            card.className = "glass";
            card.style.cssText = "border-radius:0.75rem;padding:0.875rem 1rem;display:flex;justify-content:space-between;align-items:center;";
            const nameEl = document.createElement("span");
            nameEl.style.cssText = "font-size:0.875rem;color:#94a3b8;";
            nameEl.textContent = acc.name;
            const valEl = document.createElement("span");
            const bal = parseFloat(acc.balance);
            valEl.style.cssText = `font-size:0.9rem;font-weight:600;color:${bal >= 0 ? "#10b981" : "#f43f5e"};`;
            valEl.textContent = `${bal >= 0 ? "+" : ""}${bal.toFixed(2).replace(".", ",")} €`;
            card.appendChild(nameEl);
            card.appendChild(valEl);
            balBox.appendChild(card);
        });
        fadeInUp(Array.from(balBox.children), 40);
    }
}

export async function renderDashboard() {
    const user = await getCurrentUser();
    if (!user) { navigate("#/login"); return; }

    const app = document.getElementById("app");

    const wrapper = document.createElement("div");
    wrapper.style.cssText = "min-height:100dvh;color:white;";

    const navContainer = document.createElement("div");
    navContainer.id = "nav-container";
    wrapper.appendChild(navContainer);

    const main = document.createElement("main");
    main.style.cssText = "padding:2rem;max-width:72rem;margin:0 auto;";

    // ── Header row (month nav + add button)
    const headerRow = document.createElement("div");
    headerRow.style.cssText = "display:flex;align-items:center;justify-content:space-between;margin-bottom:2rem;flex-wrap:wrap;gap:1rem;";

    const monthNav = document.createElement("div");
    monthNav.style.cssText = "display:flex;align-items:center;gap:1rem;";

    const btnStyle = "padding:0.4rem 0.875rem;border-radius:0.5rem;border:1px solid rgba(255,255,255,0.12);background:rgba(255,255,255,0.04);color:#94a3b8;cursor:pointer;font-size:1rem;transition:all 0.15s;";
    const prevBtn = document.createElement("button");
    prevBtn.style.cssText = btnStyle;
    prevBtn.textContent = "←";

    const monthLabel = document.createElement("span");
    monthLabel.id = "dash-month-label";
    monthLabel.style.cssText = "font-size:1.125rem;font-weight:600;color:#e2e8f0;min-width:12rem;text-align:center;";
    monthLabel.textContent = _monthLabel(_year, _month);

    const nextBtn = document.createElement("button");
    nextBtn.style.cssText = btnStyle;
    nextBtn.textContent = "→";

    monthNav.appendChild(prevBtn);
    monthNav.appendChild(monthLabel);
    monthNav.appendChild(nextBtn);

    const addTxBtn = document.createElement("button");
    addTxBtn.style.cssText = "padding:0.5rem 1.25rem;border-radius:0.75rem;border:none;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;cursor:pointer;font-size:0.875rem;font-weight:500;box-shadow:0 4px 20px rgba(99,102,241,0.3);transition:opacity 0.15s;";
    addTxBtn.textContent = t("dashboard.addTransaction");
    addTxBtn.addEventListener("mouseover", () => { addTxBtn.style.opacity = "0.85"; });
    addTxBtn.addEventListener("mouseout", () => { addTxBtn.style.opacity = "1"; });
    addTxBtn.addEventListener("click", () => navigate("#/transactions"));

    headerRow.appendChild(monthNav);
    headerRow.appendChild(addTxBtn);
    main.appendChild(headerRow);

    // ── Summary cards
    const summaryGrid = document.createElement("div");
    summaryGrid.style.cssText = "display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:2rem;";

    const cardDefs = [
        { id: "dash-income",   label: t("dashboard.income"),   color: "#10b981" },
        { id: "dash-expenses", label: t("dashboard.expenses"), color: "#f43f5e" },
        { id: "dash-balance",  label: t("dashboard.balance"),  color: "#818cf8" },
    ];
    cardDefs.forEach(({ id, label, color }) => {
        const card = document.createElement("div");
        card.className = "glass glow-accent";
        card.style.cssText = "border-radius:1rem;padding:1.25rem 1.5rem;";
        const lbl = document.createElement("p");
        lbl.style.cssText = "font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:#64748b;margin-bottom:0.5rem;";
        lbl.textContent = label;
        const val = document.createElement("p");
        val.id = id;
        val.style.cssText = `font-size:1.75rem;font-weight:700;color:${color};font-variant-numeric:tabular-nums;`;
        val.textContent = "—";
        card.appendChild(lbl);
        card.appendChild(val);
        summaryGrid.appendChild(card);
    });
    main.appendChild(summaryGrid);
    fadeInUp(Array.from(summaryGrid.children), 60);

    // ── Soll/Ist
    const sollIstSection = document.createElement("div");
    sollIstSection.className = "glass";
    sollIstSection.style.cssText = "border-radius:1rem;margin-bottom:2rem;overflow:hidden;";

    const sollIstHeader = document.createElement("div");
    sollIstHeader.style.cssText = "padding:1rem 1.25rem;border-bottom:1px solid rgba(255,255,255,0.06);";
    const sollIstTitle = document.createElement("h2");
    sollIstTitle.style.cssText = "font-size:0.8rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;";
    sollIstTitle.textContent = t("dashboard.sollIst");
    sollIstHeader.appendChild(sollIstTitle);

    const sollIstBox = document.createElement("div");
    sollIstBox.id = "dash-soll-ist";

    sollIstSection.appendChild(sollIstHeader);
    sollIstSection.appendChild(sollIstBox);
    main.appendChild(sollIstSection);

    // ── Account balances
    const balHeader = document.createElement("h2");
    balHeader.style.cssText = "font-size:0.8rem;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.75rem;";
    balHeader.textContent = t("dashboard.accounts");

    const balBox = document.createElement("div");
    balBox.id = "dash-balances";
    balBox.style.cssText = "display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0.75rem;";

    main.appendChild(balHeader);
    main.appendChild(balBox);
    wrapper.appendChild(main);

    app.textContent = "";
    app.appendChild(wrapper);

    await renderNav(navContainer);

    prevBtn.addEventListener("click", () => {
        _month--;
        if (_month < 1) { _month = 12; _year--; }
        crossfade(main, () => _loadDashboard(main));
    });
    nextBtn.addEventListener("click", () => {
        _month++;
        if (_month > 12) { _month = 1; _year++; }
        crossfade(main, () => _loadDashboard(main));
    });

    await _loadDashboard(main);
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/js/views/dashboard.js
git commit -m "feat: rewrite dashboard with Cinema Dark + Glassmorphism WOW design"
```

---

## Task 10: transactions.js

**Files:**
- Create: `frontend/js/views/transactions.js`

All DOM built via `createElement` + `appendChild`. User data only via `textContent`. Modals replace `window.confirm/alert`.

- [ ] **Step 1: Write `frontend/js/views/transactions.js`**

```javascript
import { getCurrentUser } from "../auth.js";
import { navigate } from "../router.js";
import { renderNav } from "../nav.js";
import { api } from "../api.js";
import { toast, confirmDialog } from "../toast.js";
import { fadeInUp } from "../animations.js";

let _year = new Date().getFullYear();
let _month = new Date().getMonth() + 1;
let _filterAccount = "";
let _filterCategory = "";
let _accounts = [];
let _categories = [];

function _flatCats(list) {
    const result = [];
    function walk(items) {
        items.forEach(c => { result.push(c); if (c.children) walk(c.children); });
    }
    walk(list);
    return result;
}

function _monthKey() {
    return `${_year}-${String(_month).padStart(2, "0")}`;
}

function _fmtAmount(str, type) {
    const n = parseFloat(str);
    const color = type === "transfer" ? "#8b5cf6" : n >= 0 ? "#10b981" : "#f43f5e";
    const sign = n >= 0 ? "+" : "";
    return { text: `${sign}${n.toFixed(2).replace(".", ",")} €`, color };
}

function _inp(form, id, label, type, value) {
    const wrap = document.createElement("div");
    const lbl = document.createElement("label");
    lbl.style.cssText = "font-size:0.8rem;color:#64748b;display:block;margin-bottom:0.3rem;";
    lbl.textContent = label;
    lbl.htmlFor = id;
    const inp = document.createElement("input");
    inp.id = id; inp.name = id; inp.type = type;
    if (value !== undefined) inp.value = value;
    inp.style.cssText = "width:100%;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:0.5rem;padding:0.6rem 0.875rem;color:#e2e8f0;font-size:0.9rem;outline:none;";
    inp.addEventListener("focus", () => { inp.style.borderColor = "rgba(99,102,241,0.6)"; });
    inp.addEventListener("blur", () => { inp.style.borderColor = "rgba(255,255,255,0.1)"; });
    wrap.appendChild(lbl);
    wrap.appendChild(inp);
    form.appendChild(wrap);
    return inp;
}

function _sel(form, id, label, options, value) {
    const wrap = document.createElement("div");
    const lbl = document.createElement("label");
    lbl.style.cssText = "font-size:0.8rem;color:#64748b;display:block;margin-bottom:0.3rem;";
    lbl.textContent = label;
    lbl.htmlFor = id;
    const sel = document.createElement("select");
    sel.id = id; sel.name = id;
    sel.style.cssText = "width:100%;background:rgba(10,10,20,0.9);border:1px solid rgba(255,255,255,0.1);border-radius:0.5rem;padding:0.6rem 0.875rem;color:#e2e8f0;font-size:0.9rem;outline:none;";
    sel.addEventListener("focus", () => { sel.style.borderColor = "rgba(99,102,241,0.6)"; });
    sel.addEventListener("blur", () => { sel.style.borderColor = "rgba(255,255,255,0.1)"; });
    options.forEach(({ val, lbl: optLbl }) => {
        const opt = document.createElement("option");
        opt.value = val; opt.textContent = optLbl;
        if (val === String(value ?? "")) opt.selected = true;
        sel.appendChild(opt);
    });
    wrap.appendChild(lbl);
    wrap.appendChild(sel);
    form.appendChild(wrap);
    return sel;
}

function _modal(title, bodyFn, onSubmit) {
    const overlay = document.createElement("div");
    Object.assign(overlay.style, {
        position: "fixed", inset: "0",
        background: "rgba(0,0,0,0.7)",
        backdropFilter: "blur(6px)", WebkitBackdropFilter: "blur(6px)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: "10000", opacity: "0", transition: "opacity 0.2s ease",
    });
    const box = document.createElement("div");
    Object.assign(box.style, {
        background: "rgba(10,10,20,0.97)",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: "1.25rem",
        padding: "2rem",
        width: "min(480px,90vw)",
        maxHeight: "85vh",
        overflowY: "auto",
        transform: "scale(0.88) translateY(20px)",
        transition: "transform 0.35s cubic-bezier(0.34,1.56,0.64,1), opacity 0.2s ease",
        opacity: "0",
    });
    const h2 = document.createElement("h2");
    h2.style.cssText = "font-size:1.125rem;font-weight:600;color:#e2e8f0;margin-bottom:1.5rem;";
    h2.textContent = title;
    box.appendChild(h2);

    const form = document.createElement("form");
    form.style.cssText = "display:flex;flex-direction:column;gap:1rem;";
    bodyFn(form);

    const row = document.createElement("div");
    row.style.cssText = "display:flex;gap:0.75rem;justify-content:flex-end;margin-top:0.5rem;";

    const cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.style.cssText = "padding:0.5rem 1.25rem;border-radius:0.5rem;border:1px solid rgba(255,255,255,0.15);background:transparent;color:#94a3b8;cursor:pointer;font-size:0.875rem;";
    cancelBtn.textContent = t("transactions.cancel");

    const submitBtn = document.createElement("button");
    submitBtn.type = "submit";
    submitBtn.style.cssText = "padding:0.5rem 1.25rem;border-radius:0.5rem;border:none;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;cursor:pointer;font-size:0.875rem;font-weight:500;";
    submitBtn.textContent = t("transactions.save");

    row.appendChild(cancelBtn);
    row.appendChild(submitBtn);
    form.appendChild(row);
    box.appendChild(form);
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    requestAnimationFrame(() => {
        overlay.style.opacity = "1";
        box.style.transform = "scale(1) translateY(0)";
        box.style.opacity = "1";
    });

    const close = () => {
        overlay.style.opacity = "0";
        box.style.transform = "scale(0.95) translateY(10px)";
        box.style.opacity = "0";
        setTimeout(() => overlay.remove(), 250);
    };
    cancelBtn.addEventListener("click", close);
    overlay.addEventListener("click", (e) => { if (e.target === overlay) close(); });
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        submitBtn.disabled = true;
        submitBtn.style.opacity = "0.6";
        try { await onSubmit(form, close); }
        finally { submitBtn.disabled = false; submitBtn.style.opacity = "1"; }
    });
}

function _openAdd(onDone) {
    _modal(t("transactions.add"), (form) => {
        const typeOpts = [
            { val: "expense", lbl: t("transactions.expense") },
            { val: "income", lbl: t("transactions.income") },
        ];
        _sel(form, "transaction_type", t("transactions.type"), typeOpts, "expense");
        _sel(form, "account_id", t("transactions.account"), _accounts.filter(a => !a.archived).map(a => ({ val: String(a.id), lbl: a.name })));
        _sel(form, "category_id", t("transactions.category"), _categories.map(c => ({ val: String(c.id), lbl: c.name })));
        _inp(form, "amount", t("transactions.amount"), "number", "0.00");
        _inp(form, "date", t("transactions.date"), "date", new Date().toISOString().slice(0, 10));
        _inp(form, "description", t("transactions.description"), "text");
    }, async (form, close) => {
        const d = Object.fromEntries(new FormData(form).entries());
        const r = await api.post("/transactions", {
            account_id: parseInt(d.account_id),
            category_id: parseInt(d.category_id),
            amount: d.amount,
            date: d.date,
            description: d.description,
            transaction_type: d.transaction_type,
        });
        if (!r.ok) { toast(t("errors.generic"), "error"); return; }
        toast(t("transactions.add"), "success");
        close();
        onDone();
    });
}

function _openTransfer(onDone) {
    _modal(t("transactions.addTransfer"), (form) => {
        const accOpts = _accounts.filter(a => !a.archived).map(a => ({ val: String(a.id), lbl: a.name }));
        _sel(form, "from_account_id", t("transactions.fromAccount"), accOpts);
        _sel(form, "to_account_id", t("transactions.toAccount"), accOpts);
        _inp(form, "amount", t("transactions.amount"), "number", "0.00");
        _inp(form, "date", t("transactions.date"), "date", new Date().toISOString().slice(0, 10));
        _inp(form, "description", t("transactions.description"), "text");
    }, async (form, close) => {
        const d = Object.fromEntries(new FormData(form).entries());
        const r = await api.post("/transactions/transfer", {
            from_account_id: parseInt(d.from_account_id),
            to_account_id: parseInt(d.to_account_id),
            amount: d.amount,
            date: d.date,
            description: d.description,
        });
        if (!r.ok) { toast(t("errors.generic"), "error"); return; }
        toast(t("transactions.addTransfer"), "success");
        close();
        onDone();
    });
}

function _openEdit(tx, onDone) {
    _modal(t("transactions.edit"), (form) => {
        const typeOpts = [
            { val: "expense", lbl: t("transactions.expense") },
            { val: "income", lbl: t("transactions.income") },
        ];
        _sel(form, "transaction_type", t("transactions.type"), typeOpts, tx.transaction_type);
        _sel(form, "account_id", t("transactions.account"),
            _accounts.filter(a => !a.archived).map(a => ({ val: String(a.id), lbl: a.name })),
            String(tx.account_id));
        _sel(form, "category_id", t("transactions.category"),
            _categories.map(c => ({ val: String(c.id), lbl: c.name })),
            tx.category_id ? String(tx.category_id) : "");
        _inp(form, "amount", t("transactions.amount"), "number", Math.abs(parseFloat(tx.amount)).toFixed(2));
        _inp(form, "date", t("transactions.date"), "date", tx.date);
        _inp(form, "description", t("transactions.description"), "text", tx.description);
    }, async (form, close) => {
        const d = Object.fromEntries(new FormData(form).entries());
        const r = await api.patch(`/transactions/${tx.id}`, {
            account_id: parseInt(d.account_id),
            category_id: d.category_id ? parseInt(d.category_id) : null,
            amount: d.amount,
            date: d.date,
            description: d.description,
            transaction_type: d.transaction_type,
        });
        if (!r.ok) { toast(t("errors.generic"), "error"); return; }
        toast(t("transactions.save"), "success");
        close();
        onDone();
    });
}

async function _loadTable(tbody) {
    let url = `/transactions?year=${_year}&month=${_month}`;
    if (_filterAccount) url += `&account_id=${_filterAccount}`;
    if (_filterCategory) url += `&category_id=${_filterCategory}`;
    const res = await api.get(url);
    if (!res.ok) { toast(t("errors.generic"), "error"); return; }
    const txs = await res.json();
    tbody.textContent = "";

    if (txs.length === 0) {
        const tr = document.createElement("tr");
        const td = document.createElement("td");
        td.colSpan = 6;
        td.style.cssText = "text-align:center;padding:2.5rem;color:#475569;font-size:0.875rem;";
        td.textContent = t("transactions.noData");
        tr.appendChild(td);
        tbody.appendChild(tr);
        return;
    }

    txs.forEach(tx => {
        const accName = _accounts.find(a => a.id === tx.account_id)?.name ?? "—";
        const catObj = _categories.find(c => c.id === tx.category_id);
        const catName = catObj ? catObj.name
            : (tx.transaction_type === "transfer" ? t("transactions.transfer") : "—");
        const { text: amtText, color: amtColor } = _fmtAmount(tx.amount, tx.transaction_type);

        const tr = document.createElement("tr");
        tr.style.cssText = "border-bottom:1px solid rgba(255,255,255,0.04);transition:background 0.1s;";
        tr.addEventListener("mouseover", () => { tr.style.background = "rgba(255,255,255,0.02)"; });
        tr.addEventListener("mouseout", () => { tr.style.background = "transparent"; });

        const cellDefs = [
            { text: tx.date, s: "color:#64748b;font-size:0.8rem;" },
            { text: tx.description, s: "color:#e2e8f0;" },
            { text: catName, s: "color:#94a3b8;font-size:0.85rem;" },
            { text: accName, s: "color:#94a3b8;font-size:0.85rem;" },
            { text: amtText, s: `color:${amtColor};font-weight:600;font-variant-numeric:tabular-nums;text-align:right;` },
        ];
        cellDefs.forEach(({ text, s }) => {
            const td = document.createElement("td");
            td.style.cssText = `padding:0.75rem 1rem;${s}`;
            td.textContent = text;
            tr.appendChild(td);
        });

        const actionTd = document.createElement("td");
        actionTd.style.cssText = "padding:0.5rem 1rem;text-align:right;white-space:nowrap;";

        if (tx.transaction_type !== "transfer") {
            const editBtn = document.createElement("button");
            editBtn.style.cssText = "font-size:0.75rem;color:#6366f1;background:none;border:none;cursor:pointer;margin-right:0.5rem;";
            editBtn.textContent = t("transactions.edit");
            editBtn.addEventListener("click", () => _openEdit(tx, () => _loadTable(tbody)));
            actionTd.appendChild(editBtn);
        }

        const delBtn = document.createElement("button");
        delBtn.style.cssText = "font-size:0.75rem;color:#f43f5e;background:none;border:none;cursor:pointer;";
        delBtn.textContent = t("transactions.delete");
        delBtn.addEventListener("click", () => {
            confirmDialog(t("transactions.confirmDelete"), async () => {
                const r = await api.delete(`/transactions/${tx.id}`);
                if (!r.ok) { toast(t("errors.generic"), "error"); return; }
                toast(t("transactions.delete"), "success");
                _loadTable(tbody);
            });
        });
        actionTd.appendChild(delBtn);
        tr.appendChild(actionTd);
        tbody.appendChild(tr);
    });
    fadeInUp(Array.from(tbody.querySelectorAll("tr")), 20);
}

export async function renderTransactions() {
    const user = await getCurrentUser();
    if (!user) { navigate("#/login"); return; }

    const app = document.getElementById("app");
    const wrapper = document.createElement("div");
    wrapper.style.cssText = "min-height:100dvh;color:white;";

    const navContainer = document.createElement("div");
    navContainer.id = "nav-container";
    wrapper.appendChild(navContainer);

    const main = document.createElement("main");
    main.style.cssText = "padding:2rem;max-width:72rem;margin:0 auto;";

    // Load reference data
    const [accRes, catRes] = await Promise.all([api.get("/accounts"), api.get("/categories")]);
    _accounts = accRes.ok ? await accRes.json() : [];
    const catTree = catRes.ok ? await catRes.json() : [];
    _categories = _flatCats(catTree);

    // Header
    const headerRow = document.createElement("div");
    headerRow.style.cssText = "display:flex;align-items:center;justify-content:space-between;margin-bottom:1.5rem;flex-wrap:wrap;gap:1rem;";

    const title = document.createElement("h1");
    title.style.cssText = "font-size:1.5rem;font-weight:700;color:#e2e8f0;";
    title.textContent = t("transactions.title");

    const btnGroup = document.createElement("div");
    btnGroup.style.cssText = "display:flex;gap:0.75rem;";

    const addBtn = document.createElement("button");
    addBtn.style.cssText = "padding:0.5rem 1.25rem;border-radius:0.75rem;border:none;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:white;cursor:pointer;font-size:0.875rem;font-weight:500;box-shadow:0 4px 20px rgba(99,102,241,0.3);";
    addBtn.textContent = t("transactions.add");

    const transferBtn = document.createElement("button");
    transferBtn.style.cssText = "padding:0.5rem 1.25rem;border-radius:0.75rem;border:1px solid rgba(139,92,246,0.4);background:rgba(139,92,246,0.1);color:#a78bfa;cursor:pointer;font-size:0.875rem;";
    transferBtn.textContent = t("transactions.addTransfer");

    btnGroup.appendChild(addBtn);
    btnGroup.appendChild(transferBtn);
    headerRow.appendChild(title);
    headerRow.appendChild(btnGroup);
    main.appendChild(headerRow);

    // Filters
    const filterRow = document.createElement("div");
    filterRow.style.cssText = "display:flex;gap:0.75rem;margin-bottom:1.5rem;flex-wrap:wrap;";

    const inputStyle = "background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1);border-radius:0.5rem;padding:0.4rem 0.75rem;color:#e2e8f0;font-size:0.85rem;outline:none;";

    const monthInp = document.createElement("input");
    monthInp.type = "month";
    monthInp.value = _monthKey();
    monthInp.style.cssText = inputStyle;

    const accFilter = document.createElement("select");
    accFilter.style.cssText = inputStyle;
    const allAccOpt = document.createElement("option");
    allAccOpt.value = ""; allAccOpt.textContent = t("transactions.filterAccount");
    accFilter.appendChild(allAccOpt);
    _accounts.forEach(a => {
        const o = document.createElement("option"); o.value = String(a.id); o.textContent = a.name;
        accFilter.appendChild(o);
    });

    const catFilter = document.createElement("select");
    catFilter.style.cssText = inputStyle;
    const allCatOpt = document.createElement("option");
    allCatOpt.value = ""; allCatOpt.textContent = t("transactions.filterCategory");
    catFilter.appendChild(allCatOpt);
    _categories.forEach(c => {
        const o = document.createElement("option"); o.value = String(c.id); o.textContent = c.name;
        catFilter.appendChild(o);
    });

    filterRow.appendChild(monthInp);
    filterRow.appendChild(accFilter);
    filterRow.appendChild(catFilter);
    main.appendChild(filterRow);

    // Table
    const tableWrap = document.createElement("div");
    tableWrap.className = "glass";
    tableWrap.style.cssText = "border-radius:1rem;overflow:hidden;";

    const table = document.createElement("table");
    table.style.cssText = "width:100%;border-collapse:collapse;";

    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    headRow.style.cssText = "border-bottom:1px solid rgba(255,255,255,0.06);";
    const thDefs = [
        t("transactions.date"), t("transactions.description"),
        t("transactions.category"), t("transactions.account"),
        t("transactions.amount"), "",
    ];
    thDefs.forEach((lbl, i) => {
        const th = document.createElement("th");
        th.style.cssText = "padding:0.75rem 1rem;text-align:left;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#475569;";
        if (i === 4) th.style.textAlign = "right";
        th.textContent = lbl;
        headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    table.appendChild(tbody);
    tableWrap.appendChild(table);
    main.appendChild(tableWrap);

    wrapper.appendChild(main);
    app.textContent = "";
    app.appendChild(wrapper);

    await renderNav(navContainer);

    monthInp.addEventListener("change", () => {
        const parts = monthInp.value.split("-").map(Number);
        _year = parts[0]; _month = parts[1];
        _loadTable(tbody);
    });
    accFilter.addEventListener("change", () => { _filterAccount = accFilter.value; _loadTable(tbody); });
    catFilter.addEventListener("change", () => { _filterCategory = catFilter.value; _loadTable(tbody); });
    addBtn.addEventListener("click", () => _openAdd(() => _loadTable(tbody)));
    transferBtn.addEventListener("click", () => _openTransfer(() => _loadTable(tbody)));

    await _loadTable(tbody);
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/js/views/transactions.js
git commit -m "feat: add transactions page with CRUD, transfer, and custom modals"
```

---

## Task 11: Final Verification

- [ ] **Step 1: Run all backend tests**

```bash
cd backend && pytest -v
```

Expected: all PASSED, no failures

- [ ] **Step 2: Verify dev server**

```bash
cd backend
SECRET_KEY=dev-secret-key-change-in-production!! DATABASE_PATH=./helledger.db uvicorn app.main:app --port 3000 --reload
```

Verify in browser at http://localhost:3000:
- Login → dashboard with ambient blobs, glassmorphic cards visible
- Summary cards count up from 0 with animation
- Month navigation ← → changes data with crossfade
- Soll/Ist progress bars animate in
- "Add Transaction" → custom spring-animated modal (not a browser dialog)
- Toast appears bottom-right on success
- Transactions page: table loads, filters work
- Add income/expense via modal → row appears, toast shown
- Add transfer → two rows appear, transfer type shown in purple
- Delete → `confirmDialog` overlay (no `window.confirm`), toast on confirm
- Edit on transfer row → edit button not shown

- [ ] **Step 3: Push**

```bash
git push origin main
```
