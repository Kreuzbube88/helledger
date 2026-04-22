<p align="center">
  <img src="frontend/public/logo.png" alt="HELLEDGER" width="450" height="450"/>
</p>

<p align="center">
  <strong>Self-Hosted Household Finance Tracker for Homelab</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-active-brightgreen" alt="Status">
  <img src="https://img.shields.io/badge/python-%3E%3D3.12-blue" alt="Python">
  <img src="https://img.shields.io/github/license/Kreuzbube88/helledger" alt="License">
  <img src="https://img.shields.io/badge/platform-Unraid-orange" alt="Platform">
</p>

---

HELLEDGER is a self-hosted household finance tracker built for homelab enthusiasts. It runs as a single Docker container, stores everything in a local SQLite database, and gives you full control over your financial data — no cloud dependency, no subscription, works offline as a PWA.

> ⚠️ HELLEDGER was built entirely with AI (Claude.ai). It is not designed for public internet exposure and should only be used within a local network / homelab.

---

## Features

- **Transactions** — Income and expense tracking with categories, accounts, and recurring entries
- **Accounts** — Multiple bank accounts per household
- **Budget** — Expected vs. actual comparison (Soll/Ist) per category and month
- **Year View** — Full-year category × month breakdown at a glance
- **Month View** — Detailed monthly Soll/Ist comparison with variance and savings rate
- **Net Worth** — Snapshot tracking of total assets and liabilities over time
- **Excel Import/Export** — Bulk transaction import and export to XLSX
- **CSV Import** — Transaction import from CSV files
- **Backups** — Automated scheduled backups to a configurable backup volume
- **OIDC Login** — Optional SSO via any OIDC provider (Authentik, Keycloak, etc.); native login always available
- **Admin Panel** — SMTP config, OIDC config, user management, registration control
- **Multi-Household** — Separate financial spaces per household; users can belong to multiple households
- **PWA** — Installable on desktop and mobile; offline shell via service worker
- **i18n** — German (default) and English; per-user language preference
- **Dark/Light Mode** — Manual toggle

---

## Installation

### Unraid Community Apps (recommended)

1. Open the **Apps** tab in Unraid
2. Search for **HELLEDGER**
3. Click **Install** and follow the template

HELLEDGER will be available at `http://YOUR-UNRAID-IP:3000`.

### Docker Compose

```yaml
services:
  helledger:
    image: ghcr.io/kreuzbube88/helledger:latest
    container_name: helledger
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - SECRET_KEY=your_secret_here   # openssl rand -hex 32
      - TZ=Europe/Berlin
    volumes:
      - /mnt/user/appdata/helledger:/data
      - /mnt/user/appdata/helledger/backups:/backups
```

### Docker Run

```bash
docker run -d \
  --name helledger \
  --restart unless-stopped \
  -p 3000:3000 \
  -v /path/to/appdata:/data \
  -v /path/to/backups:/backups \
  -e SECRET_KEY=$(openssl rand -hex 32) \
  ghcr.io/kreuzbube88/helledger:latest
```

---

## Quick Start

After installation, open the web UI at `http://YOUR-IP:3000`. The first registered user becomes the admin automatically. Head to the **Admin** panel to configure SMTP, OIDC, default language, and registration settings.

---

## Documentation

Full documentation is available in the [`docs/`](docs/en/installation.md) folder in both German and English, covering installation, first steps, import/export, backups, and admin configuration.

---

## Configuration

| Variable | Required | Default | Description |
|----------|---------|----------|-------------|
| `SECRET_KEY` | **Yes** | — | JWT signing key — use `openssl rand -hex 32` |
| `DATABASE_PATH` | No | `/data/helledger.db` | Absolute path to the SQLite database file |
| `PORT` | No | `3000` | HTTP port the app listens on |
| `TZ` | No | `UTC` | Container timezone |
| `DEFAULT_LANGUAGE` | No | `de` | UI language (`de`, `en`) |
| `ALLOW_REGISTRATION` | No | `true` | Allow new user self-registration |
| `BACKUP_INTERVAL_HOURS` | No | `24` | Hours between automatic backups (0 to disable) |
| `LOG_LEVEL` | No | `INFO` | Uvicorn log level |

All SMTP and OIDC configuration lives in the Admin UI and is stored in the database.

---

## License

Apache 2.0 © HEL*Apps
