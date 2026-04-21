from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_admin_user, get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.users import UserOut, UserPatch, PreferencesOut, PreferencesPatch, ProfilePatch

router = APIRouter(prefix="/users")


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    return db.query(User).order_by(User.id).all()


@router.patch("/me", response_model=UserOut)
def update_profile(
    body: ProfilePatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.name is not None:
        user.name = body.name
    if body.language is not None:
        user.language = body.language
    db.commit()
    db.refresh(user)
    return user


@router.get("/me/preferences", response_model=PreferencesOut)
def get_preferences(user: User = Depends(get_current_user)):
    return user


@router.patch("/me/preferences", response_model=PreferencesOut)
def update_preferences(
    body: PreferencesPatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.language is not None:
        user.language = body.language
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if current.role != "admin" and current.id != user_id:
        raise HTTPException(status_code=403, detail="forbidden")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def patch_user(
    user_id: int,
    body: UserPatch,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    if body.name is not None:
        user.name = body.name
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.language is not None:
        user.language = body.language
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="cannot_delete_self")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    db.delete(user)
    db.commit()
