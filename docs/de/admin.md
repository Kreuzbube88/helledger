# 🛡️ Adminbereich

Der Adminbereich ist nur für Benutzer mit der Rolle **Admin** sichtbar. Erreichbar über das Navigationsmenü unter **Admin**.

---

## 👥 Benutzerverwaltung

Die Benutzerliste zeigt alle registrierten Accounts mit Status und Rolle.

| Aktion | Beschreibung |
|--------|--------------|
| **Deaktivieren** | Sperrt den Login für diesen Benutzer |
| **Aktivieren** | Entsperrt einen gesperrten Benutzer |
| **Löschen** | Entfernt den Benutzer dauerhaft (nach Bestätigung) |

---

## 📊 Systemstatus

Zeigt aktuelle Metriken der Instanz:

- Anzahl Benutzer
- Anzahl Haushalte
- Anzahl Transaktionen
- Datenbankgröße

---

## ⚙️ Einstellungen

### Allgemein
- **Registrierung erlauben** — Neue Nutzer können sich selbst registrieren (ein-/ausschalten)
- **Standardsprache** — Sprache für neue Benutzer (`de` oder `en`)

### 📧 SMTP (E-Mail)
Konfiguriere einen SMTP-Server für zukünftige E-Mail-Funktionen:

| Feld | Beschreibung |
|------|--------------|
| SMTP Host | Hostname des Mailservers |
| SMTP Port | Port (meist 587 oder 465) |
| SMTP User | Benutzername |
| Absender-E-Mail | Absenderadresse |

### 🔐 OIDC (Single Sign-On)
Optionale SSO-Anbindung an Authentik, Keycloak oder andere OIDC-Provider:

| Feld | Beschreibung |
|------|--------------|
| OIDC aktivieren | SSO ein-/ausschalten |
| Client ID | OIDC Client ID |
| Discovery URL | `https://dein-provider/.well-known/openid-configuration` |

> Nach dem Aktivieren von OIDC erscheint auf der Login-Seite ein **"Login mit SSO"**-Button. Der native Login bleibt immer verfügbar.
