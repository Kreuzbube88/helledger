# 💾 Backups

HELLEDGER automatically creates backups of the SQLite database in the configured backup volume.

---

## Automatic Backups

Backups are created on the interval configured via `BACKUP_INTERVAL_HOURS` (default: 24 hours).

```
BACKUP_INTERVAL_HOURS=24   # every 24 hours
BACKUP_INTERVAL_HOURS=0    # disabled
```

---

## Backup Management

Under **Backups** (navigation menu) you can:

- **Create backup now** — trigger an immediate backup
- **Download** — save a backup file locally
- **Delete** — remove individual backups

### Retention

The **retention period** (in days) can be configured directly on the Backups page. Older backups are deleted automatically.

---

## Restore

To restore a backup:

1. Stop the container
2. Copy the backup file to `/data/helledger.db`
3. Start the container

```bash
docker stop helledger
cp backup_2026-04-23.db /path/to/appdata/helledger.db
docker start helledger
```
