import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.backup import BackupItem, BackupSettings, BackupSettingsPatch
from app.services import backup as backup_svc
from app.services.settings import get_setting, set_setting

router = APIRouter(prefix="/backup", tags=["backup"])


def _require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="admin_required")
    return user


@router.get("/settings", response_model=BackupSettings)
async def get_backup_settings(
    user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
) -> BackupSettings:
    days = int(get_setting(db, "backup_retention_days", "7"))
    return BackupSettings(backup_retention_days=days)


@router.patch("/settings", response_model=BackupSettings)
async def patch_backup_settings(
    body: BackupSettingsPatch,
    user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
) -> BackupSettings:
    set_setting(db, "backup_retention_days", str(body.backup_retention_days))
    return BackupSettings(backup_retention_days=body.backup_retention_days)


@router.post("/trigger", response_model=BackupItem, status_code=201)
async def trigger_backup(
    user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
) -> BackupItem:
    item = backup_svc.create_backup(db, settings.BACKUP_PATH, settings.DATABASE_PATH)
    return BackupItem(**item)


@router.get("/list", response_model=list[BackupItem])
async def list_backups(
    user: User = Depends(_require_admin),
) -> list[BackupItem]:
    return backup_svc.list_backups(settings.BACKUP_PATH)


@router.get("/{filename}/download")
async def download_backup(
    filename: str,
    user: User = Depends(_require_admin),
) -> FileResponse:
    try:
        backup_svc._validate_filename(filename)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_filename")
    path = os.path.join(settings.BACKUP_PATH, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="backup_not_found")
    return FileResponse(path, filename=filename, media_type="application/octet-stream")


@router.delete("/{filename}", status_code=204)
async def delete_backup(
    filename: str,
    user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
) -> None:
    try:
        backup_svc.delete_backup(settings.BACKUP_PATH, filename)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_filename")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="backup_not_found")
