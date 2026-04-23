# 💾 Backups

HELLEDGER erstellt automatisch Backups der SQLite-Datenbank im konfigurierten Backup-Volume.

---

## Automatische Backups

Backups werden im Intervall erstellt, das via `BACKUP_INTERVAL_HOURS` konfiguriert ist (Standard: 24 Stunden).

```
BACKUP_INTERVAL_HOURS=24   # alle 24 Stunden
BACKUP_INTERVAL_HOURS=0    # deaktiviert
```

---

## Backup-Verwaltung

Unter **Backups** (Navigationsmenü) kannst du:

- **Backup jetzt erstellen** — Sofort-Backup auslösen
- **Herunterladen** — Backup als Datei lokal sichern
- **Löschen** — Einzelne Backups entfernen

### Aufbewahrung

Die **Aufbewahrungsdauer** (in Tagen) lässt sich direkt in der Backup-Seite konfigurieren. Ältere Backups werden automatisch gelöscht.

---

## Wiederherstellung

Zum Wiederherstellen eines Backups:

1. Container stoppen
2. Backup-Datei nach `/data/helledger.db` kopieren
3. Container starten

```bash
docker stop helledger
cp backup_2026-04-23.db /pfad/zu/appdata/helledger.db
docker start helledger
```
