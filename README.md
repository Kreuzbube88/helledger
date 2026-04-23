<p align="center">
  <img src="frontend/public/logo.png" alt="HELLEDGER" width="450" height="450"/>
</p>

<p align="center">
  <strong>Self-Hosted Household Budget Ledger for Homelab</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-active-brightgreen" alt="Status">
  <img src="https://img.shields.io/badge/python-%3E%3D3.12-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-GPL--3.0-blue" alt="License">
  <img src="https://img.shields.io/badge/platform-Unraid-orange" alt="Platform">
</p>

---

HELLEDGER is a self-hosted household budget ledger built for homelab enthusiasts. It lets you manage multiple accounts and households, track income and expenses by category, and get a clear picture of what comes in, what goes out, and what's left — month by month and year by year. Everything runs in a single Docker container with a local SQLite database. No cloud, no subscription, full data ownership.

> ⚠️ HELLEDGER was built entirely with AI (Claude.ai). It is not designed for public internet exposure and should only be used within a local network / homelab.

---

## Features

### Transactions & Accounts
- **Transactions** — Manual income, expense, and transfer entries with category and account assignment
- **Accounts** — Multiple bank accounts per household with roles: Main, Fixed Costs, Variable, Savings, Separate (excluded from calculations)
- **Categories** — Income, fixed cost, and variable expense categories with subcategories and color coding
- **CSV / OFX / QFX Import** — Bulk transaction import with column mapping and duplicate detection
- **Global Search** — Full-text search across all transactions

### Budget & Planning
- **Fixed Costs** — Recurring income, expenses, and savings transfers with configurable intervals (monthly, quarterly, semi-annual, annual); auto-booking each month; reserve tracking for non-monthly costs
- **Forecast** — 12-month projection based on fixed costs with cumulative savings account balance
- **Savings Goals** — Target amount and date, linked savings account, progress tracking

### Loans
- **Loan Management** — Consumer loans and mortgages with full amortization schedules
- **Extra Payments** — One-time and recurring extra payments with term-shortening or payment-reduction effect
- **Loan KPIs** — Interest saved, months saved, current balance, estimated payoff date
- **CSV Export** — Full amortization schedule export

### Reporting & Overview
- **Dashboard** — Monthly KPIs (savings rate, debt-to-income ratio, reserve coverage), animated account balances by role, expense donut chart, savings goals widget, expiring fixed cost warnings
- **Month View** — Detailed monthly breakdown by category (income / fixed / variable / savings transfers) with KPI bar and available balance split by account role
- **Year View** — Full-year category × month grid with totals
- **Reports** — Expense by category, monthly trend as stacked bar (fixed + variable + savings), balance history

### Infrastructure
- **Backups** — Scheduled and manual backups to a configurable backup volume with retention policy
- **OIDC Login** — Optional SSO via any OIDC provider (Authentik, Keycloak, etc.); native login always available
- **Admin Panel** — User management, SMTP config, OIDC config, registration control
- **Multi-Household** — Separate financial spaces per household; users can belong to multiple households
- **PWA** — Installable on desktop and mobile; offline shell via service worker
- **i18n** — German (default) and English; per-user language preference
- **Dark / Light Mode** — Manual toggle

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

GPL-3.0 © HEL*Apps
