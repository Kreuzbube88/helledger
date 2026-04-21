import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.household import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.import_ import (
    ConfirmRequest, ConfirmResponse, DuplicateEntry, ErrorEntry, ParseResponse,
)
from app.services.import_parser import apply_csv_mapping, parse_csv, parse_ofx
from app.services.excel_io import import_excel, export_excel

router = APIRouter(prefix="/import", tags=["import"])
export_router = APIRouter(prefix="/export", tags=["export"])

_sessions: dict[str, dict] = {}
_SESSION_TTL = 600  # 10 minutes


def _require_active_hh(user: User) -> int:
    if user.active_household_id is None:
        raise HTTPException(status_code=400, detail="no_active_household")
    return user.active_household_id


def _prune_sessions() -> None:
    now = time.time()
    for k in [k for k, v in _sessions.items() if v["expires_at"] < now]:
        del _sessions[k]


def _pop_session(token: str) -> dict:
    _prune_sessions()
    session = _sessions.get(token)
    if session is None or session["expires_at"] < time.time():
        raise HTTPException(status_code=400, detail="session_expired")
    return session


@router.post("/parse", response_model=ParseResponse)
async def parse_import(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_active_hh(user)

    filename = (file.filename or "").lower()
    if not (filename.endswith(".csv") or filename.endswith(".ofx") or filename.endswith(".qfx")):
        raise HTTPException(status_code=400, detail="unsupported_format")

    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="file_too_large")

    _prune_sessions()
    token = str(uuid.uuid4())

    if filename.endswith(".csv"):
        try:
            result = parse_csv(data)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        _sessions[token] = {
            "expires_at": time.time() + _SESSION_TTL,
            "format": "csv",
            "columns": result.columns,
            "raw_rows": result.raw_rows,
        }
        return ParseResponse(
            session_token=token,
            format="csv",
            columns=result.columns,
            preview_rows=result.preview_rows,
            suggested_mapping=result.suggested_mapping,
            detected_date_format=result.detected_date_format,
            detected_decimal_separator=result.detected_decimal_separator,
        )
    else:
        try:
            result = parse_ofx(data)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        _sessions[token] = {
            "expires_at": time.time() + _SESSION_TTL,
            "format": "ofx",
            "parsed_rows": result.transactions,
        }
        return ParseResponse(
            session_token=token,
            format="ofx",
            columns=["date", "amount", "description"],
            preview_rows=result.preview_rows,
            suggested_mapping={"date": "date", "amount": "amount", "description": "description"},
            detected_date_format="%Y-%m-%d",
            detected_decimal_separator=".",
        )


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_import(
    body: ConfirmRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    session = _pop_session(body.session_token)

    account = db.query(Account).filter(
        Account.id == body.account_id,
        Account.household_id == hh_id,
    ).first()
    if account is None:
        raise HTTPException(status_code=403, detail="forbidden")

    if session["format"] == "csv":
        try:
            parsed_rows, parse_errors = apply_csv_mapping(
                session["raw_rows"],
                session["columns"],
                body.field_map,
                body.date_format,
                body.decimal_separator,
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    else:
        parsed_rows = session["parsed_rows"]
        parse_errors = []

    now = datetime.now(timezone.utc)
    imported = 0
    duplicates: list[DuplicateEntry] = []
    errors: list[ErrorEntry] = [ErrorEntry(row=e.row, reason=e.reason) for e in parse_errors]

    for row in parsed_rows:
        amount = row.amount
        transaction_type = "income" if amount > 0 else "expense"
        amount = abs(amount) if transaction_type == "income" else -abs(amount)

        if session["format"] == "ofx" and row.external_id:
            dup = db.query(Transaction).filter(
                Transaction.account_id == body.account_id,
                Transaction.external_id == row.external_id,
            ).first()
        else:
            dup = db.query(Transaction).filter(
                Transaction.account_id == body.account_id,
                Transaction.date == row.date,
                Transaction.amount == amount,
                Transaction.description == row.description,
            ).first()

        if dup:
            duplicates.append(DuplicateEntry(
                date=str(row.date),
                amount=f"{row.amount:.2f}",
                description=row.description,
            ))
            continue

        db.add(Transaction(
            household_id=hh_id,
            account_id=body.account_id,
            category_id=body.category_id,
            amount=amount,
            date=row.date,
            description=row.description,
            transaction_type=transaction_type,
            external_id=row.external_id,
            created_at=now,
            updated_at=now,
        ))
        imported += 1

    db.commit()
    _sessions.pop(body.session_token, None)

    return ConfirmResponse(imported=imported, duplicates=duplicates, errors=errors)


@router.post("/excel")
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


@export_router.get("/excel")
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
