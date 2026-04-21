# HELLEDGER M7: Tailwind UI Redesign — Design

## Ziel

Vollständiges Frontend-Redesign: Migration von plain HTML/JS auf Vue 3 + Vite + Tailwind CSS + shadcn-vue. Dark/Light-Mode-Toggle. Alle 9 Views werden als Vue SFCs neu implementiert. Backend bleibt unverändert.

## Architecture

Vue 3 (Composition API, `<script setup>`) mit Vite als Build-Tool. Tailwind CSS via npm (kein CDN). shadcn-vue für Komponenten. Pinia für Auth- und Theme-State. Vue Router (Hash-Mode, gleiche `#/`-URLs). vue-i18n ersetzt i18next-CDN. vue-chartjs wraps Chart.js für alle Diagramme. Sonner-Toast ersetzt toast.js.

---

## 1. Stack & Abhängigkeiten

### `frontend/package.json` — neue Dependencies

**Runtime:**
```json
{
  "vue": "^3.5",
  "vue-router": "^4.4",
  "pinia": "^2.2",
  "vue-i18n": "^10",
  "vue-chartjs": "^5",
  "chart.js": "^4",
  "@fontsource-variable/inter": "*",
  "radix-vue": "^1.9",
  "class-variance-authority": "^0.7",
  "clsx": "^2",
  "tailwind-merge": "^2",
  "lucide-vue-next": "^0.400",
  "vue-sonner": "^1"
}
```

**DevDependencies:**
```json
{
  "vite": "^6",
  "@vitejs/plugin-vue": "^5",
  "tailwindcss": "^3.4",
  "autoprefixer": "^10",
  "postcss": "^8"
}
```

shadcn-vue-Komponenten werden via CLI installiert: `npx shadcn-vue@latest add <component>`

---

## 2. Dateistruktur

```
frontend/
├── index.html                    ← Vite-Entry (vereinfacht, kein CDN)
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── package.json
├── src/
│   ├── main.js                   ← Vue-App-Entry
│   ├── App.vue                   ← Root + Toaster
│   ├── router/
│   │   └── index.js              ← Vue Router, Guards
│   ├── stores/
│   │   ├── auth.js               ← Pinia: Token, User, isAdmin
│   │   └── theme.js              ← Pinia: isDark, toggle()
│   ├── lib/
│   │   ├── api.js                ← API-Composable (get/post/patch/delete + refresh)
│   │   └── utils.js              ← shadcn cn() helper
│   ├── components/
│   │   ├── ui/                   ← shadcn-vue Komponenten
│   │   └── AppNav.vue            ← Navigationsleiste
│   ├── views/
│   │   ├── LoginView.vue
│   │   ├── DashboardView.vue
│   │   ├── AccountsView.vue
│   │   ├── CategoriesView.vue
│   │   ├── TransactionsView.vue
│   │   ├── ReportsView.vue
│   │   ├── ImportView.vue
│   │   ├── SettingsView.vue
│   │   └── BackupView.vue
│   ├── locales/
│   │   ├── de.json               ← unverändert übernommen
│   │   └── en.json               ← unverändert übernommen
│   └── assets/
│       └── main.css              ← Tailwind directives + shadcn CSS-Variablen
```

---

## 3. Design-System

### Farbpalette

shadcn-vue "New York" Style. CSS-Variablen in `src/assets/main.css`:

| Token | Dark | Light |
|---|---|---|
| `--background` | zinc-950 | white |
| `--card` | zinc-900 | zinc-50 |
| `--primary` | indigo-500 | indigo-600 |
| `--muted` | zinc-800 | zinc-100 |
| `--destructive` | rose-500 | rose-600 |

Semantische Farben (fix, kein Dark/Light-Switch):
- Income: `text-emerald-500`
- Expense: `text-rose-500`
- Transfer: `text-violet-500`

### Dark/Light-Mode

- `useThemeStore()` setzt `.dark` auf `<html>`-Element
- Default: `window.matchMedia('(prefers-color-scheme: dark)').matches`
- Persistenz: `localStorage.getItem('helledger-theme')`
- Toggle in `AppNav.vue` via `lucide-vue-next` Sun/Moon-Icon + `Switch`-Komponente

### Schriftart

Inter Variable via `@fontsource-variable/inter` — kein Google CDN.

---

## 4. State Management

### `stores/auth.js` (Pinia)

```javascript
// State
token: string | null        // aus localStorage
user: UserObject | null     // { id, name, email, role, active_household_id }

// Getters
isAuthenticated: !!token
isAdmin: user?.role === 'admin'

// Actions
login(email, password) → setzt token + user
logout()                → löscht token + user
fetchUser()             → GET /auth/me
```

### `stores/theme.js` (Pinia)

```javascript
// State
isDark: boolean

// Actions
toggle()                → wechselt .dark-Klasse auf <html>
```

---

## 5. Router

Vue Router im Hash-Mode (`createWebHashHistory()`):

| Route | View | Guard |
|---|---|---|
| `#/login` | LoginView | Weiterleitung zu #/dashboard wenn eingeloggt |
| `#/register` | LoginView | Weiterleitung zu #/dashboard wenn eingeloggt |
| `#/dashboard` | DashboardView | requiresAuth |
| `#/accounts` | AccountsView | requiresAuth |
| `#/categories` | CategoriesView | requiresAuth |
| `#/transactions` | TransactionsView | requiresAuth |
| `#/reports` | ReportsView | requiresAuth |
| `#/import` | ImportView | requiresAuth |
| `#/settings` | SettingsView | requiresAuth |
| `#/backup` | BackupView | requiresAuth + requiresAdmin |

