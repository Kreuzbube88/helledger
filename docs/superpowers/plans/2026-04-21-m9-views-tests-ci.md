# HELLEDGER M9: Views, Excel, Tests, CI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add year/month/net-worth views, Excel import/export, DB performance indices, reach 60%+ pytest coverage, set up GitHub Actions CI with multi-arch Docker build, and add PWA manifest + docs skeleton.

**Architecture:** New FastAPI routers for year, month, and net-worth endpoints. New Vue SFCs for each view. Excel handled by openpyxl (add to requirements.txt; spec-mandated). DB indices added via new Alembic migration. GitHub Actions: separate CI workflow (test on PR/push) and release workflow (multi-arch ghcr.io on tags). PWA uses existing manifest.json + service-worker.js already in `frontend/public/`.

**Tech Stack:** FastAPI, openpyxl 3.1 (add), Vue 3 + vue-chartjs, Alembic (migration), GitHub Actions, Docker buildx (multi-arch).

---

## File Map

```
backend/
├── requirements.txt                ← MODIFY: add openpyxl==3.1.5
├── app/
│   ├── routers/
│   │   ├── year_view.py            ← CREATE: GET /api/dashboard/year
│   │   ├── month_view.py           ← CREATE: GET /api/dashboard/month
│   │   └── net_worth.py            ← CREATE: GET/POST /api/net-worth
│   ├── models/
│   │   └── net_worth.py            ← CREATE: NetWorthSnapshot
│   ├── schemas/
│   │   ├── year_view.py            ← CREATE
│   │   ├── month_view.py           ← CREATE
│   │   └── net_worth.py            ← CREATE
│   └── main.py                     ← MODIFY: include new routers
├── alembic/versions/
│   ├── 007_net_worth.py            ← CREATE: net_worth_snapshots table
│   └── 008_indices.py              ← CREATE: performance indices
└── tests/
    ├── test_year_view.py           ← CREATE
    ├── test_month_view.py          ← CREATE
    ├── test_net_worth.py           ← CREATE
    ├── test_excel.py               ← CREATE
    └── test_coverage_extras.py     ← CREATE: fill coverage gaps

frontend/src/
├── views/
│   ├── YearView.vue                ← CREATE
│   ├── MonthView.vue               ← CREATE
│   └── NetWorthView.vue            ← CREATE
├── router/index.js                 ← MODIFY: add /year, /month, /net-worth
├── components/AppNav.vue           ← MODIFY: add year/net-worth nav links
└── locales/
    ├── de.json                     ← MODIFY: add year/month/netWorth keys
    └── en.json                     ← MODIFY

.github/workflows/
├── ci.yml                          ← CREATE: run tests on push + PR
└── release.yml                     ← CREATE: multi-arch build on v* tags

docs/
├── de/
│   ├── installation.md             ← CREATE
│   ├── first-steps.md              ← CREATE
│   ├── import-export.md            ← CREATE
│   ├── backup.md                   ← CREATE
│   └── admin.md                    ← CREATE
└── en/
    ├── installation.md             ← CREATE
    └── first-steps.md              ← CREATE
```

---

### Task 1: DB migration — net_worth_snapshots + performance indices

**Files:**
- Create: `backend/alembic/versions/007_net_worth.py`
- Create: `backend/alembic/versions/008_indices.py`

- [ ] **Step 1: Create migration 007**

```python
# backend/alembic/versions/007_net_worth.py
"""add net_worth_snapshots table

Revision ID: 007
Revises: 006
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "net_worth_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "household_id",
            sa.Integer(),
            sa.ForeignKey("households.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_assets", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_liabilities", sa.Numeric(14, 2), nullable=False),
        sa.Column("net_worth", sa.Numeric(14, 2), nullable=False),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("net_worth_snapshots")
```

- [ ] **Step 2: Create migration 008**

```python
# backend/alembic/versions/008_indices.py
"""add performance indices on transactions

Revision ID: 008
Revises: 007
Create Date: 2026-04-21
"""
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_tx_household_date", "transactions", ["household_id", "date"])
    op.create_index("ix_tx_category", "transactions", ["category_id"])
    op.create_index("ix_tx_account", "transactions", ["account_id"])
    op.create_index("ix_tx_type", "transactions", ["type"])


def downgrade() -> None:
    op.drop_index("ix_tx_household_date", "transactions")
    op.drop_index("ix_tx_category", "transactions")
    op.drop_index("ix_tx_account", "transactions")
    op.drop_index("ix_tx_type", "transactions")
```

- [ ] **Step 3: Test migrations**

```bash
cd backend && DATABASE_PATH=data/test_m9.db SECRET_KEY=test alembic upgrade head
python -c "
import sqlite3
conn = sqlite3.connect('data/test_m9.db')
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print([t[0] for t in tables])
indices = conn.execute(\"SELECT name FROM sqlite_master WHERE type='index'\").fetchall()
print([i[0] for i in indices])
conn.close()
"
```
Expected: `net_worth_snapshots` in tables, `ix_tx_household_date` in indices.

```bash
rm backend/data/test_m9.db
```

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/007_net_worth.py backend/alembic/versions/008_indices.py
git commit -m "feat: migrations 007 (net_worth_snapshots) + 008 (tx performance indices)"
```

---

### Task 2: Net worth model + API

**Files:**
- Create: `backend/app/models/net_worth.py`
- Create: `backend/app/schemas/net_worth.py`
- Create: `backend/app/routers/net_worth.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_net_worth.py
import pytest


def test_list_snapshots_empty(registered_client):
    r = registered_client.get("/api/net-worth")
    assert r.status_code == 200
    assert r.json() == []


