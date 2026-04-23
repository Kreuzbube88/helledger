# 🛡️ Admin Panel

The admin panel is only visible to users with the **Admin** role. Access it via **Admin** in the navigation menu.

---

## 👥 User Management

The user list shows all registered accounts with their status and role.

| Action | Description |
|--------|-------------|
| **Deactivate** | Blocks login for this user |
| **Activate** | Unblocks a deactivated user |
| **Delete** | Permanently removes the user (requires confirmation) |

---

## 📊 System Status

Shows current instance metrics:

- Number of users
- Number of households
- Number of transactions
- Database size

---

## ⚙️ Settings

### General
- **Allow registration** — Enable or disable self-registration for new users
- **Default language** — Language for new users (`de` or `en`)

### 📧 SMTP (Email)
Configure an SMTP server for email functionality:

| Field | Description |
|-------|-------------|
| SMTP Host | Mail server hostname |
| SMTP Port | Port (typically 587 or 465) |
| SMTP User | Username |
| From Email | Sender address |

### 🔐 OIDC (Single Sign-On)
Optional SSO integration with Authentik, Keycloak, or any OIDC provider:

| Field | Description |
|-------|-------------|
| Enable OIDC | Toggle SSO on/off |
| Client ID | OIDC Client ID |
| Discovery URL | `https://your-provider/.well-known/openid-configuration` |

> Once OIDC is enabled, a **"Login with SSO"** button appears on the login page. Native login always remains available.
