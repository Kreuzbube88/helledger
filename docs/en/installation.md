# 🚀 Installation

## Requirements

- Docker and Docker Compose
- Port 3000 available (configurable via `PORT`)

---

## Unraid Community Apps (recommended)

1. Open the **Apps** tab in Unraid
2. Search for **HELLEDGER**
3. Click **Install** and follow the template

HELLEDGER will be available at `http://YOUR-UNRAID-IP:3000`.

---

## Docker Compose

```yaml
services:
  helledger:
    image: ghcr.io/kreuzbube88/helledger:latest
    container_name: helledger
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - SECRET_KEY=your-secret-key   # openssl rand -hex 32
      - TZ=Europe/Berlin
    volumes:
      - /mnt/user/appdata/helledger:/data
      - /mnt/user/appdata/helledger/backups:/backups
```

```bash
docker compose up -d
```

---

## Docker Run

```bash
docker run -d \
  --name helledger \
  --restart unless-stopped \
  -p 3000:3000 \
  -v /path/to/appdata:/data \
  -v /path/to/backups:/backups \
  -e SECRET_KEY=$(openssl rand -hex 32) \
  -e TZ=Europe/Berlin \
  ghcr.io/kreuzbube88/helledger:latest
```

---

## Behind a Reverse Proxy

HELLEDGER runs as a single HTTP service on port 3000. Configure a simple proxy pass to that port — no additional routing needed.

**Traefik example (labels):**
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.helledger.rule=Host(`budget.your-domain.com`)"
  - "traefik.http.services.helledger.loadbalancer.server.port=3000"
```

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|---------|----------|-------------|
| `SECRET_KEY` | **Yes** | — | JWT signing key — generate with `openssl rand -hex 32` |
| `DATABASE_PATH` | No | `/data/helledger.db` | Path to the SQLite database file |
| `PORT` | No | `3000` | HTTP port the app listens on |
| `TZ` | No | `UTC` | Container timezone |
| `DEFAULT_LANGUAGE` | No | `de` | Default UI language (`de`, `en`) |
| `ALLOW_REGISTRATION` | No | `true` | Allow new user self-registration |
| `BACKUP_INTERVAL_HOURS` | No | `24` | Hours between automatic backups (0 to disable) |
| `LOG_LEVEL` | No | `INFO` | Uvicorn log level |

> SMTP and OIDC configuration is done inside the **Admin panel** and stored in the database.
