# Installation

## Voraussetzungen

- Docker und Docker Compose
- Port 3000 verfügbar (oder beliebiger anderer Port via ENV)

## Schnellstart

```yaml
# docker-compose.yml
services:
  helledger:
    image: ghcr.io/kreuzbube88/helledger:1.0.0
    environment:
      SECRET_KEY: "dein-geheimes-32-zeichen-key"
      TZ: "Europe/Berlin"
    ports:
      - "3000:3000"
    volumes:
      - helledger_data:/data
      - helledger_backups:/backups

volumes:
  helledger_data:
  helledger_backups:
```

```bash
docker compose up -d
```

Die App ist dann unter [http://localhost:3000](http://localhost:3000) erreichbar.

## Hinter einem Reverse Proxy

Traefik-Beispiel: Füge Labels hinzu.

## Umgebungsvariablen

| Variable | Standard | Beschreibung |
|---|---|---|
| `SECRET_KEY` | — | **Pflicht.** Min. 32 Zeichen |
| `DATABASE_PATH` | `/data/helledger.db` | Pfad zur SQLite-Datenbank |
| `BACKUP_PATH` | `/backups` | Pfad für automatische Backups |
| `TZ` | `Europe/Berlin` | Zeitzone |
| `ALLOW_REGISTRATION` | `true` | Neue Registrierungen erlauben |
| `SMTP_HOST` | — | Optional: SMTP für E-Mails |
| `OIDC_ENABLED` | `false` | Optional: OIDC SSO aktivieren |
