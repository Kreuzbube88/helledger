from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.auth.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.household import Category, Account

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def global_search(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.active_household_id:
        return []
    hh_id = user.active_household_id
    results = (
        db.query(Transaction, Category, Account)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .outerjoin(Account, Transaction.account_id == Account.id)
        .filter(
            Transaction.household_id == hh_id,
            Transaction.description.ilike(f'%{q}%'),
        )
        .order_by(Transaction.date.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": tx.id,
            "date": tx.date.isoformat(),
            "description": tx.description,
            "amount": float(tx.amount),
            "transaction_type": tx.transaction_type,
            "category_name": cat.name if cat else None,
            "account_name": acc.name if acc else None,
        }
        for tx, cat, acc in results
    ]
