import os
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.services.settings import get_setting

FILENAME_RE = re.compile(r"^helledger_\d{8}_\d{6}\.db$")


def _validate_filename(filename: str) -> None:
    if not FILENAME_RE.match(filename):
        raise ValueError("invalid_filename")


def _parse_created_at(filename: str) -> str:
    dt = datetime.strptime(filename[10:25], "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
    return dt.isoformat()


def create_backup(db: Session, backup_path: str, db_path: str) -> dict:
    Path(backup_path).mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    filename = f"helledger_{now.strftime('%Y%m%d_%H%M%S')}.db"
    dest = os.path.join(backup_path, filename)
    shutil.copyfile(db_path, dest)
    rotate_backups(db, backup_path)
    return {"filename": filename, "size_bytes": os.path.getsize(dest), "created_at": now.isoformat()}


def list_backups(backup_path: str) -> list[dict]:
    p = Path(backup_path)
    if not p.exists():
        return []
    result = [
        {
            "filename": f.name,
            "size_bytes": f.stat().st_size,
            "created_at": _parse_created_at(f.name),
        }
        for f in p.iterdir()
        if FILENAME_RE.match(f.name)
    ]
    return sorted(result, key=lambda x: x["filename"], reverse=True)


def delete_backup(backup_path: str, filename: str) -> None:
    _validate_filename(filename)
    path = Path(backup_path) / filename
    if not path.exists():
        raise FileNotFoundError(filename)
    path.unlink()


def rotate_backups(db: Session, backup_path: str) -> None:
    retention_days = int(get_setting(db, "backup_retention_days", "7"))
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    p = Path(backup_path)
    if not p.exists():
        return
    for f in p.iterdir():
        if not FILENAME_RE.match(f.name):
            continue
        created = datetime.strptime(f.name[10:25], "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
        if created < cutoff:
            f.unlink()
