import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars!!")
os.environ.setdefault("DATABASE_PATH", ":memory:")
os.environ.setdefault("TESTING", "true")

from app.models.settings import AppSetting
from app.services.settings import get_setting, set_setting


def _make_db_with_setting(key: str, value: str):
    setting = AppSetting(key=key, value=value)
    db = MagicMock()
    db.get.return_value = setting
    return db


def _make_empty_db():
    db = MagicMock()
    db.get.return_value = None
    return db


def test_get_setting_returns_value():
    db = _make_db_with_setting("backup_retention_days", "14")
    assert get_setting(db, "backup_retention_days", "7") == "14"


def test_get_setting_returns_default_when_missing():
    db = _make_empty_db()
    assert get_setting(db, "backup_retention_days", "7") == "7"


def test_set_setting_updates_existing():
    existing = AppSetting(key="backup_retention_days", value="7")
    db = MagicMock()
    db.get.return_value = existing

    set_setting(db, "backup_retention_days", "30")

    assert existing.value == "30"
    db.commit.assert_called_once()


def test_set_setting_inserts_when_missing():
    db = _make_empty_db()

    set_setting(db, "backup_retention_days", "30")

    db.add.assert_called_once()
    db.commit.assert_called_once()
    added = db.add.call_args[0][0]
    assert added.key == "backup_retention_days"
    assert added.value == "30"


from app.services.backup import (
    FILENAME_RE,
    create_backup,
    delete_backup,
    list_backups,
    rotate_backups,
)


def _mock_db_retention(days: str = "7") -> MagicMock:
    return _make_db_with_setting("backup_retention_days", days)


def test_filename_regex_accepts_valid():
    assert FILENAME_RE.match("helledger_20260421_143000.db")


def test_filename_regex_rejects_traversal():
    assert not FILENAME_RE.match("../etc/passwd")
    assert not FILENAME_RE.match("helledger_2026042_143000.db")


def test_create_backup_creates_file(tmp_path):
    db_file = tmp_path / "helledger.db"
    db_file.write_bytes(b"SQLite format 3")
    backup_dir = tmp_path / "backups"

    result = create_backup(_mock_db_retention(), str(backup_dir), str(db_file))

    files = list(backup_dir.iterdir())
    assert len(files) == 1
    assert FILENAME_RE.match(files[0].name)
    assert result["filename"] == files[0].name
    assert result["size_bytes"] == len(b"SQLite format 3")


def test_create_backup_creates_dir_if_missing(tmp_path):
    db_file = tmp_path / "helledger.db"
    db_file.write_bytes(b"x")
    backup_dir = tmp_path / "deep" / "backups"

    create_backup(_mock_db_retention(), str(backup_dir), str(db_file))

    assert backup_dir.exists()


def test_list_backups_returns_descending_order(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    (backup_dir / "helledger_20260101_120000.db").write_bytes(b"a")
    (backup_dir / "helledger_20260421_120000.db").write_bytes(b"bb")

    result = list_backups(str(backup_dir))

    assert len(result) == 2
    assert result[0]["filename"] == "helledger_20260421_120000.db"
    assert result[1]["filename"] == "helledger_20260101_120000.db"
    assert result[0]["size_bytes"] == 2
    assert "created_at" in result[0]


def test_list_backups_ignores_non_matching_files(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    (backup_dir / "helledger_20260101_120000.db").write_bytes(b"ok")
    (backup_dir / "README.txt").write_bytes(b"ignore")

    result = list_backups(str(backup_dir))

    assert len(result) == 1


def test_list_backups_nonexistent_dir_returns_empty(tmp_path):
    assert list_backups(str(tmp_path / "missing")) == []


def test_delete_backup_removes_file(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    f = backup_dir / "helledger_20260101_120000.db"
    f.write_bytes(b"x")

    delete_backup(str(backup_dir), "helledger_20260101_120000.db")

    assert not f.exists()


def test_delete_backup_invalid_filename_raises_value_error(tmp_path):
    with pytest.raises(ValueError, match="invalid_filename"):
        delete_backup(str(tmp_path), "../evil.db")


def test_delete_backup_missing_file_raises_file_not_found(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        delete_backup(str(backup_dir), "helledger_20260101_120000.db")


def test_rotate_removes_files_older_than_retention(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    old_file = backup_dir / "helledger_20260101_120000.db"
    old_file.write_bytes(b"old")
    old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).timestamp()
    os.utime(old_file, (old_ts, old_ts))

    new_file = backup_dir / "helledger_20260421_120000.db"
    new_file.write_bytes(b"new")

    rotate_backups(_mock_db_retention("7"), str(backup_dir))

    assert not old_file.exists()
    assert new_file.exists()


def test_rotate_keeps_files_within_retention(tmp_path):
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    recent_file = backup_dir / "helledger_20260420_120000.db"
    recent_file.write_bytes(b"recent")

    rotate_backups(_mock_db_retention("7"), str(backup_dir))

    assert recent_file.exists()
