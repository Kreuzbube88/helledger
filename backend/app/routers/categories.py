from datetime import datetime, timezone, date as date_type, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import extract, or_, func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.household import Category
from app.models.transaction import Transaction
from app.schemas.categories import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTreeNode
)
from app.schemas.transaction import SollIstNode

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

    if not cats:
        return []

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

    # TODO Phase 2: replace with FixedCost-based soll lookup
    ev_map: dict[int, Decimal] = {}

    def _build(parent_id: int | None) -> list[SollIstNode]:
        result = []
        for cat in cats:
            if cat.parent_id != parent_id:
                continue
            children = _build(cat.id)
            ist_self = tx_map.get(cat.id, Decimal("0"))
            ist_children = sum(Decimal(c.ist) for c in children)
            ist = ist_self + ist_children
            soll_self = ev_map.get(cat.id) or Decimal("0")
            soll_children = sum(Decimal(c.soll) for c in children)
            soll = soll_self if soll_self > Decimal("0") else soll_children
            result.append(SollIstNode(
                id=cat.id, name=cat.name, category_type=cat.category_type,
                soll=f"{soll:.2f}", ist=f"{ist:.2f}", diff=f"{soll - ist:.2f}",
                children=children,
            ))
        return result

    return _build(None)


@router.get("/expiring-soon")
async def get_expiring_categories(
    days: int = 30,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    today = date_type.today()
    cutoff = today + timedelta(days=days)
    # TODO Phase 2: replace with FixedCost-based expiry lookup
    return []


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
