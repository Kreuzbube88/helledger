import os

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import get_admin_user
from app.config import settings
from app.database import get_db
from app.models.household import Household
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.admin import AdminSettings, AdminSettingsPatch, AdminStatus
from app.services.settings import get_setting, set_setting

router = APIRouter(prefix="/admin")


def _runtime(key: str, env_val: str, db: Session) -> str:
    """Return runtime setting from DB, falling back to ENV value."""
    return get_setting(db, key) or env_val


@router.get("/status", response_model=AdminStatus)
def admin_status(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    db_path = settings.DATABASE_PATH
    db_size = os.path.getsize(db_path) if os.path.isfile(db_path) else 0
    return AdminStatus(
        user_count=db.query(User).count(),
        household_count=db.query(Household).count(),
        transaction_count=db.query(Transaction).count(),
        db_size_bytes=db_size,
        allow_registration=_runtime("allow_registration", str(settings.ALLOW_REGISTRATION), db).lower() != "false",
    )


@router.get("/settings", response_model=AdminSettings)
def get_admin_settings(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    return AdminSettings(
        allow_registration=_runtime("allow_registration", str(settings.ALLOW_REGISTRATION), db).lower() != "false",
        default_language=_runtime("default_language", settings.DEFAULT_LANGUAGE, db),
        oidc_enabled=_runtime("oidc_enabled", str(settings.OIDC_ENABLED), db).lower() == "true",
        oidc_client_id=_runtime("oidc_client_id", settings.OIDC_CLIENT_ID, db),
        oidc_discovery_url=_runtime("oidc_discovery_url", settings.OIDC_DISCOVERY_URL, db),
        smtp_host=_runtime("smtp_host", settings.SMTP_HOST, db),
        smtp_port=int(_runtime("smtp_port", str(settings.SMTP_PORT), db)),
        smtp_user=_runtime("smtp_user", settings.SMTP_USER, db),
        smtp_from=_runtime("smtp_from", settings.SMTP_FROM, db),
    )


@router.patch("/settings", response_model=AdminSettings)
def update_admin_settings(
    body: AdminSettingsPatch,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    mapping = {
        "allow_registration": body.allow_registration,
        "default_language": body.default_language,
        "oidc_enabled": body.oidc_enabled,
        "oidc_client_id": body.oidc_client_id,
        "oidc_client_secret": body.oidc_client_secret,
        "oidc_discovery_url": body.oidc_discovery_url,
        "smtp_host": body.smtp_host,
        "smtp_port": body.smtp_port,
        "smtp_user": body.smtp_user,
        "smtp_password": body.smtp_password,
        "smtp_from": body.smtp_from,
    }
    for key, val in mapping.items():
        if val is not None:
            set_setting(db, key, str(val))
    return get_admin_settings(db=db, _admin=_admin)
