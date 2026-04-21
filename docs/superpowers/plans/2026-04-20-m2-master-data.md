# HELLEDGER M2: Stammdaten — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Alle Stammdaten-Modelle anlegen (Haushalte, Konten, Kategorien, Sollwerte, Budgets), vollständige CRUD-API, und Frontend-Seiten für Konten, Kategorien und Haushaltsverwaltung.

**Architecture:** Backend first — Models → Migration → Schemas → Router+Tests pro Domäne → Frontend. Alle Endpunkte lesen `active_household_id` aus dem eingeloggten User. Einzelne Alembic-Migration `002_master_data.py`. Household wird automatisch bei Registrierung angelegt.

**Tech Stack:** Python 3.12, FastAPI 0.115, SQLAlchemy 2.0 (Mapped[T]/mapped_column), Alembic, Pydantic v2 (`@field_serializer`, `model_rebuild()`), SQLite, Vanilla JS ES modules, Tailwind CDN.

**DOM Safety Rule:** `innerHTML` is used ONLY for fully static developer-authored HTML (no `${...}` template interpolation). All user-supplied values (names, amounts, colors, IDs) are written via `textContent`, `setAttribute`, or `.style.*` after the static structure is set.

---

## File Structure

**Create:**
- `backend/app/models/household.py`
- `backend/alembic/versions/002_master_data.py`
- `backend/app/schemas/households.py`
- `backend/app/schemas/accounts.py`
- `backend/app/schemas/categories.py`
- `backend/app/schemas/expected_values.py`
- `backend/app/schemas/budgets.py`
- `backend/app/routers/households.py`
- `backend/app/routers/accounts.py`
- `backend/app/routers/categories.py`
- `backend/app/routers/expected_values.py`
- `backend/app/routers/budgets.py`
- `backend/tests/test_households.py`
- `backend/tests/test_accounts.py`
- `backend/tests/test_categories.py`
- `backend/tests/test_expected_values.py`
- `backend/tests/test_budgets.py`
- `frontend/js/nav.js`
- `frontend/js/views/accounts.js`
- `frontend/js/views/categories.js`
- `frontend/js/views/settings.js`

**Modify:**
- `backend/app/models/user.py`
- `backend/app/models/__init__.py`
- `backend/alembic/env.py`
- `backend/app/schemas/auth.py`
- `backend/app/routers/auth.py`
- `backend/app/main.py`
- `backend/tests/conftest.py`
- `frontend/locales/de.json`
- `frontend/locales/en.json`
- `frontend/index.html`
- `frontend/js/views/dashboard.js`

---

## Task 1: Data Models

**Files:**
- Create: `backend/app/models/household.py`
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write `backend/app/models/household.py`**