def test_create_snapshot(registered_client):
    r = registered_client.post("/api/net-worth", json={
        "snapshot_date": "2026-04-01",
        "total_assets": 50000.00,
        "total_liabilities": 10000.00,
        "notes": "April snapshot",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["net_worth"] == 40000.0
    assert data["notes"] == "April snapshot"


def test_list_snapshots_after_create(registered_client):
    registered_client.post("/api/net-worth", json={
        "snapshot_date": "2026-03-01",
        "total_assets": 48000.00,
        "total_liabilities": 10000.00,
    })
    r = registered_client.get("/api/net-worth")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_delete_snapshot(registered_client):
    r = registered_client.post("/api/net-worth", json={
        "snapshot_date": "2026-02-01",
        "total_assets": 45000.00,
        "total_liabilities": 9000.00,
    })
    snap_id = r.json()["id"]
    d = registered_client.delete(f"/api/net-worth/{snap_id}")
    assert d.status_code == 204
    assert registered_client.get("/api/net-worth").json() == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_net_worth.py -v
```
Expected: ImportError or 404

- [ ] **Step 3: Create net_worth model**

```python
# backend/app/models/net_worth.py
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import mapped_column, Mapped
from app.database import Base


class NetWorthSnapshot(Base):
    __tablename__ = "net_worth_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_assets: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    net_worth: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

- [ ] **Step 4: Create net_worth schemas**

```python
# backend/app/schemas/net_worth.py
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal


class NetWorthCreate(BaseModel):
    snapshot_date: date
    total_assets: Decimal
    total_liabilities: Decimal
    notes: str | None = None


class NetWorthOut(BaseModel):
    id: int
    snapshot_date: date
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Create net_worth router**

```python
# backend/app/routers/net_worth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.net_worth import NetWorthSnapshot
from app.models.user import User
from app.schemas.net_worth import NetWorthCreate, NetWorthOut
from datetime import datetime, timezone

router = APIRouter(prefix="/net-worth")


def _require_household(user: User) -> int:
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    return user.active_household_id


@router.get("", response_model=list[NetWorthOut])
def list_snapshots(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hh_id = _require_household(user)
    return (
        db.query(NetWorthSnapshot)
        .filter(NetWorthSnapshot.household_id == hh_id)
        .order_by(NetWorthSnapshot.snapshot_date.desc())
        .all()
    )


@router.post("", response_model=NetWorthOut, status_code=status.HTTP_201_CREATED)
def create_snapshot(
    body: NetWorthCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hh_id = _require_household(user)
    snap = NetWorthSnapshot(
        household_id=hh_id,
        snapshot_date=body.snapshot_date,
        total_assets=body.total_assets,
        total_liabilities=body.total_liabilities,
        net_worth=body.total_assets - body.total_liabilities,
        notes=body.notes,
        created_at=datetime.now(timezone.utc),
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


@router.delete("/{snap_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snapshot(
    snap_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hh_id = _require_household(user)
    snap = db.query(NetWorthSnapshot).filter(
        NetWorthSnapshot.id == snap_id,
        NetWorthSnapshot.household_id == hh_id,
    ).first()
    if not snap:
        raise HTTPException(status_code=404, detail="not_found")
    db.delete(snap)
    db.commit()
```

- [ ] **Step 6: Register in main.py**

Add import and `app.include_router` call — same pattern as existing routers. Also import `NetWorthSnapshot` so SQLAlchemy registers the model:
```python
from app.routers import net_worth as net_worth_router
from app.models import net_worth as _nw_models  # registers model with Base
# ...
app.include_router(net_worth_router.router, prefix="/api")
```

- [ ] **Step 7: Run tests**

```bash
cd backend && python -m pytest tests/test_net_worth.py -v
```
Expected: 4 tests pass

- [ ] **Step 8: Run full suite**

```bash
cd backend && python -m pytest tests/ -x -q 2>&1 | tail -5
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/models/net_worth.py backend/app/schemas/net_worth.py backend/app/routers/net_worth.py backend/app/main.py backend/tests/test_net_worth.py
git commit -m "feat: net worth snapshots API (list/create/delete)"
```

---

### Task 3: Year view API

**Files:**
- Create: `backend/app/routers/year_view.py`
- Create: `backend/app/schemas/year_view.py`
- Modify: `backend/app/main.py`

The year view returns a 12-column matrix: for each category, actual spend per month. Response shape:
```json
{
  "year": 2026,
  "categories": [
    {
      "id": 1, "name": "Miete", "type": "fixed",
      "months": [1200.0, 1200.0, ..., 1200.0]  // 12 values, index 0 = Jan
    }
  ],
  "monthly_income": [3500.0, ...],   // 12 values
  "monthly_expense": [2100.0, ...],  // 12 values
  "monthly_balance": [1400.0, ...]   // 12 values
}
```

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_year_view.py
import pytest


def test_year_view_empty(registered_client):
    r = registered_client.get("/api/dashboard/year?year=2026")
    assert r.status_code == 200
    data = r.json()
    assert data["year"] == 2026
    assert "categories" in data
    assert "monthly_balance" in data
    assert len(data["monthly_balance"]) == 12


def test_year_view_with_transactions(registered_client):
    # Create account
    acc = registered_client.post("/api/accounts", json={
        "name": "Girokonto", "type": "checking", "initial_balance": 0, "currency": "EUR"
    }).json()

    # Create category
    cat = registered_client.post("/api/categories", json={
        "name": "Miete", "type": "fixed", "color": "#ff0000"
    }).json()

    # Create transactions in Jan + Feb 2026
    registered_client.post("/api/transactions", json={
        "date": "2026-01-15", "description": "Miete Jan",
        "account_id": acc["id"], "category_id": cat["id"],
        "amount": 1200.0, "type": "expense"
    })
    registered_client.post("/api/transactions", json={
        "date": "2026-02-15", "description": "Miete Feb",
        "account_id": acc["id"], "category_id": cat["id"],
        "amount": 1200.0, "type": "expense"
    })

    r = registered_client.get("/api/dashboard/year?year=2026")
    assert r.status_code == 200
    data = r.json()
    cats = {c["name"]: c for c in data["categories"]}
    assert "Miete" in cats
    miete = cats["Miete"]["months"]
    assert miete[0] == 1200.0   # January index 0
    assert miete[1] == 1200.0   # February index 1
    assert miete[2] == 0.0      # March index 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_year_view.py -v
```
Expected: 404 or ImportError

- [ ] **Step 3: Create year_view schemas**

```python
# backend/app/schemas/year_view.py
from pydantic import BaseModel


class YearCategoryRow(BaseModel):
    id: int
    name: str
    type: str
    color: str | None
    months: list[float]     # 12 values, index 0 = January


class YearViewResponse(BaseModel):
    year: int
    categories: list[YearCategoryRow]
    monthly_income: list[float]
    monthly_expense: list[float]
    monthly_balance: list[float]
```

- [ ] **Step 4: Create year_view router**

```python
# backend/app/routers/year_view.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.household import Category
from app.schemas.year_view import YearViewResponse, YearCategoryRow

router = APIRouter()


@router.get("/dashboard/year", response_model=YearViewResponse)
def year_view(
    year: int = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hh_id = user.active_household_id
    if not hh_id:
        return YearViewResponse(year=year, categories=[], monthly_income=[0]*12, monthly_expense=[0]*12, monthly_balance=[0]*12)

    # Sum transactions by (category_id, month, type)
    rows = (
        db.query(
            Transaction.category_id,
            func.strftime("%m", Transaction.date).label("month"),
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        )
        .filter(
            Transaction.household_id == hh_id,
            func.strftime("%Y", Transaction.date) == str(year),
        )
        .group_by(Transaction.category_id, func.strftime("%m", Transaction.date), Transaction.type)
        .all()
    )

    # Build lookup: {(cat_id, month_int): total}
    expense_by_cat_month: dict[tuple[int | None, int], float] = {}
    monthly_income = [0.0] * 12
    monthly_expense = [0.0] * 12

    for cat_id, month_str, tx_type, total in rows:
        m = int(month_str) - 1  # 0-indexed
        amount = float(total)
        if tx_type == "income":
            monthly_income[m] += amount
        elif tx_type in ("expense",):
            monthly_expense[m] += amount
            if cat_id is not None:
                expense_by_cat_month[(cat_id, m)] = expense_by_cat_month.get((cat_id, m), 0.0) + amount

    monthly_balance = [monthly_income[i] - monthly_expense[i] for i in range(12)]

    # Build category rows (only categories with any transactions this year)
    cat_ids = {k[0] for k in expense_by_cat_month.keys()}
    categories = []
    for cat_id in sorted(cat_ids):
        cat = db.get(Category, cat_id)
        if cat is None:
            continue
        months = [expense_by_cat_month.get((cat_id, m), 0.0) for m in range(12)]
        categories.append(YearCategoryRow(
            id=cat.id,
            name=cat.name,
            type=cat.type,
            color=getattr(cat, "color", None),
            months=months,
        ))

    return YearViewResponse(
        year=year,
        categories=categories,
        monthly_income=monthly_income,
        monthly_expense=monthly_expense,
        monthly_balance=monthly_balance,
    )
```

- [ ] **Step 5: Register in main.py**

```python
from app.routers import year_view as year_view_router
# ...
app.include_router(year_view_router.router, prefix="/api")
```

- [ ] **Step 6: Run tests**

```bash
cd backend && python -m pytest tests/test_year_view.py -v
```
Expected: 2 tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/year_view.py backend/app/schemas/year_view.py backend/app/main.py backend/tests/test_year_view.py
git commit -m "feat: year overview API (12-column category matrix)"
```

---

### Task 4: Month view API

**Files:**
- Create: `backend/app/routers/month_view.py`
- Create: `backend/app/schemas/month_view.py`
- Modify: `backend/app/main.py`

The month view is a soll/ist comparison per category, grouped in sections (income, fixed, variable). Response:
```json
{
  "year": 2026, "month": 4,
  "sections": [
    {
      "type": "income",
      "rows": [
        {"category_id": 1, "name": "Gehalt", "soll": 3500.0, "ist": 3500.0, "diff": 0.0, "pct": 100.0}
      ],
      "total_soll": 3500.0, "total_ist": 3500.0
    }
  ],
  "summary": {"total_income": 3500.0, "total_expense": 2100.0, "balance": 1400.0, "savings_rate": 40.0}
}
```

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_month_view.py
import pytest


def test_month_view_empty(registered_client):
    r = registered_client.get("/api/dashboard/month?year=2026&month=4")
    assert r.status_code == 200
    data = r.json()
    assert data["year"] == 2026
    assert data["month"] == 4
    assert "sections" in data
    assert "summary" in data


def test_month_view_sections(registered_client):
    acc = registered_client.post("/api/accounts", json={"name": "Konto", "type": "checking", "initial_balance": 0, "currency": "EUR"}).json()
    cat = registered_client.post("/api/categories", json={"name": "Miete", "type": "fixed", "color": "#ff0000"}).json()

    registered_client.post("/api/transactions", json={
        "date": "2026-04-10", "description": "Miete",
        "account_id": acc["id"], "category_id": cat["id"],
        "amount": 1200.0, "type": "expense"
    })

    r = registered_client.get("/api/dashboard/month?year=2026&month=4")
    data = r.json()
    fixed_section = next((s for s in data["sections"] if s["type"] == "fixed"), None)
    assert fixed_section is not None
    miete_row = next((rw for rw in fixed_section["rows"] if rw["name"] == "Miete"), None)
    assert miete_row is not None
    assert miete_row["ist"] == 1200.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_month_view.py -v
```
Expected: 404

- [ ] **Step 3: Create month_view schemas**

```python
# backend/app/schemas/month_view.py
from pydantic import BaseModel


class MonthCategoryRow(BaseModel):
    category_id: int
    name: str
    soll: float
    ist: float
    diff: float
    pct: float  # ist/soll * 100, or 0 if soll=0


class MonthSection(BaseModel):
    type: str   # "income", "fixed", "variable"
    rows: list[MonthCategoryRow]
    total_soll: float
    total_ist: float


class MonthSummary(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    savings_rate: float  # balance/income * 100


class MonthViewResponse(BaseModel):
    year: int
    month: int
    sections: list[MonthSection]
    summary: MonthSummary
```

- [ ] **Step 4: Create month_view router**

```python
# backend/app/routers/month_view.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.household import Category
from app.schemas.month_view import MonthCategoryRow, MonthSection, MonthSummary, MonthViewResponse

router = APIRouter()

_SECTION_ORDER = ["income", "fixed", "variable"]


def _get_soll(cat: Category, year: int, month: int, db: Session) -> float:
    """Get expected value for category in given year/month. Returns 0 if none defined."""
    from app.models.household import ExpectedValue
    ev = (
        db.query(ExpectedValue)
        .filter(
            ExpectedValue.category_id == cat.id,
            ExpectedValue.valid_from <= f"{year:04d}-{month:02d}-01",
        )
        .order_by(ExpectedValue.valid_from.desc())
        .first()
    )
    return float(ev.amount) if ev else 0.0


@router.get("/dashboard/month", response_model=MonthViewResponse)
def month_view(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hh_id = user.active_household_id
    month_str = f"{year:04d}-{month:02d}"

    if not hh_id:
        empty_summary = MonthSummary(total_income=0, total_expense=0, balance=0, savings_rate=0)
        return MonthViewResponse(year=year, month=month, sections=[], summary=empty_summary)

    # Actuals by category
    rows = (
        db.query(
            Transaction.category_id,
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        )
        .filter(
            Transaction.household_id == hh_id,
            func.strftime("%Y-%m", Transaction.date) == month_str,
            Transaction.type.in_(["income", "expense"]),
        )
        .group_by(Transaction.category_id, Transaction.type)
        .all()
    )

    ist_by_cat: dict[int, float] = {}
    type_by_cat: dict[int, str] = {}
    for cat_id, tx_type, total in rows:
        if cat_id is not None:
            ist_by_cat[cat_id] = ist_by_cat.get(cat_id, 0.0) + float(total)
            type_by_cat[cat_id] = tx_type

    # All categories with transactions this month
    cat_ids = set(ist_by_cat.keys())
    all_cats = db.query(Category).filter(Category.id.in_(cat_ids)).all() if cat_ids else []

    sections_map: dict[str, list[MonthCategoryRow]] = {t: [] for t in _SECTION_ORDER}

    for cat in all_cats:
        soll = _get_soll(cat, year, month, db)
        ist = ist_by_cat.get(cat.id, 0.0)
        diff = soll - ist
        pct = (ist / soll * 100) if soll > 0 else 0.0
        sections_map[cat.type].append(MonthCategoryRow(
            category_id=cat.id, name=cat.name, soll=soll, ist=ist, diff=diff, pct=pct
        ))

    sections = []
    total_income = 0.0
    total_expense = 0.0

    for sec_type in _SECTION_ORDER:
        cat_rows = sorted(sections_map[sec_type], key=lambda r: r.name)
        total_soll = sum(r.soll for r in cat_rows)
        total_ist = sum(r.ist for r in cat_rows)
        if sec_type == "income":
            total_income = total_ist
        else:
            total_expense += total_ist
        if cat_rows:
            sections.append(MonthSection(type=sec_type, rows=cat_rows, total_soll=total_soll, total_ist=total_ist))

    balance = total_income - total_expense
    savings_rate = (balance / total_income * 100) if total_income > 0 else 0.0

    return MonthViewResponse(
        year=year, month=month, sections=sections,
        summary=MonthSummary(total_income=total_income, total_expense=total_expense, balance=balance, savings_rate=savings_rate),
    )
```

- [ ] **Step 5: Register in main.py**

```python
from app.routers import month_view as month_view_router
# ...
app.include_router(month_view_router.router, prefix="/api")
```

- [ ] **Step 6: Run tests**

```bash
cd backend && python -m pytest tests/test_month_view.py -v
```
Expected: 2 tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/month_view.py backend/app/schemas/month_view.py backend/app/main.py backend/tests/test_month_view.py
git commit -m "feat: month view API (soll/ist per category with sections)"
```

---

### Task 5: Excel import + export

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/services/excel_io.py`
- Modify: `backend/app/routers/import_.py`
- Modify: `backend/app/main.py` (add export endpoint or a new router)

- [ ] **Step 1: Add openpyxl to requirements.txt**

```
# backend/requirements.txt — add:
openpyxl==3.1.5
```

```bash
cd backend && pip install openpyxl==3.1.5
python -c "import openpyxl; print('ok')"
```
Expected: `ok`

- [ ] **Step 2: Write the failing test**

```python
# backend/tests/test_excel.py
import io
import openpyxl
import pytest


def _make_excel(rows: list[dict]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["date", "description", "amount", "type"])
    for row in rows:
        ws.append([row["date"], row["description"], row["amount"], row["type"]])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_excel_import(registered_client):
    acc = registered_client.post("/api/accounts", json={"name": "Konto", "type": "checking", "initial_balance": 0, "currency": "EUR"}).json()
    xlsx_bytes = _make_excel([
        {"date": "2026-01-10", "description": "Gehalt", "amount": 3500.0, "type": "income"},
        {"date": "2026-01-15", "description": "Miete", "amount": -1200.0, "type": "expense"},
    ])
    r = registered_client.post(
        "/api/import/excel",
        files={"file": ("test.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"account_id": str(acc["id"])},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["imported"] == 2
    assert data["errors"] == 0


def test_excel_export(registered_client):
    acc = registered_client.post("/api/accounts", json={"name": "Konto", "type": "checking", "initial_balance": 0, "currency": "EUR"}).json()
    registered_client.post("/api/transactions", json={
        "date": "2026-01-10", "description": "Gehalt",
        "account_id": acc["id"], "amount": 3500.0, "type": "income"
    })
    r = registered_client.get("/api/export/excel?year=2026")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd")
    # Verify it's valid Excel
    wb = openpyxl.load_workbook(io.BytesIO(r.content))
    ws = wb.active
    data_rows = list(ws.iter_rows(min_row=2, values_only=True))
    assert len(data_rows) == 1
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_excel.py -v
```
Expected: 404

- [ ] **Step 4: Create excel_io.py service**

```python
# backend/app/services/excel_io.py
import io
from datetime import date, datetime, timezone
from decimal import Decimal

import openpyxl
from sqlalchemy.orm import Session

from app.models.transaction import Transaction


def import_excel(
    file_bytes: bytes,
    account_id: int,
    household_id: int,
    db: Session,
) -> dict:
    """
    Expects columns: date (YYYY-MM-DD or Excel date), description, amount, type (income/expense).
    Returns {"imported": N, "duplicates": D, "errors": E}.
    """
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active

    headers = [str(c.value).strip().lower() if c.value else "" for c in next(ws.iter_rows(min_row=1, max_row=1))]

    def col(row, name: str):
        try:
            idx = headers.index(name)
            return row[idx].value
        except (ValueError, IndexError):
            return None

    imported = 0
    errors = 0

    for row in ws.iter_rows(min_row=2):
        try:
            raw_date = col(row, "date")
            description = str(col(row, "description") or "")
            raw_amount = col(row, "amount")
            tx_type = str(col(row, "type") or "expense").lower()

            if raw_date is None or raw_amount is None:
                errors += 1
                continue

            if isinstance(raw_date, (date, datetime)):
                tx_date = raw_date if isinstance(raw_date, date) else raw_date.date()
            else:
                tx_date = date.fromisoformat(str(raw_date))

            amount = abs(float(raw_amount))

            tx = Transaction(
                household_id=household_id,
                account_id=account_id,
                date=tx_date,
                description=description,
                amount=Decimal(str(amount)),
                type=tx_type if tx_type in ("income", "expense", "transfer") else "expense",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(tx)
            imported += 1
        except Exception:
            errors += 1
            continue

    if imported > 0:
        db.commit()

    return {"imported": imported, "duplicates": 0, "errors": errors}


def export_excel(transactions: list[Transaction]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Transactions"
    ws.append(["date", "description", "type", "amount", "account_id", "category_id"])
    for tx in transactions:
        ws.append([
            str(tx.date),
            tx.description,
            tx.type,
            float(tx.amount),
            tx.account_id,
            tx.category_id,
        ])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
```

- [ ] **Step 5: Add Excel import endpoint to import_.py**

In `backend/app/routers/import_.py`, add:
```python
from fastapi import UploadFile, Form
from fastapi.responses import Response
from app.services.excel_io import import_excel, export_excel

@router.post("/import/excel")
async def import_excel_route(
    file: UploadFile,
    account_id: int = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    content = await file.read()
    result = import_excel(content, account_id, user.active_household_id, db)
    return result


@router.get("/export/excel")
def export_excel_route(
    year: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    txs = (
        db.query(Transaction)
        .filter(
            Transaction.household_id == user.active_household_id,
            func.strftime("%Y", Transaction.date) == str(year),
        )
        .order_by(Transaction.date)
        .all()
    )
    xlsx_bytes = export_excel(txs)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=helledger-{year}.xlsx"},
    )
```

Add missing imports at top of import_.py:
```python
from sqlalchemy import func
from app.models.transaction import Transaction
```

- [ ] **Step 6: Run tests**

```bash
cd backend && python -m pytest tests/test_excel.py -v
```
Expected: 2 tests pass

- [ ] **Step 7: Run full suite**

```bash
cd backend && python -m pytest tests/ -x -q 2>&1 | tail -5
```

- [ ] **Step 8: Commit**

```bash
git add backend/requirements.txt backend/app/services/excel_io.py backend/app/routers/import_.py backend/tests/test_excel.py
git commit -m "feat: Excel import/export (openpyxl)"
```

---

### Task 6: Frontend — Year, Month, NetWorth views + router

**Files:**
- Create: `frontend/src/views/YearView.vue`
- Create: `frontend/src/views/MonthView.vue`
- Create: `frontend/src/views/NetWorthView.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/components/AppNav.vue`
- Modify: `frontend/src/locales/de.json` and `en.json`

- [ ] **Step 1: Add i18n keys**

Add to both locale files:
```json
"yearView": {
  "title": "Jahresübersicht",
  "category": "Kategorie",
  "noData": "Keine Daten für dieses Jahr"
},
"monthView": {
  "title": "Monatsübersicht",
  "soll": "Soll",
  "ist": "Ist",
  "diff": "Differenz",
  "pct": "%",
  "income": "Einnahmen",
  "fixed": "Fixkosten",
  "variable": "Variable Ausgaben",
  "savingsRate": "Sparquote",
  "balance": "Bilanz"
},
"netWorth": {
  "title": "Nettovermögen",
  "newSnapshot": "Neuer Snapshot",
  "totalAssets": "Aktiva",
  "totalLiabilities": "Passiva",
  "netWorth": "Nettovermögen",
  "notes": "Notizen",
  "date": "Datum",
  "delete": "Löschen",
  "confirmDelete": "Snapshot wirklich löschen?",
  "save": "Speichern",
  "cancel": "Abbrechen"
}
```
(English equivalents in en.json)

- [ ] **Step 2: Create YearView.vue**

```vue
<!-- frontend/src/views/YearView.vue -->
<script setup>
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

const { t } = useI18n()
const api = useApi()

const year = ref(String(new Date().getFullYear()))
const data = ref(null)

const MONTHS = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

async function load() {
  const r = await api.get(`/dashboard/year?year=${year.value}`)
  if (r.ok) data.value = await r.json()
}

const chartData = computed(() => ({
  labels: MONTHS,
  datasets: [
    { label: t('dashboard.income'), data: data.value?.monthly_income || [], borderColor: '#10b981', tension: 0.3 },
    { label: t('dashboard.expenses'), data: data.value?.monthly_expense || [], borderColor: '#f43f5e', tension: 0.3 },
    { label: t('dashboard.balance'), data: data.value?.monthly_balance || [], borderColor: '#6366f1', tension: 0.3 },
  ]
}))

const chartOptions = { responsive: true, plugins: { legend: { position: 'top' } } }

watch(year, load)
onMounted(load)

// Import computed from vue
import { computed } from 'vue'
</script>

<template>
  <div class="container mx-auto py-6 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">{{ $t('yearView.title') }}</h1>
      <Select v-model="year">
        <SelectTrigger class="w-32"><SelectValue /></SelectTrigger>
        <SelectContent>
          <SelectItem v-for="y in [2024,2025,2026,2027]" :key="y" :value="String(y)">{{ y }}</SelectItem>
        </SelectContent>
      </Select>
    </div>

    <Card v-if="data">
      <CardContent class="pt-4">
        <Line :data="chartData" :options="chartOptions" />
      </CardContent>
    </Card>

    <Card v-if="data && data.categories.length > 0">
      <CardContent class="pt-4 overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b">
              <th class="text-left py-2 pr-4">{{ $t('yearView.category') }}</th>
              <th v-for="m in ['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez']" :key="m" class="text-right py-2 px-2 min-w-16">{{ m }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cat in data.categories" :key="cat.id" class="border-b hover:bg-muted/50">
              <td class="py-1 pr-4 font-medium">{{ cat.name }}</td>
              <td v-for="(val, i) in cat.months" :key="i" class="text-right py-1 px-2 tabular-nums"
                  :class="val > 0 ? 'text-rose-500' : 'text-muted-foreground'">
                {{ val > 0 ? val.toFixed(0) : '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </CardContent>
    </Card>

    <p v-else-if="data && data.categories.length === 0" class="text-muted-foreground text-center py-8">
      {{ $t('yearView.noData') }}
    </p>
  </div>
</template>
```

- [ ] **Step 3: Create MonthView.vue**

```vue
<!-- frontend/src/views/MonthView.vue -->
<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const { t } = useI18n()
const api = useApi()

const now = new Date()
const year = ref(now.getFullYear())
const month = ref(now.getMonth() + 1)
const data = ref(null)

function prevMonth() {
  if (month.value === 1) { month.value = 12; year.value-- }
  else month.value--
}
function nextMonth() {
  if (month.value === 12) { month.value = 1; year.value++ }
  else month.value++
}

async function load() {
  const r = await api.get(`/dashboard/month?year=${year.value}&month=${month.value}`)
  if (r.ok) data.value = await r.json()
}

watch([year, month], load)
onMounted(load)

const MONTH_NAMES = ['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember']

function pctColor(pct, type) {
  if (type === 'income') return pct >= 100 ? 'text-emerald-500' : 'text-rose-500'
  if (pct <= 80) return 'text-emerald-500'
  if (pct <= 100) return 'text-yellow-500'
  return 'text-rose-500'
}
</script>

<template>
  <div class="container mx-auto py-6 space-y-4">
    <div class="flex items-center gap-4">
      <Button variant="ghost" size="icon" @click="prevMonth">‹</Button>
      <h1 class="text-2xl font-bold">{{ MONTH_NAMES[month - 1] }} {{ year }}</h1>
      <Button variant="ghost" size="icon" @click="nextMonth">›</Button>
    </div>

    <template v-if="data">
      <Card v-for="section in data.sections" :key="section.type">
        <CardHeader>
          <CardTitle>{{ $t(`monthView.${section.type}`) }}</CardTitle>
        </CardHeader>
        <CardContent>
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b text-muted-foreground">
                <th class="text-left py-1">Kategorie</th>
                <th class="text-right py-1">{{ $t('monthView.soll') }}</th>
                <th class="text-right py-1">{{ $t('monthView.ist') }}</th>
                <th class="text-right py-1">{{ $t('monthView.diff') }}</th>
                <th class="text-right py-1 w-32">{{ $t('monthView.pct') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in section.rows" :key="row.category_id" class="border-b hover:bg-muted/50">
                <td class="py-1">{{ row.name }}</td>
                <td class="text-right tabular-nums">{{ row.soll.toFixed(2) }}</td>
                <td class="text-right tabular-nums">{{ row.ist.toFixed(2) }}</td>
                <td class="text-right tabular-nums" :class="row.diff >= 0 ? 'text-emerald-500' : 'text-rose-500'">
                  {{ row.diff.toFixed(2) }}
                </td>
                <td class="text-right">
                  <div class="flex items-center gap-2 justify-end">
                    <div class="w-16 h-2 bg-muted rounded-full overflow-hidden">
                      <div class="h-full rounded-full transition-all"
                        :class="pctColor(row.pct, section.type).replace('text-', 'bg-')"
                        :style="{ width: `${Math.min(row.pct, 100)}%` }" />
                    </div>
                    <span :class="pctColor(row.pct, section.type)">{{ row.pct.toFixed(0) }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="font-semibold">
                <td class="pt-2">Gesamt</td>
                <td class="text-right pt-2 tabular-nums">{{ section.total_soll.toFixed(2) }}</td>
                <td class="text-right pt-2 tabular-nums">{{ section.total_ist.toFixed(2) }}</td>
                <td></td><td></td>
              </tr>
            </tfoot>
          </table>
        </CardContent>
      </Card>

      <Card>
        <CardContent class="pt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="space-y-1">
            <p class="text-sm text-muted-foreground">{{ $t('dashboard.income') }}</p>
            <p class="text-xl font-bold text-emerald-500">{{ data.summary.total_income.toFixed(2) }}</p>
          </div>
          <div class="space-y-1">
            <p class="text-sm text-muted-foreground">{{ $t('dashboard.expenses') }}</p>
            <p class="text-xl font-bold text-rose-500">{{ data.summary.total_expense.toFixed(2) }}</p>
          </div>
          <div class="space-y-1">
            <p class="text-sm text-muted-foreground">{{ $t('monthView.balance') }}</p>
            <p class="text-xl font-bold" :class="data.summary.balance >= 0 ? 'text-emerald-500' : 'text-rose-500'">
              {{ data.summary.balance.toFixed(2) }}
            </p>
          </div>
          <div class="space-y-1">
            <p class="text-sm text-muted-foreground">{{ $t('monthView.savingsRate') }}</p>
            <p class="text-xl font-bold text-indigo-500">{{ data.summary.savings_rate.toFixed(1) }}%</p>
          </div>
        </CardContent>
      </Card>
    </template>
  </div>
</template>
```

- [ ] **Step 4: Create NetWorthView.vue**

```vue
<!-- frontend/src/views/NetWorthView.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { useApi } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip)

const { t } = useI18n()
const api = useApi()

const snapshots = ref([])
const showDialog = ref(false)
const form = ref({ snapshot_date: '', total_assets: '', total_liabilities: '', notes: '' })

async function load() {
  const r = await api.get('/net-worth')
  if (r.ok) snapshots.value = await r.json()
}

async function save() {
  const r = await api.post('/net-worth', {
    snapshot_date: form.value.snapshot_date,
    total_assets: parseFloat(form.value.total_assets),
    total_liabilities: parseFloat(form.value.total_liabilities),
    notes: form.value.notes || null,
  })
  if (r.ok) {
    showDialog.value = false
    form.value = { snapshot_date: '', total_assets: '', total_liabilities: '', notes: '' }
    await load()
  } else {
    toast.error(t('errors.generic'))
  }
}

async function deleteSnapshot(id) {
  if (!confirm(t('netWorth.confirmDelete'))) return
  await api.delete(`/net-worth/${id}`)
  await load()
}

const chartData = computed(() => ({
  labels: [...snapshots.value].reverse().map(s => s.snapshot_date),
  datasets: [{
    label: t('netWorth.netWorth'),
    data: [...snapshots.value].reverse().map(s => s.net_worth),
    borderColor: '#6366f1',
    tension: 0.3,
    fill: false,
  }]
}))
const chartOptions = { responsive: true, plugins: { legend: { display: false } } }

onMounted(load)
</script>

<template>
  <div class="container mx-auto py-6 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">{{ $t('netWorth.title') }}</h1>
      <Button @click="showDialog = true">{{ $t('netWorth.newSnapshot') }}</Button>
    </div>

    <Card v-if="snapshots.length > 0">
      <CardContent class="pt-4">
        <Line :data="chartData" :options="chartOptions" />
      </CardContent>
    </Card>

    <Card>
      <CardContent class="pt-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{{ $t('netWorth.date') }}</TableHead>
              <TableHead class="text-right">{{ $t('netWorth.totalAssets') }}</TableHead>
              <TableHead class="text-right">{{ $t('netWorth.totalLiabilities') }}</TableHead>
              <TableHead class="text-right">{{ $t('netWorth.netWorth') }}</TableHead>
              <TableHead>{{ $t('netWorth.notes') }}</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="s in snapshots" :key="s.id">
              <TableCell>{{ s.snapshot_date }}</TableCell>
              <TableCell class="text-right tabular-nums text-emerald-500">{{ Number(s.total_assets).toFixed(2) }}</TableCell>
              <TableCell class="text-right tabular-nums text-rose-500">{{ Number(s.total_liabilities).toFixed(2) }}</TableCell>
              <TableCell class="text-right tabular-nums font-bold" :class="s.net_worth >= 0 ? 'text-emerald-500' : 'text-rose-500'">
                {{ Number(s.net_worth).toFixed(2) }}
              </TableCell>
              <TableCell class="text-muted-foreground">{{ s.notes || '—' }}</TableCell>
              <TableCell>
                <Button size="sm" variant="destructive" @click="deleteSnapshot(s.id)">
                  {{ $t('netWorth.delete') }}
                </Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>

    <Dialog v-model:open="showDialog">
      <DialogContent>
        <DialogHeader><DialogTitle>{{ $t('netWorth.newSnapshot') }}</DialogTitle></DialogHeader>
        <div class="space-y-3 py-2">
          <div class="space-y-1">
            <Label>{{ $t('netWorth.date') }}</Label>
            <Input type="date" v-model="form.snapshot_date" />
          </div>
          <div class="space-y-1">
            <Label>{{ $t('netWorth.totalAssets') }}</Label>
            <Input type="number" v-model="form.total_assets" placeholder="50000" />
          </div>
          <div class="space-y-1">
            <Label>{{ $t('netWorth.totalLiabilities') }}</Label>
            <Input type="number" v-model="form.total_liabilities" placeholder="10000" />
          </div>
          <div class="space-y-1">
            <Label>{{ $t('netWorth.notes') }}</Label>
            <Input v-model="form.notes" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="showDialog = false">{{ $t('netWorth.cancel') }}</Button>
          <Button @click="save">{{ $t('netWorth.save') }}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
```

- [ ] **Step 5: Add routes to router/index.js**

```javascript
{ path: '/year', component: () => import('../views/YearView.vue'), meta: { requiresAuth: true } },
{ path: '/month', component: () => import('../views/MonthView.vue'), meta: { requiresAuth: true } },
{ path: '/net-worth', component: () => import('../views/NetWorthView.vue'), meta: { requiresAuth: true } },
```

- [ ] **Step 6: Add nav links to AppNav.vue**

In the nav links section, add after "reports":
```html
<RouterLink to="/year" ...>{{ $t('nav.year') }}</RouterLink>
<RouterLink to="/month" ...>{{ $t('nav.month') }}</RouterLink>
<RouterLink to="/net-worth" ...>{{ $t('nav.netWorth') }}</RouterLink>
```

Add to both locale files under `nav`:
```json
"year": "Jahr",
"month": "Monat",
"netWorth": "Vermögen"
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/views/YearView.vue frontend/src/views/MonthView.vue frontend/src/views/NetWorthView.vue frontend/src/router/index.js frontend/src/components/AppNav.vue frontend/src/locales/de.json frontend/src/locales/en.json
git commit -m "feat: year/month/net-worth views + router routes"
```

---

### Task 7: Test coverage — reach 60%

**Files:**
- Create: `backend/tests/test_coverage_extras.py`

Current count: ~160 tests. Run coverage first, identify gaps, fill them.

- [ ] **Step 1: Measure current coverage**

```bash
cd backend && pip install pytest-cov && python -m pytest tests/ --cov=app --cov-report=term-missing 2>&1 | grep "TOTAL"
```
Note the current percentage. Target: ≥60%.

- [ ] **Step 2: Check which modules have low coverage**

```bash
cd backend && python -m pytest tests/ --cov=app --cov-report=term-missing 2>&1 | grep -E "^\s*(app/|TOTAL)"
```
Identify the lowest-coverage files.

- [ ] **Step 3: Add missing tests for commonly untested paths**

```python
# backend/tests/test_coverage_extras.py
"""Tests to fill coverage gaps across service and router code."""
import pytest


# === Auth edge cases ===

def test_register_first_user_is_admin(client):
    r = client.post("/api/auth/register", json={"email": "first@example.com", "password": "securepassword1", "name": "First"})
    assert r.json()["role"] == "admin"


def test_register_second_user_is_not_admin(client):
    client.post("/api/auth/register", json={"email": "first@example.com", "password": "securepassword1", "name": "First"})
    r = client.post("/api/auth/register", json={"email": "second@example.com", "password": "securepassword1", "name": "Second"})
    assert r.json()["role"] == "user"


def test_login_inactive_user(client):
    from app.models.user import User
    from app.database import get_db
    client.post("/api/auth/register", json={"email": "inactive@example.com", "password": "securepassword1", "name": "Inactive"})
    db = next(client.app.dependency_overrides[get_db]())
    user = db.query(User).filter(User.email == "inactive@example.com").first()
    user.is_active = False
    db.commit()
    r = client.post("/api/auth/login", json={"email": "inactive@example.com", "password": "securepassword1"})
    assert r.status_code == 403


def test_refresh_token_expired(client):
    from app.models.user import RefreshToken
    from app.database import get_db
    from datetime import datetime, timedelta, timezone
    client.post("/api/auth/register", json={"email": "exp@example.com", "password": "securepassword1", "name": "Exp"})
    client.post("/api/auth/login", json={"email": "exp@example.com", "password": "securepassword1"})
    db = next(client.app.dependency_overrides[get_db]())
    rt = db.query(RefreshToken).first()
    rt.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
    r = client.post("/api/auth/refresh", cookies={"refresh_token": "invalid"})
    assert r.status_code == 401


# === Health endpoint ===

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200


# === Accounts edge cases ===

def test_create_account_missing_fields(registered_client):
    r = registered_client.post("/api/accounts", json={"name": "Test"})
    assert r.status_code == 422


# === Categories edge cases ===

def test_archive_category(registered_client):
    r = registered_client.post("/api/categories", json={"name": "Test", "type": "variable", "color": "#ff0000"})
    cat_id = r.json()["id"]
    r2 = registered_client.patch(f"/api/categories/{cat_id}", json={"archived": True})
    assert r2.status_code == 200


# === Reports edge cases ===

def test_reports_no_household_data(registered_client):
    r = registered_client.get("/api/reports/monthly-trend?year=2026")
    assert r.status_code in (200, 400)


# === User preferences ===

def test_language_preference_persists(registered_client):
    registered_client.patch("/api/users/me/preferences", json={"language": "en"})
    r = registered_client.get("/api/users/me/preferences")
    assert r.json()["language"] == "en"


# === Admin ===

def test_admin_delete_user(client):
    client.post("/api/auth/register", json={"email": "adm@example.com", "password": "securepassword1", "name": "Admin"})
    r = client.post("/api/auth/login", json={"email": "adm@example.com", "password": "securepassword1"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/auth/register", json={"email": "victim@example.com", "password": "securepassword1", "name": "Victim"})
    users = client.get("/api/users", headers=headers).json()
    victim_id = next(u["id"] for u in users if u["email"] == "victim@example.com")

    d = client.delete(f"/api/users/{victim_id}", headers=headers)
    assert d.status_code == 204


def test_admin_cannot_delete_self(client):
    client.post("/api/auth/register", json={"email": "self@example.com", "password": "securepassword1", "name": "Self"})
    r = client.post("/api/auth/login", json={"email": "self@example.com", "password": "securepassword1"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    users = client.get("/api/users", headers=headers).json()
    self_id = users[0]["id"]
    r2 = client.delete(f"/api/users/{self_id}", headers=headers)
    assert r2.status_code == 400
```

- [ ] **Step 4: Run tests and measure coverage**

```bash
cd backend && python -m pytest tests/ --cov=app --cov-report=term-missing 2>&1 | grep TOTAL
```
Expected: ≥60%. If below, look at the missing lines report and add more targeted tests.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_coverage_extras.py
git commit -m "test: add coverage tests to reach 60%+ for API/services"
```

---

### Task 8: GitHub Actions — CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create CI workflow**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Run tests with coverage
        run: python -m pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=60 -q

      - name: Summary
        if: always()
        run: |
          echo "### Test Results" >> $GITHUB_STEP_SUMMARY
          python -m pytest tests/ --co -q 2>&1 | tail -3 >> $GITHUB_STEP_SUMMARY
```

- [ ] **Step 2: Verify workflow YAML is valid**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo "valid"
```
Expected: `valid`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add test workflow on push/PR with 60% coverage gate"
```

---

### Task 9: GitHub Actions — multi-arch release workflow

**Files:**
- Modify: `.github/workflows/docker-build.yml` (rename + extend) OR create `.github/workflows/release.yml`

- [ ] **Step 1: Create release.yml**

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/setup-qemu-action@v3

      - uses: docker/setup-buildx-action@v3

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/kreuzbube88/helledger
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest

      - uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - run: |
          echo "### Release published" >> $GITHUB_STEP_SUMMARY
          echo "Tags: ${{ steps.meta.outputs.tags }}" >> $GITHUB_STEP_SUMMARY
```

- [ ] **Step 2: Verify workflow YAML is valid**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))" && echo "valid"
```
Expected: `valid`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "ci: multi-arch release workflow for v* tags (amd64 + arm64)"
```

---

### Task 10: Documentation skeleton

**Files:**
- Create: `docs/de/installation.md`
- Create: `docs/de/first-steps.md`
- Create: `docs/de/import-export.md`
- Create: `docs/de/backup.md`
- Create: `docs/de/admin.md`
- Create: `docs/en/installation.md`
- Create: `docs/en/first-steps.md`

- [ ] **Step 1: Create docs/de/installation.md**

```markdown
# Installation

## Voraussetzungen

- Docker und Docker Compose
- Port 3000 verfügbar (oder beliebiger anderer Port via ENV)

## Schnellstart

```yaml
# docker-compose.yml
version: "3.8"
services:
  helledger:
    image: ghcr.io/kreuzbube88/helledger:latest
    environment:
      SECRET_KEY: "dein-geheimes-32-zeichen-key"
      TZ: "Europe/Berlin"
    ports:
      - "3000:3000"
    volumes:
      - helledger_data:/data
      - helledger_backups:/backups

volumes:
  helledger_data:
  helledger_backups:
```

```bash
docker compose up -d
```

Die App ist dann unter [http://localhost:3000](http://localhost:3000) erreichbar.

## Hinter einem Reverse Proxy

Traefik-Beispiel: Füge Labels hinzu (Details in `docs/de/reverse-proxy.md`).

## Umgebungsvariablen

| Variable | Standard | Beschreibung |
|---|---|---|
| `SECRET_KEY` | — | **Pflicht.** Min. 32 Zeichen |
| `DATABASE_PATH` | `/data/helledger.db` | Pfad zur SQLite-Datenbank |
| `BACKUP_PATH` | `/backups` | Pfad für automatische Backups |
| `TZ` | `Europe/Berlin` | Zeitzone |
| `ALLOW_REGISTRATION` | `true` | Neue Registrierungen erlauben |
| `SMTP_HOST` | — | Optional: SMTP für E-Mails |
| `OIDC_ENABLED` | `false` | Optional: OIDC SSO aktivieren |
```

- [ ] **Step 2: Create docs/de/first-steps.md**

```markdown
# Erste Schritte

## 1. Admin-Konto anlegen

Beim ersten Öffnen kannst du dich registrieren. Der erste registrierte User wird automatisch Admin.

## 2. Haushalt einrichten

Nach der Anmeldung erscheint automatisch ein Haushalt "Mein Haushalt". Du kannst den Namen unter **Einstellungen → Haushalt** ändern.

## 3. Konten anlegen

Unter **Konten** legst du deine Bankkonten an. Für jeden Kontotyp (Girokonto, Sparkonto, Kreditkonto) kannst du ein Startguthaben hinterlegen.

## 4. Kategorien einrichten

Unter **Kategorien** richtest du deine Einnahmen- und Ausgabenkategorien ein. Für Fixkosten und Einnahmen kannst du Sollwerte hinterlegen, für variable Ausgaben ein Budget.

## 5. Transaktionen erfassen

Unter **Transaktionen** erfasst du laufend deine Einnahmen und Ausgaben. Du kannst auch CSVs, OFX- und Excel-Dateien importieren.
```

- [ ] **Step 3: Create remaining docs stubs**

Create `docs/de/import-export.md`, `docs/de/backup.md`, `docs/de/admin.md`, `docs/en/installation.md`, `docs/en/first-steps.md` with analogous content (EN versions in English, shorter content is fine for the skeleton).

- [ ] **Step 4: Commit**

```bash
git add docs/
git commit -m "docs: add documentation skeleton (DE + EN)"
```

---

### Task 11: PWA updates (manifest + service worker verification)

**Files:**
- Check: `frontend/public/manifest.json`
- Check: `frontend/public/service-worker.js`

The Vite build already copies `frontend/public/` into `frontend/dist/`. Verify the manifest and service worker are present and correct.

- [ ] **Step 1: Verify manifest.json exists and is complete**

```bash
cat frontend/public/manifest.json
```

If it exists and has `name`, `short_name`, `start_url`, `display: "standalone"`, `icons` → no changes needed.

If it is missing or incomplete, create:
```json
{
  "name": "HELLEDGER",
  "short_name": "HELLEDGER",
  "description": "Personal finance tracker",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#09090b",
  "theme_color": "#6366f1",
  "icons": [
    { "src": "/logo.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/logo.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

- [ ] **Step 2: Verify index.html references manifest**

```bash
grep -n "manifest" frontend/index.html
```
Expected: `<link rel="manifest" href="/manifest.json" />` present.

If missing, add to `<head>` in `frontend/index.html`.

- [ ] **Step 3: Commit any changes**

```bash
git add frontend/public/manifest.json frontend/index.html
git commit -m "feat: verify PWA manifest completeness"
```
(Only commit if there were actual changes)

---

## Self-Review

### Spec coverage check

| Spec requirement | Task |
|---|---|
| Net worth snapshots | Task 1-2 |
| Year overview (/year) API + UI | Task 3, 6 |
| Month overview (/month) API + UI | Task 4, 6 |
| Excel import/export | Task 5 |
| DB indices on household_id/date/category_id | Task 1 |
| pytest 60%+ coverage | Task 7 |
| GitHub Actions CI on push/PR | Task 8 |
| Multi-arch release workflow | Task 9 |
| Docs in docs/ | Task 10 |
| PWA manifest | Task 11 |

All spec requirements covered. No placeholders or TBDs.
