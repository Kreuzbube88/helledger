from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.auth.deps import get_current_user
from app.models.user import User
from app.models.net_worth import NetWorthSnapshot
from app.schemas.net_worth import NetWorthCreate, NetWorthOut

router = APIRouter(prefix="/net-worth", tags=["net-worth"])


@router.get("", response_model=list[NetWorthOut])
def list_snapshots(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    return (
        db.query(NetWorthSnapshot)
        .filter(NetWorthSnapshot.household_id == user.active_household_id)
        .order_by(NetWorthSnapshot.snapshot_date.desc())
        .all()
    )


@router.post("", response_model=NetWorthOut, status_code=201)
def create_snapshot(body: NetWorthCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    snap = NetWorthSnapshot(
        household_id=user.active_household_id,
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


@router.delete("/{snap_id}", status_code=204)
def delete_snapshot(snap_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.active_household_id:
        raise HTTPException(status_code=400, detail="no_active_household")
    snap = db.query(NetWorthSnapshot).filter(
        NetWorthSnapshot.id == snap_id,
        NetWorthSnapshot.household_id == user.active_household_id,
    ).first()
    if not snap:
        raise HTTPException(status_code=404, detail="not_found")
    db.delete(snap)
    db.commit()
