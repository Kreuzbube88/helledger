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
    if user.active_household_id == hh.id:
        user.active_household_id = None
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
    if target is None:
        raise HTTPException(status_code=404, detail="user_not_found")
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
    if user_id == user.id:
        raise HTTPException(status_code=400, detail="cannot_remove_self")
    _require_owner(household_id, user, db)
    m = db.query(HouseholdMember).filter_by(
        household_id=household_id, user_id=user_id
    ).first()
    if m is None:
        raise HTTPException(status_code=404, detail="not_found")
    db.delete(m)
    db.commit()
