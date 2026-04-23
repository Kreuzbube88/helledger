# 🚀 Installation

## Voraussetzungen

- Docker und Docker Compose
- Port 3000 verfügbar (konfigurierbar via `PORT`)

---

## Unraid Community Apps (empfohlen)

1. **Apps**-Tab in Unraid öffnen
2. Nach **HELLEDGER** suchen
3. **Installieren** klicken und dem Template folgen

HELLEDGER ist dann unter `http://DEINE-UNRAID-IP:3000` erreichbar.

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
      - SECRET_KEY=dein-geheimer-schluessel   # openssl rand -hex 32
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
  -v /pfad/zu/appdata:/data \
  -v /pfad/zu/backups:/backups \
  -e SECRET_KEY=$(openssl rand -hex 32) \
  -e TZ=Europe/Berlin \
  ghcr.io/kreuzbube88/helledger:latest
```

---

## Hinter einem Reverse Proxy

HELLEDGER läuft als einzelner HTTP-Dienst auf Port 3000. Konfiguriere einfach einen Proxy-Pass auf diesen Port. Kein weiteres Routing notwendig.

**Traefik-Beispiel (Labels):**
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.helledger.rule=Host(`budget.deine-domain.de`)"
  - "traefik.http.services.helledger.loadbalancer.server.port=3000"
```

---

## ⚙️ Umgebungsvariablen

| Variable | Pflicht | Standard | Beschreibung |
|----------|---------|----------|--------------|
| `SECRET_KEY` | **Ja** | — | JWT-Schlüssel — mit `openssl rand -hex 32` generieren |
| `DATABASE_PATH` | Nein | `/data/helledger.db` | Pfad zur SQLite-Datenbank |
| `PORT` | Nein | `3000` | HTTP-Port der App |
| `TZ` | Nein | `UTC` | Container-Zeitzone |
| `DEFAULT_LANGUAGE` | Nein | `de` | Standard-Sprache (`de`, `en`) |
| `ALLOW_REGISTRATION` | Nein | `true` | Neue Registrierungen erlauben |
| `BACKUP_INTERVAL_HOURS` | Nein | `24` | Stunden zwischen automatischen Backups (0 = deaktiviert) |
| `LOG_LEVEL` | Nein | `INFO` | Uvicorn Log-Level |

> SMTP- und OIDC-Konfiguration erfolgt im **Admin-Bereich** der App und wird in der Datenbank gespeichert.