```python
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Integer,
    Numeric, String, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Household(Base):
    __tablename__ = "households"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class HouseholdMember(Base):
    __tablename__ = "household_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    __table_args__ = (UniqueConstraint("household_id", "user_id"),)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    account_type: Mapped[str] = mapped_column(String(20))
    starting_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    category_type: Mapped[str] = mapped_column(String(20))
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class ExpectedValue(Base):
    __tablename__ = "expected_values"

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

- [ ] **Step 2: Replace `backend/app/models/user.py`** — `active_household_id` hinzufügen

```python
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="user")
    language: Mapped[str] = mapped_column(String(5), default="de")
    active_household_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("households.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    user: Mapped[User] = relationship(back_populates="refresh_tokens")
```

- [ ] **Step 3: Replace `backend/app/models/__init__.py`**

```python
from app.models.user import User, RefreshToken
from app.models.household import (
    Household, HouseholdMember, Account, Category, ExpectedValue, Budget
)

__all__ = [
    "User", "RefreshToken",
    "Household", "HouseholdMember", "Account", "Category",
    "ExpectedValue", "Budget",
]
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add M2 data models (households, accounts, categories, expected_values, budgets)"
```

---

## Task 2: Alembic Migration 002

**Files:**
- Create: `backend/alembic/versions/002_master_data.py`
- Modify: `backend/alembic/env.py`

- [ ] **Step 1: Update `backend/alembic/env.py`** — Zeile 11 ändern

From:
```python
from app.models import user  # noqa: F401
```
To:
```python
from app.models import user, household  # noqa: F401
```

- [ ] **Step 2: Write `backend/alembic/versions/002_master_data.py`**

```python
"""master data: households, accounts, categories, expected_values, budgets

Revision ID: 002
Revises: 001
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "households",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_households_owner_id", "households", ["owner_id"])

    op.create_table(
        "household_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("household_id", "user_id"),
    )
    op.create_index("ix_household_members_household_id", "household_members", ["household_id"])
    op.create_index("ix_household_members_user_id", "household_members", ["user_id"])

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("account_type", sa.String(length=20), nullable=False),
        sa.Column("starting_balance", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
        sa.Column("archived", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_accounts_household_id", "accounts", ["household_id"])

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category_type", sa.String(length=20), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("archived", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_household_id", "categories", ["household_id"])
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])

    op.create_table(
        "expected_values",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expected_values_household_id", "expected_values", ["household_id"])
    op.create_index("ix_expected_values_category_id", "expected_values", ["category_id"])

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("household_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_budgets_household_id", "budgets", ["household_id"])
    op.create_index("ix_budgets_category_id", "budgets", ["category_id"])

    op.add_column("users", sa.Column("active_household_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "active_household_id")
    op.drop_table("budgets")
    op.drop_table("expected_values")
    op.drop_table("categories")
    op.drop_table("accounts")
    op.drop_table("household_members")
    op.drop_table("households")
```

- [ ] **Step 3: Verify migration**

```bash
cd backend
SECRET_KEY=test alembic upgrade head
```

Expected last line: `INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, master data: ...`

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/
git commit -m "feat: add alembic migration 002 for M2 master data tables"
```

---

## Task 3: Schemas

**Files:** Create all 5 schema files.

- [ ] **Step 1: Write `backend/app/schemas/households.py`**

```python
from datetime import datetime
from pydantic import BaseModel


class HouseholdCreate(BaseModel):
    name: str


class HouseholdUpdate(BaseModel):
    name: str | None = None


class HouseholdResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class MemberCreate(BaseModel):
    email: str


class MemberUpdate(BaseModel):
    role: str


class MemberDetailResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: str
    created_at: datetime
    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Write `backend/app/schemas/accounts.py`**

```python
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_serializer


class AccountCreate(BaseModel):
    name: str
    account_type: str
    starting_balance: Decimal
    currency: str = "EUR"


class AccountUpdate(BaseModel):
    name: str | None = None
    account_type: str | None = None
    starting_balance: Decimal | None = None
    currency: str | None = None


class AccountResponse(BaseModel):
    id: int
    household_id: int
    name: str
    account_type: str
    starting_balance: Decimal
    currency: str
    archived: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

    @field_serializer("starting_balance")
    def serialize_balance(self, v: Decimal) -> str:
        return f"{v:.2f}"
```

- [ ] **Step 3: Write `backend/app/schemas/categories.py`**

```python
from datetime import datetime
from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    category_type: str
    parent_id: int | None = None
    color: str | None = None
    icon: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    category_type: str | None = None
    parent_id: int | None = None
    color: str | None = None
    icon: str | None = None


class CategoryResponse(BaseModel):
    id: int
    household_id: int
    name: str
    category_type: str
    parent_id: int | None
    color: str | None
    icon: str | None
    archived: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CategoryTreeNode(BaseModel):
    id: int
    name: str
    category_type: str
    parent_id: int | None
    color: str | None
    icon: str | None
    archived: bool
    children: list["CategoryTreeNode"] = []
    model_config = {"from_attributes": True}


CategoryTreeNode.model_rebuild()
```

- [ ] **Step 4: Write `backend/app/schemas/expected_values.py`**

```python
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, field_serializer


class ExpectedValueCreate(BaseModel):
    category_id: int
    amount: Decimal
    valid_from: date


class ExpectedValueUpdate(BaseModel):
    amount: Decimal | None = None
    valid_from: date | None = None
    valid_until: date | None = None


class ExpectedValueResponse(BaseModel):
    id: int
    household_id: int
    category_id: int
    amount: Decimal
    valid_from: date
    valid_until: date | None
    created_at: datetime
    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal) -> str:
        return f"{v:.2f}"
```

- [ ] **Step 5: Write `backend/app/schemas/budgets.py`**

```python
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, field_serializer


class BudgetCreate(BaseModel):
    category_id: int
    amount: Decimal
    valid_from: date


class BudgetUpdate(BaseModel):
    amount: Decimal | None = None
    valid_from: date | None = None
    valid_until: date | None = None


class BudgetResponse(BaseModel):
    id: int
    household_id: int
    category_id: int
    amount: Decimal
    valid_from: date
    valid_until: date | None
    created_at: datetime
    model_config = {"from_attributes": True}

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal) -> str:
        return f"{v:.2f}"
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add M2 schemas (households, accounts, categories, expected_values, budgets)"
```

---

## Task 4: conftest.py Extensions

**Files:** Modify `backend/tests/conftest.py`

- [ ] **Step 1: Replace `backend/tests/conftest.py`**

```python
import os

# Must be before any app import
os.environ["SECRET_KEY"] = "test-secret-key-minimum-32-chars!!"
os.environ["DATABASE_PATH"] = ":memory:"
os.environ["TESTING"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


def _make_engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _setup_override(engine) -> None:
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def client():
    engine = _make_engine()
    Base.metadata.create_all(engine)
    _setup_override(engine)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def _shared_engine():
    engine = _make_engine()
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def registered_client(_shared_engine):
    _setup_override(_shared_engine)
    with TestClient(app) as c:
        c.post("/api/auth/register", json={
            "email": "usera@example.com",
            "password": "securepassword1",
            "name": "User A",
        })
        r = c.post("/api/auth/login", json={
            "email": "usera@example.com",
            "password": "securepassword1",
        })
        c.headers.update(auth_headers(r.json()["access_token"]))
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def second_user_client(_shared_engine, registered_client):
    # dependency override already active via registered_client
    with TestClient(app) as c:
        c.post("/api/auth/register", json={
            "email": "userb@example.com",
            "password": "securepassword1",
            "name": "User B",
        })
        r = c.post("/api/auth/login", json={
            "email": "userb@example.com",
            "password": "securepassword1",
        })
        c.headers.update(auth_headers(r.json()["access_token"]))
        yield c
```

- [ ] **Step 2: Run existing tests — alle müssen bestehen**

```bash
cd backend && pytest -v
```

Expected: alle 21 bisherigen Tests PASSED.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/conftest.py
git commit -m "feat: extend conftest with registered_client, second_user_client, auth_headers"
```

---

## Task 5: UserResponse Update + Register Auto-Household

**Files:** Modify `backend/app/schemas/auth.py`, `backend/app/routers/auth.py`

- [ ] **Step 1: Write failing tests** — am Ende von `backend/tests/test_auth.py` anhängen

```python
def test_register_creates_household(client):
    r = client.post("/api/auth/register", json={
        "email": "h@example.com", "password": "securepassword1", "name": "H"
    })
    assert r.status_code == 201
    assert r.json()["active_household_id"] is not None


def test_login_me_has_active_household(client):
    client.post("/api/auth/register", json={
        "email": "h@example.com", "password": "securepassword1", "name": "H"
    })
    r = client.post("/api/auth/login", json={
        "email": "h@example.com", "password": "securepassword1"
    })
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["active_household_id"] is not None
```

- [ ] **Step 2: Run — expect FAILED**

```bash
cd backend && pytest tests/test_auth.py::test_register_creates_household -v
```

Expected: `KeyError: 'active_household_id'` or assertion error.

- [ ] **Step 3: Replace `backend/app/schemas/auth.py`**

```python
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 12:
            raise ValueError("password must be at least 12 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    language: str
    active_household_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Replace `backend/app/routers/auth.py`** — auto-Haushalt bei Register

```python
import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.jwt import create_access_token, create_refresh_token
from app.auth.password import hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.models.user import RefreshToken, User
from app.models.household import Household, HouseholdMember
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(status_code=403, detail="registration_disabled")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="email_taken")
    is_first = db.query(User).count() == 0
    role = "admin" if (is_first and settings.FIRST_USER_IS_ADMIN) else "user"
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        role=role,
        language=settings.DEFAULT_LANGUAGE,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.flush()  # ergibt user.id ohne commit

    household_name = "Mein Haushalt" if user.language == "de" else "My Household"
    now = datetime.now(timezone.utc)
    household = Household(
        name=household_name,
        owner_id=user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(household)
    db.flush()  # ergibt household.id

    db.add(HouseholdMember(
        household_id=household.id,
        user_id=user.id,
        role="owner",
        created_at=now,
    ))
    user.active_household_id = household.id
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    user.last_login = datetime.now(timezone.utc)
    raw_refresh, refresh_hash = create_refresh_token()
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=expires,
        created_at=datetime.now(timezone.utc),
    ))
    db.commit()
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="missing_refresh_token")
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if rt is None or rt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="invalid_refresh_token")
    return TokenResponse(access_token=create_access_token(rt.user_id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if refresh_token:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).delete()
        db.commit()
    response.delete_cookie("refresh_token")
```

- [ ] **Step 5: Run all auth tests**

```bash
cd backend && pytest tests/test_auth.py -v
```

Expected: alle 23 Tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/auth.py backend/app/routers/auth.py
git commit -m "feat: auto-create household on register, add active_household_id to UserResponse"
```

---

## Task 6: Households Router

**Files:**
- Create: `backend/tests/test_households.py`
- Create: `backend/app/routers/households.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write `backend/tests/test_households.py`**

```python
def test_list_households_returns_own(registered_client):
    r = registered_client.get("/api/households")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["name"] in ("Mein Haushalt", "My Household")


def test_create_household(registered_client):
    r = registered_client.post("/api/households", json={"name": "Zweithaushalt"})
    assert r.status_code == 201
    assert r.json()["name"] == "Zweithaushalt"


def test_create_household_requires_auth(client):
    r = client.post("/api/households", json={"name": "X"})
    assert r.status_code == 403


def test_rename_household_owner(registered_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = registered_client.patch(f"/api/households/{hh_id}", json={"name": "Umbenannt"})
    assert r.status_code == 200
    assert r.json()["name"] == "Umbenannt"


def test_rename_household_forbidden_for_non_owner(registered_client, second_user_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = second_user_client.patch(f"/api/households/{hh_id}", json={"name": "X"})
    assert r.status_code == 403


def test_delete_last_household_forbidden(registered_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = registered_client.delete(f"/api/households/{hh_id}")
    assert r.status_code == 400
    assert r.json()["detail"] == "cannot_delete_last_household"


def test_delete_household(registered_client):
    registered_client.post("/api/households", json={"name": "Zweiter"})
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = registered_client.delete(f"/api/households/{hh_id}")
    assert r.status_code == 204


def test_activate_household(registered_client):
    r2 = registered_client.post("/api/households", json={"name": "Zweiter"})
    hh2_id = r2.json()["id"]
    r = registered_client.post(f"/api/households/{hh2_id}/activate")
    assert r.status_code == 200
    me = registered_client.get("/api/auth/me").json()
    assert me["active_household_id"] == hh2_id


def test_activate_foreign_household_forbidden(registered_client, second_user_client):
    hh_id = second_user_client.get("/api/households").json()[0]["id"]
    r = registered_client.post(f"/api/households/{hh_id}/activate")
    assert r.status_code == 403


def test_list_members(registered_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = registered_client.get(f"/api/households/{hh_id}/members")
    assert r.status_code == 200
    members = r.json()
    assert len(members) == 1
    assert members[0]["role"] == "owner"


def test_add_member(registered_client, second_user_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = registered_client.post(
        f"/api/households/{hh_id}/members",
        json={"email": "userb@example.com"},
    )
    assert r.status_code == 201
    members = registered_client.get(f"/api/households/{hh_id}/members").json()
    assert len(members) == 2


def test_add_nonexistent_member(registered_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    r = registered_client.post(
        f"/api/households/{hh_id}/members",
        json={"email": "nobody@example.com"},
    )
    assert r.status_code == 404


def test_remove_member(registered_client, second_user_client):
    hh_id = registered_client.get("/api/households").json()[0]["id"]
    registered_client.post(
        f"/api/households/{hh_id}/members",
        json={"email": "userb@example.com"},
    )
    me_b = second_user_client.get("/api/auth/me").json()
    r = registered_client.delete(f"/api/households/{hh_id}/members/{me_b['id']}")
    assert r.status_code == 204


def test_household_isolation(registered_client, second_user_client):
    hh_a = registered_client.get("/api/households").json()[0]["id"]
    hh_b = second_user_client.get("/api/households").json()[0]["id"]
    assert hh_a != hh_b
    r = second_user_client.get(f"/api/households/{hh_a}/members")
    assert r.status_code == 403
```

- [ ] **Step 2: Run — expect 404 errors (router not yet registered)**

```bash
cd backend && pytest tests/test_households.py -v 2>&1 | head -20
```

- [ ] **Step 3: Write `backend/app/routers/households.py`**

```python
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.household import Household, HouseholdMember
from app.schemas.households import (
    HouseholdCreate, HouseholdUpdate, HouseholdResponse,
    MemberCreate, MemberUpdate, MemberDetailResponse,
)

router = APIRouter(prefix="/households")


def _require_member(household_id: int, user: User, db: Session) -> HouseholdMember:
    m = db.query(HouseholdMember).filter_by(
        household_id=household_id, user_id=user.id
    ).first()
    if m is None:
        raise HTTPException(status_code=403, detail="forbidden")
    return m


def _require_owner(household_id: int, user: User, db: Session) -> Household:
    hh = db.get(Household, household_id)
    if hh is None:
        raise HTTPException(status_code=404, detail="not_found")
    if hh.owner_id != user.id:
        raise HTTPException(status_code=403, detail="forbidden")
    return hh


@router.get("", response_model=list[HouseholdResponse])
async def list_households(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memberships = db.query(HouseholdMember).filter_by(user_id=user.id).all()
    ids = [m.household_id for m in memberships]
    return db.query(Household).filter(Household.id.in_(ids)).all()


@router.post("", response_model=HouseholdResponse, status_code=201)
async def create_household(
    body: HouseholdCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    hh = Household(name=body.name, owner_id=user.id, created_at=now, updated_at=now)
    db.add(hh)
    db.flush()
    db.add(HouseholdMember(
        household_id=hh.id, user_id=user.id, role="owner", created_at=now
    ))
    db.commit()
    db.refresh(hh)
    return hh


@router.patch("/{household_id}", response_model=HouseholdResponse)
async def rename_household(
    household_id: int,
    body: HouseholdUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh = _require_owner(household_id, user, db)
    if body.name is not None:
        hh.name = body.name
        hh.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(hh)
    return hh


@router.delete("/{household_id}", status_code=204)
async def delete_household(
    household_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh = _require_owner(household_id, user, db)
    total = db.query(HouseholdMember).filter_by(user_id=user.id).count()
    if total <= 1:
        raise HTTPException(status_code=400, detail="cannot_delete_last_household")
    db.delete(hh)
    db.commit()


@router.post("/{household_id}/activate", response_model=dict)
async def activate_household(
    household_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_member(household_id, user, db)
    user.active_household_id = household_id
    db.commit()
    return {"active_household_id": household_id}


@router.get("/{household_id}/members", response_model=list[MemberDetailResponse])
async def list_members(
    household_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_member(household_id, user, db)
    from app.models.user import User as UserModel
    rows = (
        db.query(HouseholdMember, UserModel)
        .join(UserModel, HouseholdMember.user_id == UserModel.id)
        .filter(HouseholdMember.household_id == household_id)
        .all()
    )
    return [
        MemberDetailResponse(
            user_id=m.user_id,
            name=u.name,
            email=u.email,
            role=m.role,
            created_at=m.created_at,
        )
        for m, u in rows
    ]


@router.post("/{household_id}/members", response_model=MemberDetailResponse, status_code=201)
async def add_member(
    household_id: int,
    body: MemberCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_owner(household_id, user, db)
    from app.models.user import User as UserModel
    target = db.query(UserModel).filter_by(email=body.email).first()
    if target is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    existing = db.query(HouseholdMember).filter_by(
        household_id=household_id, user_id=target.id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="already_member")
    now = datetime.now(timezone.utc)
    m = HouseholdMember(
        household_id=household_id, user_id=target.id, role="member", created_at=now
    )
    db.add(m)
    db.commit()
    return MemberDetailResponse(
        user_id=target.id, name=target.name, email=target.email,
        role="member", created_at=now,
    )


@router.patch("/{household_id}/members/{user_id}", response_model=MemberDetailResponse)
async def update_member_role(
    household_id: int,
    user_id: int,
    body: MemberUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_owner(household_id, user, db)
    from app.models.user import User as UserModel
    m = db.query(HouseholdMember).filter_by(
        household_id=household_id, user_id=user_id
    ).first()
    if m is None:
        raise HTTPException(status_code=404, detail="not_found")
    target = db.get(UserModel, user_id)
    m.role = body.role
    db.commit()
    return MemberDetailResponse(
        user_id=target.id, name=target.name, email=target.email,
        role=m.role, created_at=m.created_at,
    )


@router.delete("/{household_id}/members/{user_id}", status_code=204)
async def remove_member(
    household_id: int,
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_owner(household_id, user, db)
    m = db.query(HouseholdMember).filter_by(
        household_id=household_id, user_id=user_id
    ).first()
    if m is None:
        raise HTTPException(status_code=404, detail="not_found")
    db.delete(m)
    db.commit()
```

- [ ] **Step 4: Register router — append to `backend/app/main.py` imports and include_router**

After the existing `from app.routers import auth as auth_router` line:
```python
from app.routers import households as households_router
```

After `app.include_router(auth_router.router, prefix="/api")`:
```python
app.include_router(households_router.router, prefix="/api")
```

- [ ] **Step 5: Run household tests**

```bash
cd backend && pytest tests/test_households.py -v
```

Expected: alle 14 Tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/households.py backend/tests/test_households.py backend/app/main.py
git commit -m "feat: add households CRUD API with member management"
```

---

## Task 7: Accounts Router

**Files:**
- Create: `backend/tests/test_accounts.py`
- Create: `backend/app/routers/accounts.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write `backend/tests/test_accounts.py`**

```python
def _create_account(client, **kwargs):
    payload = {
        "name": "Girokonto",
        "account_type": "checking",
        "starting_balance": "1000.00",
        "currency": "EUR",
        **kwargs,
    }
    return client.post("/api/accounts", json=payload)


def test_create_account(registered_client):
    r = _create_account(registered_client)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Girokonto"
    assert body["starting_balance"] == "1000.00"
    assert body["archived"] is False


def test_list_accounts(registered_client):
    _create_account(registered_client, name="A")
    _create_account(registered_client, name="B")
    r = registered_client.get("/api/accounts")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_excludes_archived_by_default(registered_client):
    r = _create_account(registered_client)
    acc_id = r.json()["id"]
    registered_client.delete(f"/api/accounts/{acc_id}")
    r2 = registered_client.get("/api/accounts")
    assert len(r2.json()) == 0


def test_list_includes_archived_when_requested(registered_client):
    r = _create_account(registered_client)
    acc_id = r.json()["id"]
    registered_client.delete(f"/api/accounts/{acc_id}")
    r2 = registered_client.get("/api/accounts?include_archived=true")
    assert len(r2.json()) == 1
    assert r2.json()[0]["archived"] is True


def test_get_account(registered_client):
    acc_id = _create_account(registered_client).json()["id"]
    r = registered_client.get(f"/api/accounts/{acc_id}")
    assert r.status_code == 200
    assert r.json()["id"] == acc_id


def test_patch_account(registered_client):
    acc_id = _create_account(registered_client).json()["id"]
    r = registered_client.patch(f"/api/accounts/{acc_id}", json={"name": "Sparkonto"})
    assert r.status_code == 200
    assert r.json()["name"] == "Sparkonto"


def test_delete_account_soft(registered_client):
    acc_id = _create_account(registered_client).json()["id"]
    r = registered_client.delete(f"/api/accounts/{acc_id}")
    assert r.status_code == 204
    r2 = registered_client.get(f"/api/accounts/{acc_id}")
    assert r2.json()["archived"] is True


def test_account_isolation(registered_client, second_user_client):
    acc_id = _create_account(registered_client).json()["id"]
    r = second_user_client.get(f"/api/accounts/{acc_id}")
    assert r.status_code == 404


def test_account_requires_auth(client):
    r = client.get("/api/accounts")
    assert r.status_code == 403
```

- [ ] **Step 2: Write `backend/app/routers/accounts.py`**

```python
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.household import Account
from app.schemas.accounts import AccountCreate, AccountUpdate, AccountResponse

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
```

- [ ] **Step 3: Register router in `backend/app/main.py`**

```python
from app.routers import accounts as accounts_router
# ...
app.include_router(accounts_router.router, prefix="/api")
```

- [ ] **Step 4: Run account tests**

```bash
cd backend && pytest tests/test_accounts.py -v
```

Expected: alle 9 Tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/accounts.py backend/tests/test_accounts.py backend/app/main.py
git commit -m "feat: add accounts CRUD API with soft-delete and household isolation"
```

---

## Task 8: Categories Router

**Files:**
- Create: `backend/tests/test_categories.py`
- Create: `backend/app/routers/categories.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write `backend/tests/test_categories.py`**

```python
def _create_cat(client, name="Fixkosten", cat_type="fixed", **kwargs):
    return client.post("/api/categories", json={
        "name": name, "category_type": cat_type, **kwargs,
    })


def test_create_category(registered_client):
    r = _create_cat(registered_client)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Fixkosten"
    assert body["archived"] is False
    assert body["parent_id"] is None


def test_list_categories_tree(registered_client):
    parent_id = _create_cat(registered_client, "Fixkosten", "fixed").json()["id"]
    _create_cat(registered_client, "Miete", "fixed", parent_id=parent_id)
    r = registered_client.get("/api/categories")
    assert r.status_code == 200
    tree = r.json()
    assert len(tree) == 1
    assert tree[0]["name"] == "Fixkosten"
    assert len(tree[0]["children"]) == 1
    assert tree[0]["children"][0]["name"] == "Miete"


def test_list_categories_by_type(registered_client):
    _create_cat(registered_client, "Gehalt", "income")
    _create_cat(registered_client, "Miete", "fixed")
    _create_cat(registered_client, "Lebensmittel", "variable")
    r = registered_client.get("/api/categories")
    names = [c["name"] for c in r.json()]
    assert "Gehalt" in names and "Miete" in names and "Lebensmittel" in names


def test_get_category(registered_client):
    cat_id = _create_cat(registered_client).json()["id"]
    r = registered_client.get(f"/api/categories/{cat_id}")
    assert r.status_code == 200
    assert r.json()["id"] == cat_id


def test_patch_category(registered_client):
    cat_id = _create_cat(registered_client).json()["id"]
    r = registered_client.patch(f"/api/categories/{cat_id}", json={"name": "Neu", "color": "#ff0000"})
    assert r.status_code == 200
    assert r.json()["name"] == "Neu"
    assert r.json()["color"] == "#ff0000"


def test_patch_category_parent(registered_client):
    p_id = _create_cat(registered_client, "Eltern", "fixed").json()["id"]
    c_id = _create_cat(registered_client, "Kind", "fixed").json()["id"]
    r = registered_client.patch(f"/api/categories/{c_id}", json={"parent_id": p_id})
    assert r.status_code == 200
    assert r.json()["parent_id"] == p_id


def test_archive_category(registered_client):
    cat_id = _create_cat(registered_client).json()["id"]
    r = registered_client.delete(f"/api/categories/{cat_id}")
    assert r.status_code == 204
    r2 = registered_client.get(f"/api/categories/{cat_id}")
    assert r2.json()["archived"] is True


def test_archived_excluded_from_tree_by_default(registered_client):
    cat_id = _create_cat(registered_client).json()["id"]
    registered_client.delete(f"/api/categories/{cat_id}")
    r = registered_client.get("/api/categories")
    assert len(r.json()) == 0


def test_category_isolation(registered_client, second_user_client):
    cat_id = _create_cat(registered_client).json()["id"]
    r = second_user_client.get(f"/api/categories/{cat_id}")
    assert r.status_code == 404
```

- [ ] **Step 2: Write `backend/app/routers/categories.py`**

```python
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.household import Category
from app.schemas.categories import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTreeNode
)

router = APIRouter(prefix="/categories")


def _require_active_hh(user: User) -> int:
    if user.active_household_id is None:
        raise HTTPException(status_code=400, detail="no_active_household")
    return user.active_household_id


def _get_category(category_id: int, hh_id: int, db: Session) -> Category:
    cat = db.get(Category, category_id)
    if cat is None or cat.household_id != hh_id:
        raise HTTPException(status_code=404, detail="not_found")
    return cat


def _build_tree(
    categories: list[Category], parent_id: int | None
) -> list[CategoryTreeNode]:
    result = []
    for cat in categories:
        if cat.parent_id == parent_id:
            result.append(CategoryTreeNode(
                id=cat.id,
                name=cat.name,
                category_type=cat.category_type,
                parent_id=cat.parent_id,
                color=cat.color,
                icon=cat.icon,
                archived=cat.archived,
                children=_build_tree(categories, cat.id),
            ))
    return result


@router.get("", response_model=list[CategoryTreeNode])
async def list_categories(
    include_archived: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    q = db.query(Category).filter(Category.household_id == hh_id)
    if not include_archived:
        q = q.filter(Category.archived.is_(False))
    return _build_tree(q.all(), None)


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    body: CategoryCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    now = datetime.now(timezone.utc)
    cat = Category(
        household_id=hh_id,
        name=body.name,
        category_type=body.category_type,
        parent_id=body.parent_id,
        color=body.color,
        icon=body.icon,
        created_at=now,
        updated_at=now,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    return _get_category(category_id, hh_id, db)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    body: CategoryUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    cat = _get_category(category_id, hh_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    cat.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=204)
async def archive_category(
    category_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    cat = _get_category(category_id, hh_id, db)
    cat.archived = True
    cat.updated_at = datetime.now(timezone.utc)
    db.commit()
```

- [ ] **Step 3: Register router in `backend/app/main.py`**

```python
from app.routers import categories as categories_router
# ...
app.include_router(categories_router.router, prefix="/api")
```

- [ ] **Step 4: Run category tests**

```bash
cd backend && pytest tests/test_categories.py -v
```

Expected: alle 9 Tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/categories.py backend/tests/test_categories.py backend/app/main.py
git commit -m "feat: add categories CRUD API with tree view and soft-delete"
```

---

## Task 9: Expected Values Router

**Files:**
- Create: `backend/tests/test_expected_values.py`
- Create: `backend/app/routers/expected_values.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write `backend/tests/test_expected_values.py`**

```python
def _create_cat(client, name="Miete", cat_type="fixed"):
    return client.post("/api/categories", json={
        "name": name, "category_type": cat_type
    }).json()["id"]


def _create_ev(client, category_id, amount="1200.00", valid_from="2026-01-01"):
    return client.post("/api/expected-values", json={
        "category_id": category_id, "amount": amount, "valid_from": valid_from,
    })


def test_create_expected_value(registered_client):
    cat_id = _create_cat(registered_client)
    r = _create_ev(registered_client, cat_id)
    assert r.status_code == 201
    body = r.json()
    assert body["amount"] == "1200.00"
    assert body["valid_from"] == "2026-01-01"
    assert body["valid_until"] is None


def test_list_expected_values(registered_client):
    cat_id = _create_cat(registered_client)
    _create_ev(registered_client, cat_id)
    r = registered_client.get("/api/expected-values")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_list_by_category(registered_client):
    cat1 = _create_cat(registered_client, "Miete")
    cat2 = _create_cat(registered_client, "Strom")
    _create_ev(registered_client, cat1)
    _create_ev(registered_client, cat2)
    r = registered_client.get(f"/api/expected-values?category_id={cat1}")
    assert len(r.json()) == 1
    assert r.json()[0]["category_id"] == cat1


def test_autoclose_open_entry(registered_client):
    cat_id = _create_cat(registered_client)
    _create_ev(registered_client, cat_id, "1000.00", "2026-01-01")
    r2 = _create_ev(registered_client, cat_id, "1200.00", "2026-04-01")
    assert r2.status_code == 201
    all_evs = registered_client.get(f"/api/expected-values?category_id={cat_id}").json()
    assert len(all_evs) == 2
    closed = next(e for e in all_evs if e["amount"] == "1000.00")
    assert closed["valid_until"] == "2026-03-31"
    open_ev = next(e for e in all_evs if e["amount"] == "1200.00")
    assert open_ev["valid_until"] is None


def test_patch_expected_value(registered_client):
    cat_id = _create_cat(registered_client)
    ev_id = _create_ev(registered_client, cat_id).json()["id"]
    r = registered_client.patch(f"/api/expected-values/{ev_id}", json={"amount": "999.00"})
    assert r.status_code == 200
    assert r.json()["amount"] == "999.00"


def test_delete_expected_value(registered_client):
    cat_id = _create_cat(registered_client)
    ev_id = _create_ev(registered_client, cat_id).json()["id"]
    r = registered_client.delete(f"/api/expected-values/{ev_id}")
    assert r.status_code == 204
    assert len(registered_client.get("/api/expected-values").json()) == 0


def test_expected_value_isolation(registered_client, second_user_client):
    cat_id = _create_cat(registered_client)
    _create_ev(registered_client, cat_id)
    r = second_user_client.get("/api/expected-values")
    assert len(r.json()) == 0


def test_expected_value_wrong_category(registered_client, second_user_client):
    cat_b = _create_cat(second_user_client, "Fremd")
    r = _create_ev(registered_client, cat_b)
    assert r.status_code == 404
```

- [ ] **Step 2: Write `backend/app/routers/expected_values.py`**

```python
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
```

- [ ] **Step 3: Register router in `backend/app/main.py`**

```python
from app.routers import expected_values as ev_router
# ...
app.include_router(ev_router.router, prefix="/api")
```

- [ ] **Step 4: Run tests**

```bash
cd backend && pytest tests/test_expected_values.py -v
```

Expected: alle 8 Tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/expected_values.py backend/tests/test_expected_values.py backend/app/main.py
git commit -m "feat: add expected_values API with autoclose logic"
```

---

## Task 10: Budgets Router

**Files:**
- Create: `backend/tests/test_budgets.py`
- Create: `backend/app/routers/budgets.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write `backend/tests/test_budgets.py`**

```python
def _create_cat(client, name="Lebensmittel"):
    return client.post("/api/categories", json={
        "name": name, "category_type": "variable"
    }).json()["id"]


def _create_budget(client, category_id, amount="300.00", valid_from="2026-01-01"):
    return client.post("/api/budgets", json={
        "category_id": category_id, "amount": amount, "valid_from": valid_from,
    })


def test_create_budget(registered_client):
    cat_id = _create_cat(registered_client)
    r = _create_budget(registered_client, cat_id)
    assert r.status_code == 201
    assert r.json()["amount"] == "300.00"
    assert r.json()["valid_until"] is None


def test_list_budgets(registered_client):
    cat_id = _create_cat(registered_client)
    _create_budget(registered_client, cat_id)
    r = registered_client.get("/api/budgets")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_autoclose_open_budget(registered_client):
    cat_id = _create_cat(registered_client)
    _create_budget(registered_client, cat_id, "300.00", "2026-01-01")
    _create_budget(registered_client, cat_id, "400.00", "2026-04-01")
    all_b = registered_client.get(f"/api/budgets?category_id={cat_id}").json()
    assert len(all_b) == 2
    closed = next(b for b in all_b if b["amount"] == "300.00")
    assert closed["valid_until"] == "2026-03-31"


def test_patch_budget(registered_client):
    cat_id = _create_cat(registered_client)
    b_id = _create_budget(registered_client, cat_id).json()["id"]
    r = registered_client.patch(f"/api/budgets/{b_id}", json={"amount": "500.00"})
    assert r.status_code == 200
    assert r.json()["amount"] == "500.00"


def test_delete_budget(registered_client):
    cat_id = _create_cat(registered_client)
    b_id = _create_budget(registered_client, cat_id).json()["id"]
    r = registered_client.delete(f"/api/budgets/{b_id}")
    assert r.status_code == 204


def test_budget_isolation(registered_client, second_user_client):
    cat_id = _create_cat(registered_client)
    _create_budget(registered_client, cat_id)
    r = second_user_client.get("/api/budgets")
    assert len(r.json()) == 0
```

- [ ] **Step 2: Write `backend/app/routers/budgets.py`**

```python
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
```

- [ ] **Step 3: Register router in `backend/app/main.py`**

```python
from app.routers import budgets as budgets_router
# ...
app.include_router(budgets_router.router, prefix="/api")
```

- [ ] **Step 4: Run budget tests**

```bash
cd backend && pytest tests/test_budgets.py -v
```

Expected: alle 6 Tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/budgets.py backend/tests/test_budgets.py backend/app/main.py
git commit -m "feat: add budgets API with autoclose logic"
```

---

## Task 11: Final main.py + Full Test Run

**Files:** Replace `backend/app/main.py` with final version.

- [ ] **Step 1: Write final `backend/app/main.py`**

```python
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import health
from app.routers import auth as auth_router
from app.routers import households as households_router
from app.routers import accounts as accounts_router
from app.routers import categories as categories_router
from app.routers import expected_values as ev_router
from app.routers import budgets as budgets_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def _run_migrations() -> None:
    import sys
    import importlib

    sys.modules.pop("alembic", None)
    sys.modules.pop("alembic.config", None)
    sys.modules.pop("alembic.command", None)

    site_pkgs = next(
        (p for p in sys.path if "site-packages" in p and "venv" in p.lower()),
        None,
    )
    if site_pkgs and site_pkgs not in sys.path[:1]:
        sys.path.insert(0, site_pkgs)

    alembic_cfg_mod = importlib.import_module("alembic.config")
    alembic_cmd_mod = importlib.import_module("alembic.command")
    cfg = alembic_cfg_mod.Config("alembic.ini")
    alembic_cmd_mod.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.TESTING:
        logger.info("Running database migrations")
        _run_migrations()
    logger.info("HELLEDGER started")
    yield


app = FastAPI(
    title="HELLEDGER",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth_router.router, prefix="/api")
app.include_router(households_router.router, prefix="/api")
app.include_router(accounts_router.router, prefix="/api")
app.include_router(categories_router.router, prefix="/api")
app.include_router(ev_router.router, prefix="/api")
app.include_router(budgets_router.router, prefix="/api")

_frontend = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(_frontend):
    app.mount("/", StaticFiles(directory=_frontend, html=True), name="static")
```

- [ ] **Step 2: Run full test suite**

```bash
cd backend && pytest -v --tb=short
```

Expected: alle Tests PASSED — M1 (21) + M2 (23+14+9+9+8+6) = mindestens 68 Tests.

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: wire all M2 routers in main.py, bump version to 0.2.0"
```

---

## Task 12: Locales + Nav Component

**Files:**
- Replace: `frontend/locales/de.json`
- Replace: `frontend/locales/en.json`
- Create: `frontend/js/nav.js`

- [ ] **Step 1: Replace `frontend/locales/de.json`**

```json
{
  "app": { "name": "HELLEDGER", "tagline": "Dein persönlicher Finanz-Tracker" },
  "nav": {
    "dashboard": "Dashboard",
    "accounts": "Konten",
    "categories": "Kategorien",
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
    "empty": "Dein Dashboard ist noch leer."
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
    "empty": "Your dashboard is empty."
  },
  "accounts": {
    "title": "Accounts", "add": "Add Account",
    "name": "Name", "type": "Type", "balance": "Starting Balance",
    "currency": "Currency", "status": "Status",
    "active": "Active", "archived": "Archived",
    "archive": "Archive", "edit": "Edit",
    "save": "Save", "cancel": "Cancel",
    "types": { "checking": "Checking", "savings": "Savings", "credit": "Credit" }
  },
  "categories": {
    "title": "Categories", "add": "Add Category", "addSub": "Add Sub-Category",
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
    "addMember": "Add Member", "memberEmail": "Email Address",
    "add": "Add", "remove": "Remove",
    "roles": { "owner": "Owner", "member": "Member" },
    "save": "Save"
  },
  "lang": { "de": "Deutsch", "en": "English" }
}
```

- [ ] **Step 3: Write `frontend/js/nav.js`**

All user-supplied text (household names, user names) is set via `textContent`. The static HTML structure uses no template interpolation.

```javascript
import { logout } from "./auth.js";
import { api } from "./api.js";
import { navigate } from "./router.js";

export async function renderNav(container) {
    const [hhRes, meRes] = await Promise.all([
        api.get("/households"),
        api.get("/auth/me"),
    ]);
    const households = hhRes.ok ? await hhRes.json() : [];
    const user = meRes.ok ? await meRes.json() : null;
    const activeHhId = user ? user.active_household_id : null;
    const activeHh = households.find((h) => h.id === activeHhId) || null;

    // Static HTML — no user data interpolated
    container.innerHTML = [
        '<header class="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between">',
        '  <div class="flex items-center gap-6">',
        '    <span id="nav-brand" class="font-bold text-lg text-indigo-400"></span>',
        '    <nav class="flex gap-4">',
        '      <a id="nav-dashboard" href="#/dashboard" class="text-sm transition-colors"></a>',
        '      <a id="nav-accounts" href="#/accounts" class="text-sm transition-colors"></a>',
        '      <a id="nav-categories" href="#/categories" class="text-sm transition-colors"></a>',
        '      <a id="nav-settings" href="#/settings" class="text-sm transition-colors"></a>',
        '    </nav>',
        '  </div>',
        '  <div class="flex items-center gap-4">',
        '    <div class="relative">',
        '      <button id="hh-toggle" class="flex items-center gap-1 text-sm text-gray-300 hover:text-white">',
        '        <span id="hh-name" class="max-w-32 truncate"></span>',
        '        <svg class="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">',
        '          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>',
        '        </svg>',
        '      </button>',
        '      <div id="hh-dropdown" class="hidden absolute right-0 mt-2 w-52 bg-gray-800 rounded-lg border border-gray-700 shadow-xl z-50 py-1">',
        '        <div id="hh-list"></div>',
        '      </div>',
        '    </div>',
        '    <span id="nav-user" class="text-sm text-gray-400"></span>',
        '    <button id="nav-logout" class="text-sm text-gray-400 hover:text-white transition-colors"></button>',
        '  </div>',
        '</header>',
    ].join("\n");

    // Set all text via textContent
    document.getElementById("nav-brand").textContent = t("app.name");
    document.getElementById("nav-logout").textContent = t("nav.logout");
    if (user) document.getElementById("nav-user").textContent = user.name;
    document.getElementById("hh-name").textContent = activeHh ? activeHh.name : "";

    // Highlight active nav link
    const hash = window.location.hash;
    ["dashboard", "accounts", "categories", "settings"].forEach((page) => {
        const el = document.getElementById("nav-" + page);
        el.textContent = t("nav." + page);
        const isActive = hash === "#/" + page || hash.startsWith("#/" + page + "/");
        el.className = "text-sm transition-colors " + (isActive ? "text-white font-medium" : "text-gray-400 hover:text-white");
    });

    // Build household dropdown items via createElement (user data via textContent)
    const hhList = document.getElementById("hh-list");
    households.forEach((hh) => {
        const btn = document.createElement("button");
        btn.className = "w-full text-left px-3 py-2 text-sm hover:bg-gray-700 transition-colors " + (hh.id === activeHhId ? "text-indigo-400" : "text-gray-300");
        btn.textContent = hh.name;
        btn.addEventListener("click", async () => {
            await api.post("/households/" + hh.id + "/activate", {});
            location.reload();
        });
        hhList.appendChild(btn);
    });

    document.getElementById("hh-toggle").addEventListener("click", (e) => {
        e.stopPropagation();
        document.getElementById("hh-dropdown").classList.toggle("hidden");
    });
    document.addEventListener("click", () => {
        const dd = document.getElementById("hh-dropdown");
        if (dd) dd.classList.add("hidden");
    });

    document.getElementById("nav-logout").addEventListener("click", async () => {
        await logout();
        navigate("#/login");
    });
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/locales/ frontend/js/nav.js
git commit -m "feat: add M2 locale keys and shared nav component"
```

---

## Task 13: Accounts Page

**Files:** Create `frontend/js/views/accounts.js`

All user-supplied content is written via `textContent` or safe properties. Rows are built with `createElement` throughout — no user data in `innerHTML`.

- [ ] **Step 1: Write `frontend/js/views/accounts.js`**

```javascript
import { api } from "../api.js";
import { renderNav } from "../nav.js";
import { navigate } from "../router.js";

export async function renderAccounts() {
    const app = document.getElementById("app");

    // Static HTML structure — no user data
    app.innerHTML = [
        '<div class="min-h-screen bg-gray-950 text-white">',
        '  <div id="nav-container"></div>',
        '  <main class="p-8 max-w-5xl mx-auto">',
        '    <div class="flex items-center justify-between mb-6">',
        '      <h1 id="page-title" class="text-2xl font-bold"></h1>',
        '      <button id="btn-add" class="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 py-2 rounded-lg transition-colors"></button>',
        '    </div>',
        '    <div class="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">',
        '      <table class="w-full">',
        '        <thead class="border-b border-gray-800"><tr>',
        '          <th id="th-name" class="text-left px-6 py-3 text-xs text-gray-400 uppercase tracking-wider"></th>',
        '          <th id="th-type" class="text-left px-6 py-3 text-xs text-gray-400 uppercase tracking-wider"></th>',
        '          <th id="th-balance" class="text-right px-6 py-3 text-xs text-gray-400 uppercase tracking-wider"></th>',
        '          <th id="th-currency" class="text-left px-6 py-3 text-xs text-gray-400 uppercase tracking-wider"></th>',
        '          <th id="th-status" class="text-left px-6 py-3 text-xs text-gray-400 uppercase tracking-wider"></th>',
        '          <th class="px-6 py-3"></th>',
        '        </tr></thead>',
        '        <tbody id="accounts-body" class="divide-y divide-gray-800"></tbody>',
        '      </table>',
        '    </div>',
        '  </main>',
        '</div>',
        '<div id="modal" class="hidden fixed inset-0 bg-black/60 flex items-center justify-center z-50">',
        '  <div class="bg-gray-900 rounded-2xl border border-gray-800 p-6 w-full max-w-md mx-4">',
        '    <h2 id="modal-title" class="text-lg font-semibold mb-4"></h2>',
        '    <form id="modal-form" class="space-y-4">',
        '      <div><label id="lbl-name" class="block text-sm text-gray-400 mb-1"></label>',
        '        <input id="modal-name" type="text" required class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500"></div>',
        '      <div><label id="lbl-type" class="block text-sm text-gray-400 mb-1"></label>',
        '        <select id="modal-type" class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500">',
        '          <option id="opt-checking" value="checking"></option>',
        '          <option id="opt-savings" value="savings"></option>',
        '          <option id="opt-credit" value="credit"></option>',
        '        </select></div>',
        '      <div><label id="lbl-balance" class="block text-sm text-gray-400 mb-1"></label>',
        '        <input id="modal-balance" type="number" step="0.01" required class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500"></div>',
        '      <div><label id="lbl-currency" class="block text-sm text-gray-400 mb-1"></label>',
        '        <input id="modal-currency" type="text" value="EUR" required class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500"></div>',
        '      <div class="flex gap-3 pt-2">',
        '        <button type="submit" id="modal-save" class="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white py-2 rounded-lg transition-colors"></button>',
        '        <button type="button" id="modal-cancel" class="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded-lg transition-colors"></button>',
        '      </div>',
        '    </form>',
        '  </div>',
        '</div>',
    ].join("\n");

    await renderNav(document.getElementById("nav-container"));

    document.getElementById("page-title").textContent = t("accounts.title");
    document.getElementById("btn-add").textContent = t("accounts.add");
    document.getElementById("th-name").textContent = t("accounts.name");
    document.getElementById("th-type").textContent = t("accounts.type");
    document.getElementById("th-balance").textContent = t("accounts.balance");
    document.getElementById("th-currency").textContent = t("accounts.currency");
    document.getElementById("th-status").textContent = t("accounts.status");
    document.getElementById("lbl-name").textContent = t("accounts.name");
    document.getElementById("lbl-type").textContent = t("accounts.type");
    document.getElementById("lbl-balance").textContent = t("accounts.balance");
    document.getElementById("lbl-currency").textContent = t("accounts.currency");
    document.getElementById("modal-save").textContent = t("accounts.save");
    document.getElementById("modal-cancel").textContent = t("accounts.cancel");
    document.getElementById("opt-checking").textContent = t("accounts.types.checking");
    document.getElementById("opt-savings").textContent = t("accounts.types.savings");
    document.getElementById("opt-credit").textContent = t("accounts.types.credit");

    let editingId = null;

    async function loadAccounts() {
        const r = await api.get("/accounts");
        if (!r.ok) return;
        const accounts = await r.json();
        const tbody = document.getElementById("accounts-body");
        tbody.innerHTML = "";

        accounts.forEach((acc) => {
            const tr = document.createElement("tr");
            tr.className = "hover:bg-gray-800/50 transition-colors";

            // Name cell — textContent for user data
            const tdName = document.createElement("td");
            tdName.className = "px-6 py-4 text-sm font-medium text-white";
            tdName.textContent = acc.name;

            // Type badge — uses i18n lookup (controlled), fallback textContent
            const tdType = document.createElement("td");
            tdType.className = "px-6 py-4 text-sm";
            const typeBadge = document.createElement("span");
            typeBadge.className = "px-2 py-0.5 rounded text-xs bg-indigo-900/50 text-indigo-300";
            typeBadge.textContent = t("accounts.types." + acc.account_type) || acc.account_type;
            tdType.appendChild(typeBadge);

            // Balance cell
            const tdBal = document.createElement("td");
            tdBal.className = "px-6 py-4 text-sm text-right font-mono text-gray-200";
            tdBal.textContent = parseFloat(acc.starting_balance).toLocaleString("de-DE", { minimumFractionDigits: 2 });

            // Currency cell
            const tdCur = document.createElement("td");
            tdCur.className = "px-6 py-4 text-sm text-gray-400";
            tdCur.textContent = acc.currency;

            // Status badge
            const tdStatus = document.createElement("td");
            tdStatus.className = "px-6 py-4 text-sm";
            const statusBadge = document.createElement("span");
            statusBadge.className = acc.archived
                ? "px-2 py-0.5 rounded text-xs bg-red-900/40 text-red-400"
                : "px-2 py-0.5 rounded text-xs bg-green-900/40 text-green-400";
            statusBadge.textContent = acc.archived ? t("accounts.archived") : t("accounts.active");
            tdStatus.appendChild(statusBadge);

            // Actions cell
            const tdActions = document.createElement("td");
            tdActions.className = "px-6 py-4 text-sm";
            const actDiv = document.createElement("div");
            actDiv.className = "flex gap-3 justify-end";

            const editBtn = document.createElement("button");
            editBtn.className = "text-indigo-400 hover:text-indigo-300 transition-colors text-xs";
            editBtn.textContent = t("accounts.edit");
            editBtn.addEventListener("click", async () => {
                const res = await api.get("/accounts/" + acc.id);
                if (!res.ok) return;
                const data = await res.json();
                editingId = acc.id;
                document.getElementById("modal-name").value = data.name;
                document.getElementById("modal-type").value = data.account_type;
                document.getElementById("modal-balance").value = data.starting_balance;
                document.getElementById("modal-currency").value = data.currency;
                document.getElementById("modal-title").textContent = t("accounts.edit");
                document.getElementById("modal").classList.remove("hidden");
            });

            const archiveBtn = document.createElement("button");
            archiveBtn.className = "text-red-400 hover:text-red-300 transition-colors text-xs";
            archiveBtn.textContent = t("accounts.archive");
            archiveBtn.addEventListener("click", async () => {
                await api.delete("/accounts/" + acc.id);
                await loadAccounts();
            });

            actDiv.appendChild(editBtn);
            actDiv.appendChild(archiveBtn);
            tdActions.appendChild(actDiv);

            [tdName, tdType, tdBal, tdCur, tdStatus, tdActions].forEach((td) => tr.appendChild(td));
            tbody.appendChild(tr);
        });
    }

    document.getElementById("btn-add").addEventListener("click", () => {
        editingId = null;
        document.getElementById("modal-form").reset();
        document.getElementById("modal-currency").value = "EUR";
        document.getElementById("modal-title").textContent = t("accounts.add");
        document.getElementById("modal").classList.remove("hidden");
    });

    document.getElementById("modal-cancel").addEventListener("click", () => {
        document.getElementById("modal").classList.add("hidden");
    });

    document.getElementById("modal-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById("modal-name").value,
            account_type: document.getElementById("modal-type").value,
            starting_balance: document.getElementById("modal-balance").value,
            currency: document.getElementById("modal-currency").value,
        };
        if (editingId) {
            await api.patch("/accounts/" + editingId, payload);
        } else {
            await api.post("/accounts", payload);
        }
        document.getElementById("modal").classList.add("hidden");
        await loadAccounts();
    });

    await loadAccounts();
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/js/views/accounts.js
git commit -m "feat: add accounts frontend page"
```

---

## Task 14: Categories Page

**Files:** Create `frontend/js/views/categories.js`

Static HTML in `innerHTML` has no `${...}` — all dynamic values (name, color, IDs) are set via `textContent` / `style.*` / `addEventListener` after the static structure is set.

- [ ] **Step 1: Write `frontend/js/views/categories.js`**

```javascript
import { api } from "../api.js";
import { renderNav } from "../nav.js";

export async function renderCategories() {
    const app = document.getElementById("app");

    // Static HTML — no user data interpolated
    app.innerHTML = [
        '<div class="min-h-screen bg-gray-950 text-white">',
        '  <div id="nav-container"></div>',
        '  <main class="p-8 max-w-4xl mx-auto">',
        '    <div class="flex items-center justify-between mb-6">',
        '      <h1 id="page-title" class="text-2xl font-bold"></h1>',
        '      <button id="btn-add" class="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 py-2 rounded-lg transition-colors"></button>',
        '    </div>',
        '    <div id="cat-sections" class="space-y-8"></div>',
        '  </main>',
        '</div>',
        '<div id="cat-modal" class="hidden fixed inset-0 bg-black/60 flex items-center justify-center z-50">',
        '  <div class="bg-gray-900 rounded-2xl border border-gray-800 p-6 w-full max-w-md mx-4">',
        '    <h2 id="cat-modal-title" class="text-lg font-semibold mb-4"></h2>',
        '    <form id="cat-modal-form" class="space-y-4">',
        '      <div><label id="lbl-cat-name" class="block text-sm text-gray-400 mb-1"></label>',
        '        <input id="cat-name" type="text" required class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500"></div>',
        '      <div><label id="lbl-cat-type" class="block text-sm text-gray-400 mb-1"></label>',
        '        <select id="cat-type" class="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500">',
        '          <option id="opt-income" value="income"></option>',
        '          <option id="opt-fixed" value="fixed"></option>',
        '          <option id="opt-variable" value="variable"></option>',
        '        </select></div>',
        '      <div><label id="lbl-cat-color" class="block text-sm text-gray-400 mb-1"></label>',
        '        <input id="cat-color" type="color" value="#6366f1" class="h-10 w-full rounded-lg bg-gray-800 border border-gray-700 cursor-pointer"></div>',
        '      <input id="cat-parent-id" type="hidden" value="">',
        '      <div class="flex gap-3 pt-2">',
        '        <button type="submit" id="cat-save" class="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white py-2 rounded-lg transition-colors"></button>',
        '        <button type="button" id="cat-cancel" class="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded-lg transition-colors"></button>',
        '      </div>',
        '    </form>',
        '  </div>',
        '</div>',
    ].join("\n");

    await renderNav(document.getElementById("nav-container"));

    document.getElementById("page-title").textContent = t("categories.title");
    document.getElementById("btn-add").textContent = t("categories.add");
    document.getElementById("lbl-cat-name").textContent = t("categories.name");
    document.getElementById("lbl-cat-type").textContent = t("categories.type");
    document.getElementById("lbl-cat-color").textContent = t("categories.color");
    document.getElementById("opt-income").textContent = t("categories.types.income");
    document.getElementById("opt-fixed").textContent = t("categories.types.fixed");
    document.getElementById("opt-variable").textContent = t("categories.types.variable");
    document.getElementById("cat-save").textContent = t("categories.save");
    document.getElementById("cat-cancel").textContent = t("categories.cancel");

    let editingCatId = null;

    function openModal(title, parentId, existing) {
        editingCatId = existing ? existing.id : null;
        document.getElementById("cat-modal-title").textContent = title;
        document.getElementById("cat-name").value = existing ? existing.name : "";
        document.getElementById("cat-type").value = existing ? existing.category_type : "fixed";
        document.getElementById("cat-color").value = existing && existing.color ? existing.color : "#6366f1";
        document.getElementById("cat-parent-id").value = parentId != null ? parentId : "";
        document.getElementById("cat-modal").classList.remove("hidden");
    }

    document.getElementById("cat-cancel").addEventListener("click", () => {
        document.getElementById("cat-modal").classList.add("hidden");
    });

    document.getElementById("cat-modal-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const parentRaw = document.getElementById("cat-parent-id").value;
        const payload = {
            name: document.getElementById("cat-name").value,
            category_type: document.getElementById("cat-type").value,
            color: document.getElementById("cat-color").value,
            parent_id: parentRaw !== "" ? parseInt(parentRaw, 10) : null,
        };
        if (editingCatId) {
            await api.patch("/categories/" + editingCatId, payload);
        } else {
            await api.post("/categories", payload);
        }
        document.getElementById("cat-modal").classList.add("hidden");
        await loadCategories();
    });

    document.getElementById("btn-add").addEventListener("click", () => {
        openModal(t("categories.add"), null, null);
    });

    async function loadEvPanel(catId, panel, isVariable) {
        const endpoint = isVariable ? "/budgets" : "/expected-values";
        const r = await api.get(endpoint + "?category_id=" + catId);
        if (!r.ok) return;
        const items = await r.json();
        panel.innerHTML = "";

        items.forEach((item) => {
            const row = document.createElement("div");
            row.className = "flex items-center justify-between py-1 text-sm";
            const span = document.createElement("span");
            span.className = "text-gray-300";
            const until = item.valid_until || t("categories.noLimit");
            span.textContent = item.amount + " \u20AC \u00B7 " + item.valid_from + " \u2192 " + until;
            const del = document.createElement("button");
            del.className = "text-red-400 hover:text-red-300 text-xs ml-2";
            del.textContent = "\u00D7";
            del.addEventListener("click", async () => {
                await api.delete(endpoint + "/" + item.id);
                await loadEvPanel(catId, panel, isVariable);
            });
            row.appendChild(span);
            row.appendChild(del);
            panel.appendChild(row);
        });

        const form = document.createElement("form");
        form.className = "flex gap-2 mt-2";
        const amtIn = document.createElement("input");
        amtIn.type = "number";
        amtIn.step = "0.01";
        amtIn.placeholder = t("categories.amount");
        amtIn.className = "flex-1 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-white";
        const dateIn = document.createElement("input");
        dateIn.type = "date";
        dateIn.placeholder = t("categories.validFrom");
        dateIn.className = "flex-1 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-white";
        const btn = document.createElement("button");
        btn.type = "submit";
        btn.className = "bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-3 py-1 rounded";
        btn.textContent = isVariable ? t("categories.newBudget") : t("categories.newExpectedValue");
        form.appendChild(amtIn);
        form.appendChild(dateIn);
        form.appendChild(btn);
        form.addEventListener("submit", async (ev) => {
            ev.preventDefault();
            if (!amtIn.value || !dateIn.value) return;
            await api.post(endpoint, {
                category_id: catId,
                amount: amtIn.value,
                valid_from: dateIn.value,
            });
            await loadEvPanel(catId, panel, isVariable);
        });
        panel.appendChild(form);
    }

    function buildCategoryRow(cat, depth) {
        const wrapper = document.createElement("div");

        // Static HTML structure — no user data in the string
        wrapper.innerHTML = [
            '<div class="cat-row flex items-center gap-3 py-2 px-4 hover:bg-gray-800/40 rounded-lg">',
            '  <span class="color-dot w-3 h-3 rounded-full flex-shrink-0"></span>',
            '  <span class="cat-name flex-1 text-sm text-white"></span>',
            '  <div class="flex gap-2">',
            '    <button class="btn-ev text-xs text-gray-400 hover:text-indigo-400 transition-colors"></button>',
            '    <button class="btn-sub text-xs text-gray-400 hover:text-green-400 transition-colors"></button>',
            '    <button class="btn-edit text-xs text-gray-400 hover:text-white transition-colors"></button>',
            '    <button class="btn-arc text-xs text-red-400/60 hover:text-red-400 transition-colors"></button>',
            '  </div>',
            '</div>',
            '<div class="ev-panel hidden px-4 pb-3 bg-gray-800/20 rounded-lg mx-2 mb-1"></div>',
        ].join("\n");

        // Fill dynamic values safely
        wrapper.querySelector(".cat-row").style.paddingLeft = (16 + depth * 24) + "px";
        wrapper.querySelector(".color-dot").style.backgroundColor = cat.color || "#6366f1";
        wrapper.querySelector(".cat-name").textContent = cat.name;

        const isVariable = cat.category_type === "variable";
        wrapper.querySelector(".btn-ev").textContent = isVariable ? t("categories.budget") : t("categories.expectedValue");
        wrapper.querySelector(".btn-sub").textContent = t("categories.addSub");
        wrapper.querySelector(".btn-edit").textContent = t("categories.edit");
        wrapper.querySelector(".btn-arc").textContent = t("categories.archive");

        const evPanel = wrapper.querySelector(".ev-panel");

        wrapper.querySelector(".btn-ev").addEventListener("click", async () => {
            evPanel.classList.toggle("hidden");
            if (!evPanel.classList.contains("hidden")) {
                await loadEvPanel(cat.id, evPanel, isVariable);
            }
        });
        wrapper.querySelector(".btn-sub").addEventListener("click", () => openModal(t("categories.addSub"), cat.id, null));
        wrapper.querySelector(".btn-edit").addEventListener("click", () => openModal(t("categories.edit"), cat.parent_id, cat));
        wrapper.querySelector(".btn-arc").addEventListener("click", async () => {
            await api.delete("/categories/" + cat.id);
            await loadCategories();
        });

        return wrapper;
    }

    function renderTree(nodes, container, depth) {
        nodes.forEach((cat) => {
            container.appendChild(buildCategoryRow(cat, depth));
            if (cat.children && cat.children.length > 0) {
                renderTree(cat.children, container, depth + 1);
            }
        });
    }

    async function loadCategories() {
        const r = await api.get("/categories");
        if (!r.ok) return;
        const tree = await r.json();
        const sections = document.getElementById("cat-sections");
        sections.innerHTML = "";

        ["income", "fixed", "variable"].forEach((catType) => {
            const nodes = tree.filter((n) => n.category_type === catType);
            if (nodes.length === 0) return;
            const section = document.createElement("div");
            const heading = document.createElement("h2");
            heading.className = "text-lg font-semibold text-gray-300 mb-3";
            heading.textContent = t("categories.sections." + catType);
            section.appendChild(heading);
            const card = document.createElement("div");
            card.className = "bg-gray-900 rounded-2xl border border-gray-800 py-2";
            renderTree(nodes, card, 0);
            section.appendChild(card);
            sections.appendChild(section);
        });
    }

    await loadCategories();
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/js/views/categories.js
git commit -m "feat: add categories frontend page with tree view and EV/budget editors"
```

---

## Task 15: Settings Page

**Files:** Create `frontend/js/views/settings.js`

- [ ] **Step 1: Write `frontend/js/views/settings.js`**

```javascript
import { api } from "../api.js";
import { renderNav } from "../nav.js";

export async function renderSettings() {
    const app = document.getElementById("app");

    // Static HTML — no user data
    app.innerHTML = [
        '<div class="min-h-screen bg-gray-950 text-white">',
        '  <div id="nav-container"></div>',
        '  <main class="p-8 max-w-2xl mx-auto space-y-8">',
        '    <h1 id="page-title" class="text-2xl font-bold"></h1>',
        '    <section class="bg-gray-900 rounded-2xl border border-gray-800 p-6 space-y-4">',
        '      <h2 id="sec-household" class="text-lg font-semibold"></h2>',
        '      <div>',
        '        <label id="lbl-hh-name" class="block text-sm text-gray-400 mb-1"></label>',
        '        <div class="flex gap-3">',
        '          <input id="hh-name-input" type="text" class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500">',
        '          <button id="btn-save-hh" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors text-sm"></button>',
        '        </div>',
        '      </div>',
        '    </section>',
        '    <section class="bg-gray-900 rounded-2xl border border-gray-800 p-6 space-y-4">',
        '      <h2 id="sec-members" class="text-lg font-semibold"></h2>',
        '      <div id="members-list" class="space-y-2"></div>',
        '      <div class="flex gap-3 pt-2 border-t border-gray-800">',
        '        <input id="member-email" type="email" class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-indigo-500">',
        '        <button id="btn-add-member" class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors text-sm"></button>',
        '      </div>',
        '      <div id="member-error" class="hidden text-red-400 text-sm"></div>',
        '    </section>',
        '  </main>',
        '</div>',
    ].join("\n");

    await renderNav(document.getElementById("nav-container"));

    document.getElementById("page-title").textContent = t("settings.title");
    document.getElementById("sec-household").textContent = t("settings.household");
    document.getElementById("lbl-hh-name").textContent = t("settings.householdName");
    document.getElementById("btn-save-hh").textContent = t("settings.save");
    document.getElementById("sec-members").textContent = t("settings.members");
    document.getElementById("btn-add-member").textContent = t("settings.add");
    document.getElementById("member-email").placeholder = t("settings.memberEmail");

    const meRes = await api.get("/auth/me");
    if (!meRes.ok) return;
    const user = await meRes.json();
    const hhId = user.active_household_id;
    if (!hhId) return;

    const hhsRes = await api.get("/households");
    const hhs = hhsRes.ok ? await hhsRes.json() : [];
    const hh = hhs.find((h) => h.id === hhId) || null;
    if (hh) document.getElementById("hh-name-input").value = hh.name;

    document.getElementById("btn-save-hh").addEventListener("click", async () => {
        const newName = document.getElementById("hh-name-input").value.trim();
        if (!newName) return;
        await api.patch("/households/" + hhId, { name: newName });
    });

    async function loadMembers() {
        const r = await api.get("/households/" + hhId + "/members");
        if (!r.ok) return;
        const members = await r.json();
        const list = document.getElementById("members-list");
        list.innerHTML = "";

        members.forEach((m) => {
            const row = document.createElement("div");
            row.className = "flex items-center justify-between py-2 px-3 bg-gray-800/40 rounded-lg";

            const info = document.createElement("div");
            info.className = "flex items-center gap-2 flex-1";
            const nameSpan = document.createElement("span");
            nameSpan.className = "text-sm text-white";
            nameSpan.textContent = m.name;
            const emailSpan = document.createElement("span");
            emailSpan.className = "text-xs text-gray-400";
            emailSpan.textContent = m.email;
            const roleSpan = document.createElement("span");
            roleSpan.className = "text-xs text-indigo-400";
            roleSpan.textContent = t("settings.roles." + m.role) || m.role;
            info.appendChild(nameSpan);
            info.appendChild(emailSpan);
            info.appendChild(roleSpan);

            row.appendChild(info);

            if (m.user_id !== user.id && hh && hh.owner_id === user.id) {
                const btn = document.createElement("button");
                btn.className = "text-xs text-red-400 hover:text-red-300 transition-colors";
                btn.textContent = t("settings.remove");
                btn.addEventListener("click", async () => {
                    await api.delete("/households/" + hhId + "/members/" + m.user_id);
                    await loadMembers();
                });
                row.appendChild(btn);
            }

            list.appendChild(row);
        });
    }

    document.getElementById("btn-add-member").addEventListener("click", async () => {
        const email = document.getElementById("member-email").value.trim();
        const errBox = document.getElementById("member-error");
        errBox.classList.add("hidden");
        if (!email) return;
        const r = await api.post("/households/" + hhId + "/members", { email });
        if (r.ok) {
            document.getElementById("member-email").value = "";
            await loadMembers();
        } else {
            const err = await r.json();
            errBox.textContent = err.detail || t("errors.generic");
            errBox.classList.remove("hidden");
        }
    });

    await loadMembers();
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/js/views/settings.js
git commit -m "feat: add settings frontend page with household and member management"
```

---

## Task 16: Wire Routes + Smoke Test

**Files:**
- Replace: `frontend/index.html`
- Replace: `frontend/js/views/dashboard.js`

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
</head>
<body class="bg-gray-950 antialiased">
  <div id="app">
    <div class="min-h-screen bg-gray-950 flex items-center justify-center">
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

    await initI18n();

    route("#/login", renderLogin);
    route("#/register", renderLogin);
    route("#/dashboard", renderDashboard);
    route("#/accounts", renderAccounts);
    route("#/categories", renderCategories);
    route("#/settings", renderSettings);

    initRouter();

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/service-worker.js").catch(() => {});
    }
  </script>
</body>
</html>
```

- [ ] **Step 2: Replace `frontend/js/views/dashboard.js`** — Nav einbinden

```javascript
import { getCurrentUser } from "../auth.js";
import { navigate } from "../router.js";
import { renderNav } from "../nav.js";

export async function renderDashboard() {
    const user = await getCurrentUser();
    if (!user) { navigate("#/login"); return; }

    const app = document.getElementById("app");

    // Static HTML — no user data
    app.innerHTML = [
        '<div class="min-h-screen bg-gray-950 text-white">',
        '  <div id="nav-container"></div>',
        '  <main class="p-8 max-w-4xl mx-auto">',
        '    <h2 id="welcome-msg" class="text-xl font-semibold mb-2"></h2>',
        '    <p id="empty-msg" class="text-gray-400"></p>',
        '  </main>',
        '</div>',
    ].join("\n");

    await renderNav(document.getElementById("nav-container"));

    // Set user-supplied text via textContent
    document.getElementById("welcome-msg").textContent = t("dashboard.welcome", { name: user.name });
    document.getElementById("empty-msg").textContent = t("dashboard.empty");
}
```

- [ ] **Step 3: Run full test suite**

```bash
cd backend && pytest -v --tb=short
```

Expected: alle Tests PASSED (≥68 total).

- [ ] **Step 4: Commit**

```bash
git add frontend/index.html frontend/js/views/dashboard.js
git commit -m "feat: wire M2 frontend routes and update dashboard with shared nav"
```

- [ ] **Step 5: Manual Smoke Test**

```bash
cd backend
SECRET_KEY=dev-secret-key-change-in-production!! \
DATABASE_PATH=./helledger-dev.db \
uvicorn app.main:app --port 3000 --reload
```

Verify at http://localhost:3000:
1. Register → Dashboard mit Nav-Bar (Dashboard | Konten | Kategorien | Einstellungen)
2. Haushalt-Dropdown zeigt "Mein Haushalt"
3. `#/accounts` → leere Tabelle, Konto anlegen, bearbeiten, archivieren
4. `#/categories` → Kategorien anlegen (income/fixed/variable), Sub-Kategorie, Sollwert/Budget-Editor
5. `#/settings` → Haushaltsname bearbeitbar, eigener Account in Mitgliederliste
6. Logout → Login-Seite

- [ ] **Step 6: Push**

```bash
git push
```

---

## Verification Checklist

- [ ] `cd backend && pytest -v` — alle Tests PASSED (≥68)
- [ ] `docker build -t helledger:m2 .` — baut erfolgreich
- [ ] Manual Smoke Test: alle 6 Schritte aus Task 16 Step 5 bestätigt
