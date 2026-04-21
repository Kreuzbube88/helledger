# Installation

## Requirements

- Docker and Docker Compose
- Port 3000 available (or configure a different port via ENV)

## Quick Start

```yaml
# docker-compose.yml
services:
  helledger:
    image: ghcr.io/kreuzbube88/helledger:1.0.0
    environment:
      SECRET_KEY: "your-secret-32-char-key"
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

The app will be available at [http://localhost:3000](http://localhost:3000).

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | **Required.** Min. 32 characters |
| `DATABASE_PATH` | `/data/helledger.db` | Path to SQLite database |
| `BACKUP_PATH` | `/backups` | Path for automatic backups |
| `TZ` | `Europe/Berlin` | Timezone |
| `ALLOW_REGISTRATION` | `true` | Allow new user registrations |
| `SMTP_HOST` | — | Optional: SMTP for emails |
| `OIDC_ENABLED` | `false` | Optional: Enable OIDC SSO |
