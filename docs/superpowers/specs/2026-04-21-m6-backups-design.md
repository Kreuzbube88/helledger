# HELLEDGER M6: Scheduled Backups — Design

## Ziel

Automatische und manuelle SQLite-Backups mit konfigurierbarer Aufbewahrungsdauer. Eigene Admin-only-Seite `/backup` mit manueller Auslösung, Backup-Liste, Download und Löschung.

## Architecture

asyncio-Hintergrundtask im FastAPI-Lifespan erstellt alle `BACKUP_INTERVAL_HOURS` ein Backup via `shutil.copy2`. Retention-Einstellung wird in einer neuen `app_settings`-Tabelle (Key-Value) gespeichert und ist über die UI konfigurierbar. Backup-Liste wird direkt aus dem Filesystem gelesen — keine eigene Backup-Metadatentabelle.

---

## 1. Datenbank

### Neue Tabelle `app_settings`

```sql
CREATE TABLE app_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
INSERT OR IGNORE INTO app_settings VALUES ('backup_retention_days', '7');
```

Alembic-Migration: `backend/alembic/versions/XXXX_add_app_settings.py`

---

## 2. Backend

### Neue Dateien

- `backend/app/services/backup.py` — Backup-Logik
- `backend/app/services/settings.py` — get/set `app_settings`
- `backend/app/routers/backup.py` — API, Prefix `/backup`

### BackupService (`services/backup.py`)

| Methode | Beschreibung |
|---------|-------------|
| `create_backup(db, backup_path, db_path)` | Kopiert SQLite-Datei nach `/backups/helledger_YYYYMMDD_HHMMSS.db`, rotiert danach |
| `list_backups(backup_path)` | Liest Verzeichnis, gibt `[{filename, size_bytes, created_at}]` zurück |
| `delete_backup(backup_path, filename)` | Löscht eine Datei (nach Namensvalidierung) |
| `rotate_backups(db, backup_path)` | Löscht Dateien älter als `backup_retention_days` Tage |

**Dateiname:** `helledger_YYYYMMDD_HHMMSS.db`

### SettingsService (`services/settings.py`)

| Methode | Beschreibung |
|---------|-------------|
| `get_setting(db, key, default)` | Liest Wert aus `app_settings` |
| `set_setting(db, key, value)` | Setzt Wert (upsert) |

### API-Endpunkte (`routers/backup.py`, Prefix `/backup`)

Alle Endpunkte: `is_admin` required, sonst `403`.

| Method | Path | Beschreibung |
|--------|------|-------------|
| `GET` | `/backup/settings` | Gibt `{"backup_retention_days": 7}` zurück |
| `PATCH` | `/backup/settings` | Setzt `backup_retention_days` (int, min 1) |
| `POST` | `/backup/trigger` | Erstellt sofort Backup + rotiert |
| `GET` | `/backup/list` | `[{filename, size_bytes, created_at}]` aus Filesystem |
| `GET` | `/backup/{filename}/download` | `FileResponse` — streamt Datei |
| `DELETE` | `/backup/{filename}` | Löscht Datei |

**Filename-Sanitization:** Regex `^helledger_\d{8}_\d{6}\.db$` — kein Path-Traversal möglich.

### Scheduler

In `main.py` `lifespan`:

```python
async def _backup_loop():
    while True:
        await asyncio.sleep(settings.BACKUP_INTERVAL_HOURS * 3600)
        await run_backup()  # wrapped in try/except, logged

@asynccontextmanager
async def lifespan(app):
    if not settings.TESTING:
        _run_migrations()
        asyncio.create_task(_backup_loop())
    yield
```

### Config (`config.py`)

```python
BACKUP_INTERVAL_HOURS: int = 24
BACKUP_PATH: str = "/backups"
```

---

## 3. Frontend

### Nav (`nav.js`)

`backup`-Eintrag nach `settings`, nur sichtbar wenn `user.is_admin === true`.

### View `frontend/js/views/backup.js`

Route: `#/backup`. Redirect zu `#/dashboard` wenn nicht Admin.

**Sektionen:**

1. **Einstellungen** — Inputfeld `backup_retention_days` + Speichern-Button
2. **Manuelles Backup** — Button "Backup jetzt erstellen"
3. **Backup-Liste** — Tabelle: Dateiname | Größe | Datum | Download | Löschen

Nach Trigger und Löschen: Liste neu laden. Fehler via `toast.js`.

### i18n

Neue Keys unter `"backup"` in `de.json` und `en.json`:

```json
"backup": {
  "title": "Backups",
  "settings": "Einstellungen",
  "retentionDays": "Aufbewahrung (Tage)",
  "save": "Speichern",
  "triggerBtn": "Backup jetzt erstellen",
  "triggerSuccess": "Backup erstellt",
  "list": "Vorhandene Backups",
  "filename": "Dateiname",
  "size": "Größe",
  "createdAt": "Datum",
  "download": "Herunterladen",
  "delete": "Löschen",
  "deleteConfirm": "Backup wirklich löschen?",
  "empty": "Keine Backups vorhanden",
  "noAccess": "Kein Zugriff"
}
```

---

## 4. Tests

- Unit-Tests für `BackupService.create_backup`, `list_backups`, `rotate_backups`, `delete_backup`
- Kein Scheduler-Test (asyncio-Timing, flaky)
- API-Tests für alle 6 Endpunkte (inkl. 403 für Nicht-Admin)
