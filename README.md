# HELLEDGER

Self-hosted personal finance tracker — multi-user, multi-currency, multi-account, with PWA support.

## Quickstart

```yaml
# docker-compose.yml
services:
  helledger:
    image: ghcr.io/kreuzbube88/helledger:latest
    container_name: helledger
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_PATH=/data/helledger.db
      - TZ=Europe/Berlin
    volumes:
      - ./data:/data
      - ./backups:/backups
```

```bash
mkdir -p data backups
echo "SECRET_KEY=$(openssl rand -hex 32)" > .env
docker compose up -d
```

Open http://localhost:3000.

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | yes | — | JWT signing key, min 32 chars |
| `DATABASE_PATH` | no | `/data/helledger.db` | SQLite file path |
| `PORT` | no | `3000` | Listening port |
| `TZ` | no | `UTC` | Container timezone |
| `DEFAULT_LANGUAGE` | no | `en` | UI language (`en`, `de`) |
| `ALLOW_REGISTRATION` | no | `true` | Allow new user self-registration |
| `FIRST_USER_IS_ADMIN` | no | `true` | First registered user gets admin role |
| `LOG_LEVEL` | no | `INFO` | Uvicorn log level |

## Volumes

| Path | Purpose |
|---|---|
| `/data` | SQLite database |
| `/backups` | Backup files (manual or automated) |

## Development

```bash
# Backend
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --port 3000

# Tests
pytest -v
```

Frontend is plain HTML/JS — open `frontend/index.html` or serve via uvicorn (static files mounted at `/`).

## Milestones

| Milestone | Status | Description |
|---|---|---|
| M1 | done | Foundation — auth, accounts, transactions, Docker, CI |
| M2 | pending | Recurring transactions + budget rules |
| M3 | pending | Multi-currency + exchange rates |
| M4 | pending | Reporting & charts |
| M5 | pending | CSV/OFX import |
| M6 | pending | Scheduled backups |
| M7 | pending | Tailwind UI redesign |
| M8 | pending | Mobile PWA polish |
| M9 | pending | Public release hardening |

## License

MIT