Navigation Guard prüft `useAuthStore().isAuthenticated` und `isAdmin`.

---

## 6. API-Layer (`lib/api.js`)

Composable `useApi()` — gleiche Logik wie bisherige `api.js`:

```javascript
// Methoden
get(path)
post(path, body)
patch(path, body)
delete(path)

// Intern
_request(method, path, body, retry)   → fetch mit Bearer-Token
_tryRefresh()                          → POST /auth/refresh, setzt neuen Token
```

Token wird aus `useAuthStore()` gelesen (kein direktes localStorage-Zugriff in Views).

---

## 7. AppNav.vue

Komponente ersetzt `nav.js`. Responsive: Desktop-Horizontalleiste, Mobile-Hamburger → `Sheet`-Overlay.

Elemente:
- Brand-Logo "HELLEDGER" links
- Nav-Links (nur wenn eingeloggt): dashboard, accounts, categories, transactions, reports, import, settings, + backup (nur admin)
- Haushalt-Switcher: `DropdownMenu` mit Haushaltsliste
- User-Name
- Dark/Light-`Switch` mit Sun/Moon-Icon
- Logout-Button

---

## 8. shadcn-vue Komponenten

Installierte Komponenten via CLI:

| Komponente | Einsatz |
|---|---|
| `button` | überall |
| `input`, `label` | Formulare |
| `card`, `card-header`, `card-content`, `card-footer` | Dashboard, Settings, Backup |
| `table`, `table-head`, `table-body`, `table-row`, `table-cell` | Accounts, Categories, Transactions |
| `dialog`, `dialog-content`, `dialog-header`, `dialog-footer` | Create/Edit-Modals |
| `select`, `select-trigger`, `select-content`, `select-item` | Filter-Dropdowns |
| `badge` | Transaktionstypen, Rollen |
| `tabs`, `tabs-list`, `tabs-trigger`, `tabs-content` | Reports |
| `dropdown-menu` | Haushalt-Switcher |
| `switch` | Dark/Light-Toggle |
| `separator` | Layout |
| `sheet` | Mobile Nav-Overlay |
| `sonner` (vue-sonner) | Toast-Nachrichten global |
| `avatar` | User-Avatar in Nav |

---

## 9. Views

### LoginView.vue
Zentrierte Card mit zwei Tabs (Login / Register). Input, Label, Button. Fehler als Sonner-Toast.

### DashboardView.vue
Zwei Cards: Soll/Ist-Übersicht (Balken via Tailwind `w-[X%]`) + Monatsnavigation. Chart.js-Donut via vue-chartjs für Ausgaben nach Kategorie. Monatsselektor oben.

### AccountsView.vue
Table mit allen Konten. "Konto hinzufügen"-Button öffnet Dialog. Edit/Delete per Row-Action-Buttons.

### CategoriesView.vue
Table mit Einrückung für Unterkategorien. Dialog für Create/Edit. Badge für Typ.

### TransactionsView.vue
Table mit Monatsfilter + Account/Kategorie-Filter (Select). Dialog für Create/Edit. Badge für Typ (income/expense/transfer). Betrag farbig. Paginierung via Monats-Pager.

### ReportsView.vue
Tabs für die 4 Charts (Ausgaben nach Kategorie, Balance-Verlauf, Monatstrend, Soll/Ist). Datums-Filter oben. vue-chartjs für alle Charts. CSV-Export-Button.

### ImportView.vue
Wizard-Stepper (3 Schritte: Upload → Mapping → Ergebnis) als Card-basierter Ablauf. Drag-and-Drop-Zone. Table für Preview. Badge für Import-Ergebnis.

### SettingsView.vue
Zwei Cards: Haushalt (Name + Save) + Mitglieder (Table mit Remove-Button). Add-Member-Formular am Ende.

### BackupView.vue
Drei Cards: Einstellungen (Retention-Input), Trigger-Button, Backup-Liste (Table mit Download/Delete).

---

## 10. Kein Breaking Change am Backend

Alle FastAPI-Endpunkte, Auth-Flows, Schemas und Routen bleiben vollständig unverändert. Nur `frontend/` wird umgebaut — Backend läuft identisch weiter. Docker-Setup funktioniert weiterhin: Vite baut nach `frontend/dist/`, FastAPI serviert `dist/` als Static Files.

`backend/app/main.py` muss den Static-Files-Pfad anpassen: von `frontend/` auf `frontend/dist/`.

---

## 11. Build & Docker

**Dev:**
```bash
cd frontend
npm install
npm run dev       # Vite Dev-Server auf Port 5173
# Backend separat: uvicorn auf Port 3000
# Vite proxy /api → localhost:3000
```

**Production (Docker):**
```bash
npm run build     # Output: frontend/dist/
```

Dockerfile-Anpassung: `npm ci && npm run build` vor dem Python-Layer. FastAPI serviert `frontend/dist/` statt `frontend/`.

**`vite.config.js`** Proxy für Dev:
```javascript
server: {
  proxy: {
    '/api': 'http://localhost:3000'
  }
}
```
