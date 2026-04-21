# HELLEDGER M7: Tailwind UI Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate HELLEDGER frontend from plain HTML/JS to Vue 3 + Vite + Tailwind CSS + shadcn-vue with dark/light mode.

**Architecture:** Vue 3 Composition API (`<script setup>`), Vite build, Pinia for auth/theme, Vue Router (hash mode), vue-i18n replacing i18next CDN, vue-chartjs wrapping Chart.js, vue-sonner for toasts. Token read from localStorage in api.js to avoid circular dependency with auth store. Backend unchanged.

**Tech Stack:** Vue 3.5, Vite 6, Tailwind 3.4, shadcn-vue (New York style, zinc base, indigo primary), Pinia 2.2, Vue Router 4.4, vue-i18n 10, vue-chartjs 5, Chart.js 4, lucide-vue-next, vue-sonner, Inter Variable font.

---

## File Map

```
frontend/
├── index.html                    ← REPLACE (Vite entry, no CDN)
├── package.json                  ← CREATE
├── vite.config.js                ← CREATE
├── tailwind.config.js            ← CREATE
├── postcss.config.js             ← CREATE
├── components.json               ← CREATE (shadcn-vue config)
├── public/
│   ├── manifest.json             ← MOVE from frontend/manifest.json
│   ├── service-worker.js         ← MOVE from frontend/service-worker.js
│   └── logo.png                  ← MOVE from frontend/logo.png
└── src/
    ├── main.js                   ← CREATE
    ├── App.vue                   ← CREATE
    ├── assets/
    │   └── main.css              ← CREATE (Tailwind directives + CSS vars)
    ├── lib/
    │   ├── utils.js              ← CREATE (cn() helper)
    │   └── api.js                ← CREATE (fetch composable, localStorage token)
    ├── stores/
    │   ├── auth.js               ← CREATE (Pinia)
    │   └── theme.js              ← CREATE (Pinia)
    ├── locales/
    │   ├── de.json               ← CREATE (copy + add nav.import)
    │   └── en.json               ← CREATE (copy + add nav.import)
    ├── router/
    │   └── index.js              ← CREATE
    ├── components/
    │   ├── AppNav.vue            ← CREATE
    │   └── ui/                   ← shadcn-vue CLI output
    └── views/
        ├── LoginView.vue
        ├── DashboardView.vue
        ├── AccountsView.vue
        ├── CategoriesView.vue
        ├── TransactionsView.vue
        ├── ReportsView.vue
        ├── ImportView.vue
        ├── SettingsView.vue
        └── BackupView.vue
```

Backend changes:
- `backend/app/main.py:93-95` — change static path from `frontend/` to `frontend/dist/`
- `Dockerfile` — add `npm ci && npm run build` in builder stage, copy only `dist/`

---

## Task 1: Scaffold Vite + Tailwind

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/components.json`
- Replace: `frontend/index.html`
- Create: `frontend/public/` (move static assets)
- Create: `frontend/src/assets/main.css`

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "helledger-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@fontsource-variable/inter": "*",
    "chart.js": "^4",
    "class-variance-authority": "^0.7",
    "clsx": "^2",
    "lucide-vue-next": "^0.400",
    "pinia": "^2.2",
    "radix-vue": "^1.9",
    "tailwind-merge": "^2",
    "vue": "^3.5",
    "vue-chartjs": "^5",
    "vue-i18n": "^10",
    "vue-router": "^4.4",
    "vue-sonner": "^1"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5",
    "autoprefixer": "^10",
    "postcss": "^8",
    "tailwindcss": "^3.4",
    "vite": "^6"
  }
}
```

- [ ] **Step 2: Create `frontend/vite.config.js`**

```javascript
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      '/api': 'http://localhost:3000'
    }
  }
})
```

- [ ] **Step 3: Create `frontend/tailwind.config.js`**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{vue,js,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter Variable', 'Inter', 'sans-serif'],
      },
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 4: Create `frontend/postcss.config.js`**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 5: Create `frontend/components.json`** (shadcn-vue config, no TypeScript)

```json
{
  "$schema": "https://shadcn-vue.com/schema.json",
  "style": "new-york",
  "typescript": false,
  "tailwind": {
    "config": "tailwind.config.js",
    "css": "src/assets/main.css",
    "baseColor": "zinc",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib"
  }
}
```

- [ ] **Step 6: Replace `frontend/index.html`** (Vite entry, no CDN scripts)

```html
<!DOCTYPE html>
<html lang="de" class="">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>HELLEDGER</title>
  <link rel="manifest" href="/manifest.json" />
  <meta name="theme-color" content="#6366f1" />
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 7: Create `frontend/public/` and move static assets**

```bash
cd frontend
mkdir -p public
# Move existing static assets into Vite's public folder so they're copied to dist/
mv manifest.json public/manifest.json 2>/dev/null || true
mv service-worker.js public/service-worker.js 2>/dev/null || true
mv logo.png public/logo.png 2>/dev/null || true
```

- [ ] **Step 8: Create `frontend/src/assets/main.css`** (Tailwind + CSS variables with indigo primary)

```css
@import "@fontsource-variable/inter";

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --card: 0 0% 98%;
    --card-foreground: 240 10% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 3.9%;
    --primary: 243.4 75.4% 58.6%;
    --primary-foreground: 0 0% 98%;
    --secondary: 240 4.8% 95.9%;
    --secondary-foreground: 240 5.9% 10%;
    --muted: 240 4.8% 95.9%;
    --muted-foreground: 240 3.8% 46.1%;
    --accent: 240 4.8% 95.9%;
    --accent-foreground: 240 5.9% 10%;
    --destructive: 347.7 77.2% 49.8%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 5.9% 90%;
    --input: 240 5.9% 90%;
    --ring: 243.4 75.4% 58.6%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 240 10% 3.9%;
    --foreground: 0 0% 98%;
    --card: 240 5.9% 10%;
    --card-foreground: 0 0% 98%;
    --popover: 240 5.9% 10%;
    --popover-foreground: 0 0% 98%;
    --primary: 238.7 83.5% 66.7%;
    --primary-foreground: 240 10% 3.9%;
    --secondary: 240 3.7% 15.9%;
    --secondary-foreground: 0 0% 98%;
    --muted: 240 3.7% 15.9%;
    --muted-foreground: 240 5% 64.9%;
    --accent: 240 3.7% 15.9%;
    --accent-foreground: 0 0% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 3.7% 15.9%;
    --input: 240 3.7% 15.9%;
    --ring: 238.7 83.5% 66.7%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground font-sans antialiased;
  }
}
```

- [ ] **Step 9: Install dependencies**

```bash
cd frontend && npm install
```

Expected: `node_modules/` created, no errors.

- [ ] **Step 10: Verify scaffold builds**

```bash
cd frontend && npm run build
```

Expected: `dist/` created, build succeeds (will warn about empty entry but that's OK).

- [ ] **Step 11: Commit**

```bash
git add frontend/package.json frontend/vite.config.js frontend/tailwind.config.js \
        frontend/postcss.config.js frontend/components.json frontend/index.html \
        frontend/public/ frontend/src/assets/main.css
git commit -m "feat: scaffold vite + tailwind + shadcn-vue config"
```

---

## Task 2: Install shadcn-vue Components

**Files:**
- Create: `frontend/src/components/ui/` (shadcn CLI output)
- Create: `frontend/src/lib/utils.js` (needed before add commands)

- [ ] **Step 1: Create `frontend/src/lib/utils.js`** (shadcn `cn()` helper — must exist before `npx shadcn-vue add`)

```javascript
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 2: Install all shadcn-vue components via CLI**

Run these from `frontend/`:

```bash
cd frontend
npx shadcn-vue@latest add button --yes
npx shadcn-vue@latest add input --yes
npx shadcn-vue@latest add label --yes
npx shadcn-vue@latest add card --yes
npx shadcn-vue@latest add table --yes
npx shadcn-vue@latest add dialog --yes
npx shadcn-vue@latest add select --yes
npx shadcn-vue@latest add badge --yes
npx shadcn-vue@latest add tabs --yes
npx shadcn-vue@latest add dropdown-menu --yes
npx shadcn-vue@latest add switch --yes
npx shadcn-vue@latest add separator --yes
npx shadcn-vue@latest add sheet --yes
npx shadcn-vue@latest add avatar --yes
```

Expected: `frontend/src/components/ui/` populated with `.vue` files for each component.

- [ ] **Step 3: Verify build still passes**

```bash
cd frontend && npm run build
```

Expected: build succeeds with no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/utils.js frontend/src/components/ui/
git commit -m "feat: add shadcn-vue components and cn() helper"
```

---

## Task 3: API Composable

**Files:**
- Create: `frontend/src/lib/api.js`

- [ ] **Step 1: Create `frontend/src/lib/api.js`**

Token is read from localStorage directly to avoid circular dependency with the auth Pinia store. The auth store mirrors the same localStorage key.

```javascript
const API_BASE = '/api'
const TOKEN_KEY = 'helledger_token'

async function _request(method, path, body, retry = true) {
  const token = localStorage.getItem(TOKEN_KEY)
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    credentials: 'include',
    body: body != null ? JSON.stringify(body) : undefined,
  })

  if (res.status === 401 && retry) {
    const ok = await _tryRefresh()
    if (ok) return _request(method, path, body, false)
  }
  return res
}

async function _tryRefresh() {
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    })
    if (!res.ok) return false
    const { access_token } = await res.json()
    localStorage.setItem(TOKEN_KEY, access_token)
    return true
  } catch {
    return false
  }
}

export function useApi() {
  return {
    get: (path) => _request('GET', path, null),
    post: (path, body) => _request('POST', path, body),
    patch: (path, body) => _request('PATCH', path, body),
    delete: (path) => _request('DELETE', path, null),
    upload: (path, formData) => {
      const token = localStorage.getItem(TOKEN_KEY)
      const headers = {}
      if (token) headers['Authorization'] = `Bearer ${token}`
      return fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: formData,
      })
    },
  }
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/api.js
git commit -m "feat: add api composable with localStorage token"
```

---

## Task 4: Pinia Stores (auth + theme)

**Files:**
- Create: `frontend/src/stores/auth.js`
- Create: `frontend/src/stores/theme.js`

- [ ] **Step 1: Create `frontend/src/stores/auth.js`**

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const TOKEN_KEY = 'helledger_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY))
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setToken(newToken) {
    token.value = newToken
    newToken
      ? localStorage.setItem(TOKEN_KEY, newToken)
      : localStorage.removeItem(TOKEN_KEY)
  }

  async function login(email, password) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw err
    }
    const { access_token } = await res.json()
    setToken(access_token)
    await fetchUser()
  }

  async function register(name, email, password) {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ name, email, password }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw err
    }
    const { access_token } = await res.json()
    setToken(access_token)
    await fetchUser()
  }

  async function fetchUser() {
    const t = localStorage.getItem(TOKEN_KEY)
    if (!t) return
    const res = await fetch('/api/auth/me', {
      headers: { Authorization: `Bearer ${t}` },
      credentials: 'include',
    })
    if (res.ok) user.value = await res.json()
    else setToken(null)
  }

  function logout() {
    setToken(null)
    user.value = null
  }

  return { token, user, isAuthenticated, isAdmin, setToken, login, register, fetchUser, logout }
})
```

- [ ] **Step 2: Create `frontend/src/stores/theme.js`**

```javascript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const stored = localStorage.getItem('helledger-theme')
  const isDark = ref(
    stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches
  )

  function toggle() {
    isDark.value = !isDark.value
    document.documentElement.classList.toggle('dark', isDark.value)
    localStorage.setItem('helledger-theme', isDark.value ? 'dark' : 'light')
  }

  function init() {
    document.documentElement.classList.toggle('dark', isDark.value)
  }

  return { isDark, toggle, init }
})
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/stores/
git commit -m "feat: add pinia auth and theme stores"
```

---

## Task 5: i18n Setup

**Files:**
- Create: `frontend/src/locales/de.json`
- Create: `frontend/src/locales/en.json`

The locale files are copied from `frontend/locales/` with one addition: `nav.import` is missing from both files.

- [ ] **Step 1: Create `frontend/src/locales/de.json`**

Copy content from `frontend/locales/de.json` verbatim, then add `"import": "Import"` inside the `"nav"` object:

```json
{
  "app": { "name": "HELLEDGER", "tagline": "Dein persönlicher Finanz-Tracker" },
  "nav": {
    "dashboard": "Dashboard",
    "accounts": "Konten",
    "categories": "Kategorien",
    "transactions": "Transaktionen",
    "reports": "Berichte",
    "import": "Import",
    "settings": "Einstellungen",
    "backup": "Backups",
    "logout": "Abmelden"
  },
  "auth": {
    "login": "Anmelden", "register": "Registrieren",
    "email": "E-Mail-Adresse", "password": "Passwort",
    "name": "Name", "noAccount": "Noch kein Konto?",
    "hasAccount": "Bereits ein Konto?",
    "loginTitle": "Willkommen zurück",
    "registerTitle": "Konto erstellen",
    "passwordHint": "Mindestens 12 Zeichen",
    "switchToRegister": "Registrieren",
    "switchToLogin": "Anmelden"
  },
  "errors": {
    "email_taken": "Diese E-Mail-Adresse ist bereits vergeben.",
    "invalid_credentials": "E-Mail oder Passwort falsch.",
    "registration_disabled": "Registrierung ist deaktiviert.",
    "generic": "Ein Fehler ist aufgetreten. Bitte versuche es erneut."
  },
  "dashboard": {
    "welcome": "Willkommen, {name}!",
    "empty": "Dein Dashboard ist noch leer.",
    "income": "Einnahmen",
    "expenses": "Ausgaben",
    "balance": "Bilanz",
    "sollIst": "Soll / Ist",
    "accounts": "Kontenübersicht",
    "noData": "Keine Daten für diesen Monat.",
    "addTransaction": "Transaktion hinzufügen",
    "soll": "Soll",
    "ist": "Ist",
    "diff": "Differenz"
  },
  "transactions": {
    "title": "Transaktionen",
    "add": "Transaktion hinzufügen",
    "addTransfer": "Umbuchung",
    "date": "Datum",
    "description": "Beschreibung",
    "account": "Konto",
    "category": "Kategorie",
    "amount": "Betrag",
    "type": "Typ",
    "income": "Einnahme",
    "expense": "Ausgabe",
    "transfer": "Umbuchung",
    "fromAccount": "Von Konto",
    "toAccount": "Zu Konto",
    "save": "Speichern",
    "cancel": "Abbrechen",
    "edit": "Bearbeiten",
    "delete": "Löschen",
    "confirmDelete": "Transaktion wirklich löschen?",
    "noData": "Keine Transaktionen gefunden.",
    "filterAccount": "Konto (alle)",
    "filterCategory": "Kategorie (alle)"
  },
  "accounts": {
    "title": "Konten", "add": "Konto hinzufügen",
    "name": "Name", "type": "Typ", "balance": "Startguthaben",
    "currency": "Währung", "status": "Status",
    "active": "Aktiv", "archived": "Archiviert",
    "archive": "Archivieren", "edit": "Bearbeiten",
    "save": "Speichern", "cancel": "Abbrechen",
    "types": { "checking": "Girokonto", "savings": "Sparkonto", "credit": "Kreditkonto" }
  },
  "categories": {
    "title": "Kategorien", "add": "Kategorie hinzufügen", "addSub": "Sub-Kategorie",
    "name": "Name", "type": "Typ", "color": "Farbe",
    "archive": "Archivieren", "edit": "Bearbeiten",
    "save": "Speichern", "cancel": "Abbrechen",
    "expectedValue": "Sollwert", "budget": "Budget",
    "newExpectedValue": "Neuen Sollwert setzen", "newBudget": "Neues Budget setzen",
    "amount": "Betrag", "validFrom": "Gültig ab", "noLimit": "Unbegrenzt",
    "sections": { "income": "Einnahmen", "fixed": "Fixkosten", "variable": "Variable Ausgaben" },
    "types": { "income": "Einnahme", "fixed": "Fixkosten", "variable": "Variable" }
  },
  "settings": {
    "title": "Einstellungen", "household": "Haushalt",
    "householdName": "Haushaltsname", "members": "Mitglieder",
    "addMember": "Mitglied hinzufügen", "memberEmail": "E-Mail-Adresse",
    "add": "Hinzufügen", "remove": "Entfernen",
    "roles": { "owner": "Eigentümer", "member": "Mitglied" },
    "save": "Speichern"
  },
  "lang": { "de": "Deutsch", "en": "English" },
  "import": {
    "title": "Transaktionen importieren",
    "step": { "upload": "Datei auswählen", "mapping": "Spalten zuordnen", "result": "Ergebnis" },
    "dropzone": "CSV, OFX oder QFX hier ablegen oder klicken",
    "account": "Konto",
    "field": {
      "date": "Datum",
      "amount": "Betrag",
      "description": "Beschreibung",
      "category": "Standard-Kategorie (optional)",
      "dateFormat": "Datumsformat",
      "decimal": "Dezimaltrennzeichen"
    },
    "decimal": { "comma": "Komma (,)", "dot": "Punkt (.)" },
    "result": {
      "imported": "Transaktionen importiert",
      "duplicates": "Duplikate gefunden",
      "errors": "Fehler"
    },
    "btn": {
      "import": "Importieren",
      "restart": "Neuen Import starten",
      "toTransactions": "Zu Transaktionen"
    },
    "warn": {
      "duplicates": "Einige Transaktionen wurden bereits importiert.",
      "sessionExpired": "Sitzung abgelaufen – bitte Datei erneut hochladen."
    },
    "error": { "parseError": "Datei konnte nicht gelesen werden." },
    "noHousehold": "Kein aktiver Haushalt. Bitte zuerst in den Einstellungen einen Haushalt auswählen."
  },
  "reports": {
    "title": "Berichte",
    "period": { "month": "Monat", "year": "Jahr", "custom": "Frei" },
    "filter": { "allAccounts": "Alle Konten" },
    "chart": {
      "expensesByCategory": "Ausgaben nach Kategorie",
      "monthlyTrend": "Einnahmen & Ausgaben",
      "balanceHistory": "Kontostand-Verlauf",
      "sollIst": "Soll/Ist-Vergleich"
    },
    "export": { "png": "PNG", "csv": "CSV", "all": "Alle Charts (PNG)" },
    "noData": "Keine Daten für diesen Zeitraum",
    "selectAccount": "Bitte ein Konto auswählen"
  },
  "backup": {
    "title": "Backups",
    "settings": "Einstellungen",
    "retentionDays": "Aufbewahrung (Tage)",
    "save": "Speichern",
    "saved": "Einstellungen gespeichert",
    "triggerBtn": "Backup jetzt erstellen",
    "triggerSuccess": "Backup erstellt",
    "list": "Vorhandene Backups",
    "filename": "Dateiname",
    "size": "Größe",
    "createdAt": "Datum",
    "download": "Herunterladen",
    "delete": "Löschen",
    "deleteConfirm": "Backup wirklich löschen?",
    "empty": "Keine Backups vorhanden"
  }
}
```

- [ ] **Step 2: Create `frontend/src/locales/en.json`**

Same structure as de.json but English, copied from `frontend/locales/en.json` with `"import": "Import"` added to nav:

```json
{
  "app": { "name": "HELLEDGER", "tagline": "Your personal finance tracker" },
  "nav": {
    "dashboard": "Dashboard",
    "accounts": "Accounts",
    "categories": "Categories",
    "transactions": "Transactions",
    "reports": "Reports",
    "import": "Import",
    "settings": "Settings",
    "backup": "Backups",
    "logout": "Sign Out"
  },
  "auth": {
    "login": "Sign In", "register": "Create Account",
    "email": "Email address", "password": "Password",
    "name": "Full name", "noAccount": "Don't have an account?",
    "hasAccount": "Already have an account?",
    "loginTitle": "Welcome back",
    "registerTitle": "Create your account",
    "passwordHint": "At least 12 characters",
    "switchToRegister": "Create account",
    "switchToLogin": "Sign in"
  },
  "errors": {
    "email_taken": "This email address is already taken.",
    "invalid_credentials": "Invalid email or password.",
    "registration_disabled": "Registration is currently disabled.",
    "generic": "Something went wrong. Please try again."
  },
  "dashboard": {
    "welcome": "Welcome, {name}!",
    "empty": "Your dashboard is empty.",
    "income": "Income",
    "expenses": "Expenses",
    "balance": "Balance",
    "sollIst": "Budget vs. Actual",
    "accounts": "Account Balances",
    "noData": "No data for this month.",
    "addTransaction": "Add Transaction",
    "soll": "Budget",
    "ist": "Actual",
    "diff": "Difference"
  },
  "transactions": {
    "title": "Transactions",
    "add": "Add Transaction",
    "addTransfer": "Transfer",
    "date": "Date",
    "description": "Description",
    "account": "Account",
    "category": "Category",
    "amount": "Amount",
    "type": "Type",
    "income": "Income",
    "expense": "Expense",
    "transfer": "Transfer",
    "fromAccount": "From Account",
    "toAccount": "To Account",
    "save": "Save",
    "cancel": "Cancel",
    "edit": "Edit",
    "delete": "Delete",
    "confirmDelete": "Delete this transaction?",
    "noData": "No transactions found.",
    "filterAccount": "Account (all)",
    "filterCategory": "Category (all)"
  },
  "accounts": {
    "title": "Accounts", "add": "Add Account",
    "name": "Name", "type": "Type", "balance": "Initial Balance",
    "currency": "Currency", "status": "Status",
    "active": "Active", "archived": "Archived",
    "archive": "Archive", "edit": "Edit",
    "save": "Save", "cancel": "Cancel",
    "types": { "checking": "Checking", "savings": "Savings", "credit": "Credit" }
  },
  "categories": {
    "title": "Categories", "add": "Add Category", "addSub": "Sub-Category",
    "name": "Name", "type": "Type", "color": "Color",
    "archive": "Archive", "edit": "Edit",
    "save": "Save", "cancel": "Cancel",
    "expectedValue": "Expected Value", "budget": "Budget",
    "newExpectedValue": "Set New Expected Value", "newBudget": "Set New Budget",
    "amount": "Amount", "validFrom": "Valid From", "noLimit": "No Limit",
    "sections": { "income": "Income", "fixed": "Fixed Costs", "variable": "Variable Expenses" },
    "types": { "income": "Income", "fixed": "Fixed", "variable": "Variable" }
  },
  "settings": {
    "title": "Settings", "household": "Household",
    "householdName": "Household Name", "members": "Members",
    "addMember": "Add Member", "memberEmail": "Email address",
    "add": "Add", "remove": "Remove",
    "roles": { "owner": "Owner", "member": "Member" },
    "save": "Save"
  },
  "lang": { "de": "Deutsch", "en": "English" },
  "import": {
    "title": "Import Transactions",
    "step": { "upload": "Select File", "mapping": "Map Columns", "result": "Result" },
    "dropzone": "Drop CSV, OFX or QFX here or click to browse",
    "account": "Account",
    "field": {
      "date": "Date",
      "amount": "Amount",
      "description": "Description",
      "category": "Default Category (optional)",
      "dateFormat": "Date Format",
      "decimal": "Decimal Separator"
    },
    "decimal": { "comma": "Comma (,)", "dot": "Dot (.)" },
    "result": {
      "imported": "transactions imported",
      "duplicates": "duplicates found",
      "errors": "errors"
    },
    "btn": {
      "import": "Import",
      "restart": "Start New Import",
      "toTransactions": "Go to Transactions"
    },
    "warn": {
      "duplicates": "Some transactions were already imported.",
      "sessionExpired": "Session expired — please re-upload the file."
    },
    "error": { "parseError": "Could not read the file." },
    "noHousehold": "No active household. Please select one in Settings first."
  },
  "reports": {
    "title": "Reports",
    "period": { "month": "Month", "year": "Year", "custom": "Custom" },
    "filter": { "allAccounts": "All Accounts" },
    "chart": {
      "expensesByCategory": "Expenses by Category",
      "monthlyTrend": "Income & Expenses",
      "balanceHistory": "Balance History",
      "sollIst": "Budget vs. Actual"
    },
    "export": { "png": "PNG", "csv": "CSV", "all": "All Charts (PNG)" },
    "noData": "No data for this period",
    "selectAccount": "Please select an account"
  },
  "backup": {
    "title": "Backups",
    "settings": "Settings",
    "retentionDays": "Retention (days)",
    "save": "Save",
    "saved": "Settings saved",
    "triggerBtn": "Create backup now",
    "triggerSuccess": "Backup created",
    "list": "Existing backups",
    "filename": "Filename",
    "size": "Size",
    "createdAt": "Date",
    "download": "Download",
    "delete": "Delete",
    "deleteConfirm": "Really delete this backup?",
    "empty": "No backups yet"
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/locales/
git commit -m "feat: add src/locales with nav.import key"
```

---

## Task 6: Router + App Entry

**Files:**
- Create: `frontend/src/router/index.js`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`

- [ ] **Step 1: Create `frontend/src/router/index.js`**

```javascript
import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', component: () => import('@/views/LoginView.vue'), meta: { guest: true } },
  { path: '/register', component: () => import('@/views/LoginView.vue'), meta: { guest: true } },
  { path: '/dashboard', component: () => import('@/views/DashboardView.vue'), meta: { requiresAuth: true } },
  { path: '/accounts', component: () => import('@/views/AccountsView.vue'), meta: { requiresAuth: true } },
  { path: '/categories', component: () => import('@/views/CategoriesView.vue'), meta: { requiresAuth: true } },
  { path: '/transactions', component: () => import('@/views/TransactionsView.vue'), meta: { requiresAuth: true } },
  { path: '/reports', component: () => import('@/views/ReportsView.vue'), meta: { requiresAuth: true } },
  { path: '/import', component: () => import('@/views/ImportView.vue'), meta: { requiresAuth: true } },
  { path: '/settings', component: () => import('@/views/SettingsView.vue'), meta: { requiresAuth: true } },
  { path: '/backup', component: () => import('@/views/BackupView.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (auth.token && !auth.user) {
    try { await auth.fetchUser() } catch {}
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { path: '/login' }
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { path: '/dashboard' }
  }
  if (to.meta.guest && auth.isAuthenticated) {
    return { path: '/dashboard' }
  }
})

export default router
```

- [ ] **Step 2: Create `frontend/src/main.js`**

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import de from './locales/de.json'
import en from './locales/en.json'

import App from './App.vue'
import router from './router'
import { useThemeStore } from './stores/theme'
import './assets/main.css'

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('helledger-lang') || 'de',
  fallbackLocale: 'en',
  messages: { de, en },
})

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(i18n)

const themeStore = useThemeStore()
themeStore.init()

app.mount('#app')
```

- [ ] **Step 3: Create `frontend/src/App.vue`**

```vue
<script setup>
import { Toaster } from 'vue-sonner'
</script>

<template>
  <RouterView />
  <Toaster rich-colors position="top-right" />
</template>
```

- [ ] **Step 4: Create placeholder views** so the router can import them without error during build

Create each view file with a minimal `<template><div /></template>`. Create files for all 9 views:
- `frontend/src/views/LoginView.vue`
- `frontend/src/views/DashboardView.vue`
- `frontend/src/views/AccountsView.vue`
- `frontend/src/views/CategoriesView.vue`
- `frontend/src/views/TransactionsView.vue`
- `frontend/src/views/ReportsView.vue`
- `frontend/src/views/ImportView.vue`
- `frontend/src/views/SettingsView.vue`
- `frontend/src/views/BackupView.vue`

Each placeholder:
```vue
<template><div /></template>
```

- [ ] **Step 5: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds, `dist/index.html` contains `<div id="app"></div>`.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/router/ frontend/src/main.js frontend/src/App.vue frontend/src/views/
git commit -m "feat: add vue router, app entry, and view placeholders"
```

---

## Task 7: AppNav.vue

**Files:**
- Modify: `frontend/src/components/AppNav.vue` (replace placeholder if exists, or create)

- [ ] **Step 1: Create `frontend/src/components/AppNav.vue`**

```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Sun, Moon, ChevronDown, LogOut, Menu } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useApi } from '@/lib/api'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { Separator } from '@/components/ui/separator'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const theme = useThemeStore()
const api = useApi()

const households = ref([])
const activeHousehold = ref(null)
const mobileOpen = ref(false)

const navItems = computed(() => {
  const items = [
    { key: 'dashboard', path: '/dashboard' },
    { key: 'accounts', path: '/accounts' },
    { key: 'categories', path: '/categories' },
    { key: 'transactions', path: '/transactions' },
    { key: 'reports', path: '/reports' },
    { key: 'import', path: '/import' },
    { key: 'settings', path: '/settings' },
  ]
  if (auth.isAdmin) items.push({ key: 'backup', path: '/backup' })
  return items
})

async function loadHouseholds() {
  const res = await api.get('/households')
  if (res.ok) {
    households.value = await res.json()
    activeHousehold.value =
      households.value.find((h) => h.id === auth.user?.active_household_id) || null
  }
}

async function switchHousehold(id) {
  await api.post(`/households/${id}/activate`, {})
  await auth.fetchUser()
  activeHousehold.value = households.value.find((h) => h.id === id) || null
  router.go(0)
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

onMounted(loadHouseholds)
</script>

<template>
  <header class="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
    <div class="max-w-screen-xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
      <!-- Brand -->
      <RouterLink to="/dashboard" class="font-bold text-lg text-primary shrink-0">
        HELLEDGER
      </RouterLink>

      <!-- Desktop nav -->
      <nav class="hidden md:flex items-center gap-1 flex-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.key"
          :to="item.path"
          class="px-3 py-1.5 rounded-md text-sm transition-colors whitespace-nowrap"
          :class="
            route.path.startsWith(item.path)
              ? 'bg-primary/10 text-primary font-medium'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted'
          "
        >
          {{ t(`nav.${item.key}`) }}
        </RouterLink>
      </nav>

      <!-- Right section -->
      <div class="flex items-center gap-1 shrink-0">
        <!-- Household switcher -->
        <DropdownMenu v-if="auth.user">
          <DropdownMenuTrigger as-child>
            <Button variant="ghost" size="sm" class="gap-1 max-w-40 hidden sm:flex">
              <span class="truncate text-sm">{{ activeHousehold?.name || '...' }}</span>
              <ChevronDown class="h-3 w-3 shrink-0" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" class="w-52">
            <DropdownMenuItem
              v-for="hh in households"
              :key="hh.id"
              @click="switchHousehold(hh.id)"
              :class="hh.id === auth.user?.active_household_id ? 'text-primary' : ''"
            >
              {{ hh.name }}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <!-- User name -->
        <span v-if="auth.user" class="text-sm text-muted-foreground hidden lg:block px-2">
          {{ auth.user.name }}
        </span>

        <!-- Dark/Light toggle -->
        <div class="flex items-center gap-1 px-1">
          <Sun class="h-4 w-4 text-muted-foreground" />
          <Switch :checked="theme.isDark" @update:checked="theme.toggle" />
          <Moon class="h-4 w-4 text-muted-foreground" />
        </div>

        <!-- Logout -->
        <Button variant="ghost" size="icon" @click="handleLogout" class="hidden sm:flex">
          <LogOut class="h-4 w-4" />
        </Button>

        <!-- Mobile hamburger -->
        <Sheet v-model:open="mobileOpen">
          <SheetTrigger as-child>
            <Button variant="ghost" size="icon" class="md:hidden">
              <Menu class="h-4 w-4" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" class="w-64 pt-10">
            <nav class="flex flex-col gap-1">
              <RouterLink
                v-for="item in navItems"
                :key="item.key"
                :to="item.path"
                class="px-3 py-2 rounded-md text-sm transition-colors"
                :class="
                  route.path.startsWith(item.path)
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                "
                @click="mobileOpen = false"
              >
                {{ t(`nav.${item.key}`) }}
              </RouterLink>
            </nav>
            <Separator class="my-4" />
            <div class="px-3 space-y-2">
              <p class="text-sm text-muted-foreground">{{ auth.user?.name }}</p>
              <Button variant="outline" size="sm" class="w-full" @click="handleLogout">
                {{ t('nav.logout') }}
              </Button>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </div>
  </header>
</template>
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/AppNav.vue
git commit -m "feat: add AppNav with household switcher and dark mode toggle"
```

---

## Task 8: LoginView

**Files:**
- Modify: `frontend/src/views/LoginView.vue`

- [ ] **Step 1: Replace `frontend/src/views/LoginView.vue`**

```vue
<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const activeTab = ref(route.path === '/register' ? 'register' : 'login')
const loading = ref(false)

const loginForm = ref({ email: '', password: '' })
const registerForm = ref({ name: '', email: '', password: '' })

async function handleLogin() {
  loading.value = true
  try {
    await auth.login(loginForm.value.email, loginForm.value.password)
    router.push('/dashboard')
  } catch (err) {
    const detail = err?.detail || ''
    const key = detail === 'invalid_credentials' ? 'errors.invalid_credentials'
      : detail === 'registration_disabled' ? 'errors.registration_disabled'
      : 'errors.generic'
    toast.error(t(key))
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  loading.value = true
  try {
    await auth.register(registerForm.value.name, registerForm.value.email, registerForm.value.password)
    router.push('/dashboard')
  } catch (err) {
    const detail = err?.detail || ''
    const key = detail === 'email_taken' ? 'errors.email_taken'
      : detail === 'registration_disabled' ? 'errors.registration_disabled'
      : 'errors.generic'
    toast.error(t(key))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-dvh flex items-center justify-center bg-background px-4">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-primary">HELLEDGER</h1>
        <p class="text-sm text-muted-foreground mt-1">{{ t('app.tagline') }}</p>
      </div>

      <Tabs v-model="activeTab">
        <TabsList class="w-full">
          <TabsTrigger value="login" class="flex-1">{{ t('auth.login') }}</TabsTrigger>
          <TabsTrigger value="register" class="flex-1">{{ t('auth.register') }}</TabsTrigger>
        </TabsList>

        <TabsContent value="login">
          <Card>
            <CardHeader>
              <CardTitle>{{ t('auth.loginTitle') }}</CardTitle>
            </CardHeader>
            <CardContent>
              <form @submit.prevent="handleLogin" class="space-y-4">
                <div class="space-y-1">
                  <Label>{{ t('auth.email') }}</Label>
                  <Input
                    v-model="loginForm.email"
                    type="email"
                    required
                    autocomplete="email"
                  />
                </div>
                <div class="space-y-1">
                  <Label>{{ t('auth.password') }}</Label>
                  <Input
                    v-model="loginForm.password"
                    type="password"
                    required
                    autocomplete="current-password"
                  />
                </div>
                <Button type="submit" class="w-full" :disabled="loading">
                  {{ t('auth.login') }}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="register">
          <Card>
            <CardHeader>
              <CardTitle>{{ t('auth.registerTitle') }}</CardTitle>
            </CardHeader>
            <CardContent>
              <form @submit.prevent="handleRegister" class="space-y-4">
                <div class="space-y-1">
                  <Label>{{ t('auth.name') }}</Label>
                  <Input
                    v-model="registerForm.name"
                    type="text"
                    required
                    autocomplete="name"
                  />
                </div>
                <div class="space-y-1">
                  <Label>{{ t('auth.email') }}</Label>
                  <Input
                    v-model="registerForm.email"
                    type="email"
                    required
                    autocomplete="email"
                  />
                </div>
                <div class="space-y-1">
                  <Label>{{ t('auth.password') }}</Label>
                  <Input
                    v-model="registerForm.password"
                    type="password"
                    required
                    autocomplete="new-password"
                    :placeholder="t('auth.passwordHint')"
                  />
                </div>
                <Button type="submit" class="w-full" :disabled="loading">
                  {{ t('auth.register') }}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/LoginView.vue
git commit -m "feat: add LoginView with tabs and auth"
```

---

## Task 9: DashboardView

**Files:**
- Modify: `frontend/src/views/DashboardView.vue`

API calls:
- `GET /transactions/summary?year=&month=` → `{ income, expenses, balance }`
- `GET /categories/soll-ist?year=&month=` → hierarchical list `[{ name, ist, soll, category_type, children }]`
- `GET /accounts/balances` → `[{ id, name, balance }]`

- [ ] **Step 1: Replace `frontend/src/views/DashboardView.vue`**

```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'
import AppNav from '@/components/AppNav.vue'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useRouter } from 'vue-router'

ChartJS.register(ArcElement, Tooltip, Legend)

const CHART_COLORS = ['#6366f1','#10b981','#f59e0b','#3b82f6','#ec4899','#8b5cf6','#14b8a6','#f97316']

const { t, locale } = useI18n()
const router = useRouter()
const api = useApi()

const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const summary = ref({ income: 0, expenses: 0, balance: 0 })
const sollIst = ref([])
const balances = ref([])

const monthLabel = computed(() =>
  new Date(year.value, month.value - 1, 1).toLocaleDateString(
    locale.value === 'de' ? 'de-DE' : 'en-US',
    { month: 'long', year: 'numeric' }
  )
)

const donutData = computed(() => {
  const expenseNodes = []
  function walk(nodes) {
    for (const n of nodes) {
      if (n.category_type !== 'income' && Math.abs(parseFloat(n.ist)) > 0) {
        expenseNodes.push({ name: n.name, value: Math.abs(parseFloat(n.ist)) })
      }
      if (n.children) walk(n.children)
    }
  }
  walk(sollIst.value)
  return expenseNodes
})

const donutChartData = computed(() => ({
  labels: donutData.value.map((d) => d.name),
  datasets: [{
    data: donutData.value.map((d) => d.value),
    backgroundColor: donutData.value.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]),
    borderWidth: 0,
    hoverOffset: 8,
  }],
}))

const donutOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: { position: 'right', labels: { boxWidth: 12, padding: 12, font: { size: 12 } } },
    tooltip: {
      callbacks: {
        label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toFixed(2)} €`,
      },
    },
  },
}

async function load() {
  const [sumRes, siRes, balRes] = await Promise.all([
    api.get(`/transactions/summary?year=${year.value}&month=${month.value}`),
    api.get(`/categories/soll-ist?year=${year.value}&month=${month.value}`),
    api.get('/accounts/balances'),
  ])
  if (!sumRes.ok || !siRes.ok || !balRes.ok) {
    toast.error(t('errors.generic'))
    return
  }
  summary.value = await sumRes.json()
  sollIst.value = await siRes.json()
  balances.value = await balRes.json()
}

function prevMonth() {
  month.value--
  if (month.value < 1) { month.value = 12; year.value-- }
  load()
}

function nextMonth() {
  month.value++
  if (month.value > 12) { month.value = 1; year.value++ }
  load()
}

function fmt(val) {
  return parseFloat(val).toFixed(2).replace('.', ',') + ' €'
}

onMounted(load)
</script>

<template>
  <div class="min-h-dvh bg-background">
    <AppNav />
    <main class="max-w-screen-xl mx-auto px-4 py-6 space-y-6">

      <!-- Month nav -->
      <div class="flex items-center justify-between flex-wrap gap-3">
        <div class="flex items-center gap-3">
          <Button variant="outline" size="sm" @click="prevMonth">←</Button>
          <span class="text-lg font-semibold min-w-44 text-center">{{ monthLabel }}</span>
          <Button variant="outline" size="sm" @click="nextMonth">→</Button>
        </div>
        <Button @click="router.push('/transactions')">{{ t('dashboard.addTransaction') }}</Button>
      </div>

      <!-- Summary cards -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardHeader class="pb-1">
            <CardTitle class="text-xs uppercase tracking-wider text-muted-foreground font-medium">
              {{ t('dashboard.income') }}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-2xl font-bold text-emerald-500 tabular-nums">{{ fmt(summary.income) }}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader class="pb-1">
            <CardTitle class="text-xs uppercase tracking-wider text-muted-foreground font-medium">
              {{ t('dashboard.expenses') }}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-2xl font-bold text-rose-500 tabular-nums">{{ fmt(summary.expenses) }}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader class="pb-1">
            <CardTitle class="text-xs uppercase tracking-wider text-muted-foreground font-medium">
              {{ t('dashboard.balance') }}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-2xl font-bold tabular-nums"
               :class="parseFloat(summary.balance) >= 0 ? 'text-primary' : 'text-rose-500'">
              {{ fmt(summary.balance) }}
            </p>
          </CardContent>
        </Card>
      </div>

      <!-- Soll/Ist + Donut -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Soll/Ist progress bars -->
        <Card>
          <CardHeader class="pb-2">
            <CardTitle class="text-sm uppercase tracking-wider text-muted-foreground">
              {{ t('dashboard.sollIst') }}
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-0 p-0">
            <template v-if="sollIst.length === 0">
              <p class="text-sm text-muted-foreground text-center py-8">{{ t('dashboard.noData') }}</p>
            </template>
            <template v-else>
              <SollIstRow v-for="node in sollIst" :key="node.id" :node="node" :depth="0" />
            </template>
          </CardContent>
        </Card>

        <!-- Donut chart -->
        <Card>
          <CardHeader class="pb-2">
            <CardTitle class="text-sm uppercase tracking-wider text-muted-foreground">
              {{ t('reports.chart.expensesByCategory') }}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Doughnut
              v-if="donutData.length > 0"
              :data="donutChartData"
              :options="donutOptions"
              class="max-h-64"
            />
            <p v-else class="text-sm text-muted-foreground text-center py-8">
              {{ t('dashboard.noData') }}
            </p>
          </CardContent>
        </Card>
      </div>

      <!-- Account balances -->
      <div>
        <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {{ t('dashboard.accounts') }}
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <Card v-for="acc in balances" :key="acc.id" class="flex-row items-center">
            <CardContent class="flex items-center justify-between p-4 w-full">
              <span class="text-sm text-muted-foreground">{{ acc.name }}</span>
              <span class="text-sm font-semibold tabular-nums"
                    :class="parseFloat(acc.balance) >= 0 ? 'text-emerald-500' : 'text-rose-500'">
                {{ parseFloat(acc.balance) >= 0 ? '+' : '' }}{{ parseFloat(acc.balance).toFixed(2).replace('.', ',') }} €
              </span>
            </CardContent>
          </Card>
        </div>
      </div>

    </main>
  </div>
</template>

<script>
// Recursive sub-component for Soll/Ist rows
const SollIstRow = {
  name: 'SollIstRow',
  props: { node: Object, depth: Number },
  setup(props) {
    const pct = parseFloat(props.node.soll) > 0
      ? Math.min(100, Math.abs(parseFloat(props.node.ist) / parseFloat(props.node.soll) * 100))
      : 0
    const over = pct >= 100
    return { pct, over }
  },
  template: `
    <div>
      <div class="px-4 py-3 border-b border-border last:border-0"
           :style="{ paddingLeft: (depth * 16 + 16) + 'px' }">
        <div class="flex justify-between items-center mb-1">
          <span class="text-sm">{{ node.name }}</span>
          <div class="flex gap-4 text-xs tabular-nums">
            <span :class="over ? 'text-rose-500' : 'text-foreground'">
              {{ parseFloat(node.ist).toFixed(2).replace('.', ',') }} €
            </span>
            <span class="text-muted-foreground">/ {{ parseFloat(node.soll).toFixed(2).replace('.', ',') }} €</span>
          </div>
        </div>
        <div class="h-1 rounded-full bg-muted overflow-hidden">
          <div class="h-full rounded-full transition-all"
               :style="{ width: pct + '%' }"
               :class="over ? 'bg-rose-500' : 'bg-primary'" />
        </div>
      </div>
      <SollIstRow v-for="child in node.children" :key="child.id" :node="child" :depth="depth + 1" />
    </div>
  `,
  components: { SollIstRow: null },
}
SollIstRow.components.SollIstRow = SollIstRow
</script>
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/DashboardView.vue
git commit -m "feat: add DashboardView with summary cards, soll-ist, and donut chart"
```

---

## Task 10: AccountsView

**Files:**
- Modify: `frontend/src/views/AccountsView.vue`

API: `GET /accounts` → `[{ id, name, type, balance, currency, status }]`; `POST /accounts`, `PATCH /accounts/{id}`, `DELETE /accounts/{id}`.

- [ ] **Step 1: Replace `frontend/src/views/AccountsView.vue`**

```vue
<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import AppNav from '@/components/AppNav.vue'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const { t } = useI18n()
const api = useApi()

const accounts = ref([])
const showDialog = ref(false)
const editingId = ref(null)
const form = ref({ name: '', type: 'checking', balance: '0', currency: 'EUR' })

async function load() {
  const res = await api.get('/accounts')
  if (res.ok) accounts.value = await res.json()
}

function openCreate() {
  editingId.value = null
  form.value = { name: '', type: 'checking', balance: '0', currency: 'EUR' }
  showDialog.value = true
}

function openEdit(acc) {
  editingId.value = acc.id
  form.value = { name: acc.name, type: acc.type, balance: String(acc.balance), currency: acc.currency }
  showDialog.value = true
}

async function save() {
  const body = {
    name: form.value.name,
    type: form.value.type,
    balance: parseFloat(form.value.balance),
    currency: form.value.currency,
  }
  const res = editingId.value
    ? await api.patch(`/accounts/${editingId.value}`, body)
    : await api.post('/accounts', body)
  if (res.ok) {
    showDialog.value = false
    await load()
    toast.success(t('accounts.save'))
  } else {
    toast.error(t('errors.generic'))
  }
}

async function archive(id) {
  if (!confirm(t('accounts.archive') + '?')) return
  const res = await api.delete(`/accounts/${id}`)
  if (res.ok) { await load(); toast.success(t('accounts.archive')) }
  else toast.error(t('errors.generic'))
}

onMounted(load)
</script>

<template>
  <div class="min-h-dvh bg-background">
    <AppNav />
    <main class="max-w-5xl mx-auto px-4 py-6">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">{{ t('accounts.title') }}</h1>
        <Button @click="openCreate">{{ t('accounts.add') }}</Button>
      </div>

      <div class="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{{ t('accounts.name') }}</TableHead>
              <TableHead>{{ t('accounts.type') }}</TableHead>
              <TableHead class="text-right">{{ t('accounts.balance') }}</TableHead>
              <TableHead>{{ t('accounts.currency') }}</TableHead>
              <TableHead>{{ t('accounts.status') }}</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="acc in accounts" :key="acc.id">
              <TableCell class="font-medium">{{ acc.name }}</TableCell>
              <TableCell>{{ t(`accounts.types.${acc.type}`) }}</TableCell>
              <TableCell class="text-right tabular-nums"
                :class="acc.balance >= 0 ? 'text-emerald-500' : 'text-rose-500'">
                {{ parseFloat(acc.balance).toFixed(2) }}
              </TableCell>
              <TableCell>{{ acc.currency }}</TableCell>
              <TableCell>
                <Badge :variant="acc.status === 'active' ? 'default' : 'secondary'">
                  {{ t(`accounts.${acc.status}`) }}
                </Badge>
              </TableCell>
              <TableCell class="text-right space-x-1">
                <Button variant="ghost" size="sm" @click="openEdit(acc)">{{ t('accounts.edit') }}</Button>
                <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="archive(acc.id)">
                  {{ t('accounts.archive') }}
                </Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </main>

    <Dialog v-model:open="showDialog">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ editingId ? t('accounts.edit') : t('accounts.add') }}</DialogTitle>
        </DialogHeader>
        <form @submit.prevent="save" class="space-y-4">
          <div class="space-y-1">
            <Label>{{ t('accounts.name') }}</Label>
            <Input v-model="form.name" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('accounts.type') }}</Label>
            <Select v-model="form.type">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="checking">{{ t('accounts.types.checking') }}</SelectItem>
                <SelectItem value="savings">{{ t('accounts.types.savings') }}</SelectItem>
                <SelectItem value="credit">{{ t('accounts.types.credit') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-1">
            <Label>{{ t('accounts.balance') }}</Label>
            <Input v-model="form.balance" type="number" step="0.01" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('accounts.currency') }}</Label>
            <Input v-model="form.currency" required maxlength="3" />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" @click="showDialog = false">{{ t('accounts.cancel') }}</Button>
            <Button type="submit">{{ t('accounts.save') }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/AccountsView.vue
git commit -m "feat: add AccountsView with table and create/edit dialog"
```

---

## Task 11: CategoriesView

**Files:**
- Modify: `frontend/src/views/CategoriesView.vue`

API: `GET /categories` → hierarchical `[{ id, name, type, color, parent_id, children }]`; `POST /categories`, `PATCH /categories/{id}`.

- [ ] **Step 1: Replace `frontend/src/views/CategoriesView.vue`**

```vue
<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import AppNav from '@/components/AppNav.vue'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const { t } = useI18n()
const api = useApi()

const categories = ref([])
const showDialog = ref(false)
const editingId = ref(null)
const form = ref({ name: '', type: 'expense', color: '#6366f1', parent_id: null })

const TYPE_COLORS = { income: 'default', fixed: 'secondary', variable: 'outline' }

async function load() {
  const res = await api.get('/categories')
  if (res.ok) categories.value = await res.json()
}

function openCreate(parentId = null, defaultType = 'expense') {
  editingId.value = null
  form.value = { name: '', type: defaultType, color: '#6366f1', parent_id: parentId }
  showDialog.value = true
}

function openEdit(cat) {
  editingId.value = cat.id
  form.value = { name: cat.name, type: cat.type, color: cat.color || '#6366f1', parent_id: cat.parent_id }
  showDialog.value = true
}

async function save() {
  const body = { name: form.value.name, type: form.value.type, color: form.value.color }
  if (form.value.parent_id) body.parent_id = form.value.parent_id
  const res = editingId.value
    ? await api.patch(`/categories/${editingId.value}`, body)
    : await api.post('/categories', body)
  if (res.ok) {
    showDialog.value = false
    await load()
    toast.success(t('categories.save'))
  } else {
    toast.error(t('errors.generic'))
  }
}

async function archive(id) {
  if (!confirm(t('categories.archive') + '?')) return
  const res = await api.delete(`/categories/${id}`)
  if (res.ok) { await load(); toast.success(t('categories.archive')) }
  else toast.error(t('errors.generic'))
}

onMounted(load)
</script>

<template>
  <div class="min-h-dvh bg-background">
    <AppNav />
    <main class="max-w-4xl mx-auto px-4 py-6">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">{{ t('categories.title') }}</h1>
        <Button @click="openCreate(null, 'expense')">{{ t('categories.add') }}</Button>
      </div>

      <div v-for="section in ['income', 'fixed', 'variable']" :key="section" class="mb-8">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {{ t(`categories.sections.${section}`) }}
        </h2>
        <div class="rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{{ t('categories.name') }}</TableHead>
                <TableHead>{{ t('categories.type') }}</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              <template v-for="cat in categories.filter(c => c.type === section && !c.parent_id)" :key="cat.id">
                <TableRow>
                  <TableCell class="font-medium">
                    <div class="flex items-center gap-2">
                      <span
                        class="w-3 h-3 rounded-full shrink-0"
                        :style="{ background: cat.color || '#6366f1' }"
                      />
                      {{ cat.name }}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge :variant="TYPE_COLORS[cat.type]">{{ t(`categories.types.${cat.type}`) }}</Badge>
                  </TableCell>
                  <TableCell class="text-right space-x-1">
                    <Button variant="ghost" size="sm" @click="openCreate(cat.id, cat.type)">
                      {{ t('categories.addSub') }}
                    </Button>
                    <Button variant="ghost" size="sm" @click="openEdit(cat)">{{ t('categories.edit') }}</Button>
                    <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="archive(cat.id)">
                      {{ t('categories.archive') }}
                    </Button>
                  </TableCell>
                </TableRow>
                <!-- Children -->
                <TableRow v-for="child in (cat.children || [])" :key="child.id" class="bg-muted/30">
                  <TableCell class="pl-10">
                    <div class="flex items-center gap-2">
                      <span class="w-3 h-3 rounded-full shrink-0" :style="{ background: child.color || '#6366f1' }" />
                      {{ child.name }}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge :variant="TYPE_COLORS[child.type]">{{ t(`categories.types.${child.type}`) }}</Badge>
                  </TableCell>
                  <TableCell class="text-right space-x-1">
                    <Button variant="ghost" size="sm" @click="openEdit(child)">{{ t('categories.edit') }}</Button>
                    <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="archive(child.id)">
                      {{ t('categories.archive') }}
                    </Button>
                  </TableCell>
                </TableRow>
              </template>
            </TableBody>
          </Table>
        </div>
      </div>
    </main>

    <Dialog v-model:open="showDialog">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ editingId ? t('categories.edit') : t('categories.add') }}</DialogTitle>
        </DialogHeader>
        <form @submit.prevent="save" class="space-y-4">
          <div class="space-y-1">
            <Label>{{ t('categories.name') }}</Label>
            <Input v-model="form.name" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('categories.type') }}</Label>
            <Select v-model="form.type" :disabled="!!form.parent_id">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="income">{{ t('categories.types.income') }}</SelectItem>
                <SelectItem value="fixed">{{ t('categories.types.fixed') }}</SelectItem>
                <SelectItem value="variable">{{ t('categories.types.variable') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-1">
            <Label>{{ t('categories.color') }}</Label>
            <div class="flex gap-2 items-center">
              <input type="color" v-model="form.color" class="h-9 w-12 rounded border bg-card cursor-pointer" />
              <Input v-model="form.color" class="font-mono" />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" @click="showDialog = false">{{ t('categories.cancel') }}</Button>
            <Button type="submit">{{ t('categories.save') }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/CategoriesView.vue
git commit -m "feat: add CategoriesView with hierarchical table"
```

---

## Task 12: TransactionsView

**Files:**
- Modify: `frontend/src/views/TransactionsView.vue`

API:
- `GET /transactions?year=&month=&account_id=&category_id=` → `[{ id, date, description, amount, type, account_id, category_id, from_account_id, to_account_id, account_name, category_name }]`
- `POST /transactions`, `PATCH /transactions/{id}`, `DELETE /transactions/{id}`
- `GET /accounts`, `GET /categories`

- [ ] **Step 1: Replace `frontend/src/views/TransactionsView.vue`**

```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import AppNav from '@/components/AppNav.vue'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const { t, locale } = useI18n()
const api = useApi()

const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const filterAccountId = ref('')
const filterCategoryId = ref('')

const transactions = ref([])
const accounts = ref([])
const categories = ref([])
const flatCategories = ref([])
const showDialog = ref(false)
const editingId = ref(null)
const form = ref({
  type: 'expense',
  date: new Date().toISOString().slice(0, 10),
  description: '',
  amount: '',
  account_id: '',
  category_id: '',
  from_account_id: '',
  to_account_id: '',
})

const monthLabel = computed(() =>
  new Date(year.value, month.value - 1, 1).toLocaleDateString(
    locale.value === 'de' ? 'de-DE' : 'en-US',
    { month: 'long', year: 'numeric' }
  )
)

const TYPE_BADGE = { income: 'default', expense: 'destructive', transfer: 'secondary' }

function flattenCats(list) {
  const result = []
  function walk(items) {
    for (const c of items) {
      result.push(c)
      if (c.children) walk(c.children)
    }
  }
  walk(list)
  return result
}

async function load() {
  const params = new URLSearchParams({ year: year.value, month: month.value })
  if (filterAccountId.value) params.set('account_id', filterAccountId.value)
  if (filterCategoryId.value) params.set('category_id', filterCategoryId.value)
  const res = await api.get(`/transactions?${params}`)
  if (res.ok) transactions.value = await res.json()
}

async function loadMeta() {
  const [accRes, catRes] = await Promise.all([api.get('/accounts'), api.get('/categories')])
  if (accRes.ok) accounts.value = await accRes.json()
  if (catRes.ok) {
    categories.value = await catRes.json()
    flatCategories.value = flattenCats(categories.value)
  }
}

function prevMonth() {
  month.value--
  if (month.value < 1) { month.value = 12; year.value-- }
  load()
}
function nextMonth() {
  month.value++
  if (month.value > 12) { month.value = 1; year.value++ }
  load()
}

function openCreate() {
  editingId.value = null
  form.value = {
    type: 'expense',
    date: new Date().toISOString().slice(0, 10),
    description: '',
    amount: '',
    account_id: accounts.value[0]?.id ? String(accounts.value[0].id) : '',
    category_id: '',
    from_account_id: accounts.value[0]?.id ? String(accounts.value[0].id) : '',
    to_account_id: accounts.value[1]?.id ? String(accounts.value[1].id) : '',
  }
  showDialog.value = true
}

function openEdit(tx) {
  editingId.value = tx.id
  form.value = {
    type: tx.type,
    date: tx.date,
    description: tx.description,
    amount: String(Math.abs(parseFloat(tx.amount))),
    account_id: tx.account_id ? String(tx.account_id) : '',
    category_id: tx.category_id ? String(tx.category_id) : '',
    from_account_id: tx.from_account_id ? String(tx.from_account_id) : '',
    to_account_id: tx.to_account_id ? String(tx.to_account_id) : '',
  }
  showDialog.value = true
}

async function save() {
  let body
  if (form.value.type === 'transfer') {
    body = {
      type: 'transfer',
      date: form.value.date,
      description: form.value.description,
      amount: parseFloat(form.value.amount),
      from_account_id: parseInt(form.value.from_account_id),
      to_account_id: parseInt(form.value.to_account_id),
    }
  } else {
    body = {
      type: form.value.type,
      date: form.value.date,
      description: form.value.description,
      amount: parseFloat(form.value.amount),
      account_id: parseInt(form.value.account_id),
      category_id: form.value.category_id ? parseInt(form.value.category_id) : null,
    }
  }
  const res = editingId.value
    ? await api.patch(`/transactions/${editingId.value}`, body)
    : await api.post('/transactions', body)
  if (res.ok) {
    showDialog.value = false
    await load()
    toast.success(t('transactions.save'))
  } else {
    toast.error(t('errors.generic'))
  }
}

async function remove(id) {
  if (!confirm(t('transactions.confirmDelete'))) return
  const res = await api.delete(`/transactions/${id}`)
  if (res.ok) { await load(); toast.success(t('transactions.delete')) }
  else toast.error(t('errors.generic'))
}

function fmtAmount(tx) {
  const val = parseFloat(tx.amount)
  return (val >= 0 ? '+' : '') + val.toFixed(2).replace('.', ',') + ' €'
}

onMounted(async () => { await loadMeta(); await load() })
</script>

<template>
  <div class="min-h-dvh bg-background">
    <AppNav />
    <main class="max-w-5xl mx-auto px-4 py-6">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div class="flex items-center gap-2">
          <Button variant="outline" size="sm" @click="prevMonth">←</Button>
          <span class="font-semibold min-w-40 text-center">{{ monthLabel }}</span>
          <Button variant="outline" size="sm" @click="nextMonth">→</Button>
        </div>
        <Button @click="openCreate">{{ t('transactions.add') }}</Button>
      </div>

      <!-- Filters -->
      <div class="flex gap-3 mb-4 flex-wrap">
        <Select v-model="filterAccountId" @update:modelValue="load">
          <SelectTrigger class="w-48">
            <SelectValue :placeholder="t('transactions.filterAccount')" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">{{ t('transactions.filterAccount') }}</SelectItem>
            <SelectItem v-for="acc in accounts" :key="acc.id" :value="String(acc.id)">{{ acc.name }}</SelectItem>
          </SelectContent>
        </Select>
        <Select v-model="filterCategoryId" @update:modelValue="load">
          <SelectTrigger class="w-48">
            <SelectValue :placeholder="t('transactions.filterCategory')" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">{{ t('transactions.filterCategory') }}</SelectItem>
            <SelectItem v-for="cat in flatCategories" :key="cat.id" :value="String(cat.id)">{{ cat.name }}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <!-- Table -->
      <div class="rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{{ t('transactions.date') }}</TableHead>
              <TableHead>{{ t('transactions.description') }}</TableHead>
              <TableHead>{{ t('transactions.account') }}</TableHead>
              <TableHead>{{ t('transactions.category') }}</TableHead>
              <TableHead>{{ t('transactions.type') }}</TableHead>
              <TableHead class="text-right">{{ t('transactions.amount') }}</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-if="transactions.length === 0">
              <TableCell colspan="7" class="text-center text-muted-foreground py-8">
                {{ t('transactions.noData') }}
              </TableCell>
            </TableRow>
            <TableRow v-for="tx in transactions" :key="tx.id">
              <TableCell class="tabular-nums text-sm">{{ tx.date }}</TableCell>
              <TableCell class="max-w-48 truncate">{{ tx.description }}</TableCell>
              <TableCell class="text-sm text-muted-foreground">{{ tx.account_name }}</TableCell>
              <TableCell class="text-sm text-muted-foreground">{{ tx.category_name || '—' }}</TableCell>
              <TableCell>
                <Badge :variant="TYPE_BADGE[tx.type]">{{ t(`transactions.${tx.type}`) }}</Badge>
              </TableCell>
              <TableCell class="text-right tabular-nums"
                :class="tx.type === 'income' ? 'text-emerald-500' : tx.type === 'transfer' ? 'text-violet-500' : 'text-rose-500'">
                {{ fmtAmount(tx) }}
              </TableCell>
              <TableCell class="text-right space-x-1">
                <Button variant="ghost" size="sm" @click="openEdit(tx)">{{ t('transactions.edit') }}</Button>
                <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="remove(tx.id)">
                  {{ t('transactions.delete') }}
                </Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </main>

    <!-- Dialog -->
    <Dialog v-model:open="showDialog">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ editingId ? t('transactions.edit') : t('transactions.add') }}</DialogTitle>
        </DialogHeader>
        <form @submit.prevent="save" class="space-y-4">
          <div class="space-y-1">
            <Label>{{ t('transactions.type') }}</Label>
            <Select v-model="form.type">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="income">{{ t('transactions.income') }}</SelectItem>
                <SelectItem value="expense">{{ t('transactions.expense') }}</SelectItem>
                <SelectItem value="transfer">{{ t('transactions.transfer') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-1">
            <Label>{{ t('transactions.date') }}</Label>
            <Input v-model="form.date" type="date" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('transactions.description') }}</Label>
            <Input v-model="form.description" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('transactions.amount') }}</Label>
            <Input v-model="form.amount" type="number" step="0.01" min="0" required />
          </div>
          <!-- Transfer fields -->
          <template v-if="form.type === 'transfer'">
            <div class="space-y-1">
              <Label>{{ t('transactions.fromAccount') }}</Label>
              <Select v-model="form.from_account_id">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="acc in accounts" :key="acc.id" :value="String(acc.id)">{{ acc.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-1">
              <Label>{{ t('transactions.toAccount') }}</Label>
              <Select v-model="form.to_account_id">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="acc in accounts" :key="acc.id" :value="String(acc.id)">{{ acc.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </template>
          <!-- Income/Expense fields -->
          <template v-else>
            <div class="space-y-1">
              <Label>{{ t('transactions.account') }}</Label>
              <Select v-model="form.account_id">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="acc in accounts" :key="acc.id" :value="String(acc.id)">{{ acc.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-1">
              <Label>{{ t('transactions.category') }}</Label>
              <Select v-model="form.category_id">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">—</SelectItem>
                  <SelectItem v-for="cat in flatCategories" :key="cat.id" :value="String(cat.id)">{{ cat.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </template>
          <DialogFooter>
            <Button type="button" variant="outline" @click="showDialog = false">{{ t('transactions.cancel') }}</Button>
            <Button type="submit">{{ t('transactions.save') }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/TransactionsView.vue
git commit -m "feat: add TransactionsView with filters and create/edit dialog"
```

---

## Task 13: ReportsView

**Files:**
- Modify: `frontend/src/views/ReportsView.vue`

API:
- `GET /reports/expenses-by-category?from_date=&to_date=&account_id=` → `[{ category_name, total }]`
- `GET /reports/monthly-trend?from_date=&to_date=` → `[{ year, month, income, expenses }]`
- `GET /reports/soll-ist?from_date=&to_date=` → `[{ id, name, soll, ist, diff, category_type, children }]`
- `GET /reports/balance-history?from_date=&to_date=&account_id=` → `[{ date, balance }]` (requires account_id)

- [ ] **Step 1: Replace `frontend/src/views/ReportsView.vue`**

```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { Doughnut, Bar, Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement, CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import AppNav from '@/components/AppNav.vue'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

ChartJS.register(
  ArcElement, CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
)

const COLORS = ['#6366f1','#10b981','#f59e0b','#3b82f6','#ec4899','#8b5cf6','#14b8a6','#f97316']

const { t, locale } = useI18n()
const api = useApi()

const mode = ref('month')
const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const fromDate = ref('')
const toDate = ref('')
const accountId = ref('')
const accounts = ref([])
const activeTab = ref('expenses')

const catData = ref(null)
const trendData = ref(null)
const sollIstData = ref(null)
const balanceData = ref(null)

function lastDayOf(y, m) {
  return new Date(y, m, 0).getDate()
}

function pad(n) { return String(n).padStart(2, '0') }

const dateRange = computed(() => {
  if (mode.value === 'month') {
    return {
      from: `${year.value}-${pad(month.value)}-01`,
      to: `${year.value}-${pad(month.value)}-${pad(lastDayOf(year.value, month.value))}`,
    }
  }
  if (mode.value === 'year') {
    return { from: `${year.value}-01-01`, to: `${year.value}-12-31` }
  }
  return { from: fromDate.value, to: toDate.value }
})

function buildQs() {
  const p = new URLSearchParams({ from_date: dateRange.value.from, to_date: dateRange.value.to })
  if (accountId.value) p.set('account_id', accountId.value)
  return p.toString()
}

async function loadData() {
  const { from, to } = dateRange.value
  if (!from || !to || from > to) return
  const [catRes, trendRes, siRes] = await Promise.all([
    api.get(`/reports/expenses-by-category?${buildQs()}`),
    api.get(`/reports/monthly-trend?from_date=${from}&to_date=${to}`),
    api.get(`/reports/soll-ist?from_date=${from}&to_date=${to}`),
  ])
  if (catRes.ok) catData.value = await catRes.json()
  if (trendRes.ok) trendData.value = await trendRes.json()
  if (siRes.ok) sollIstData.value = await siRes.json()

  if (accountId.value) {
    const balRes = await api.get(`/reports/balance-history?from_date=${from}&to_date=${to}&account_id=${accountId.value}`)
    if (balRes.ok) balanceData.value = await balRes.json()
  } else {
    balanceData.value = null
  }
}

const donutChartData = computed(() => ({
  labels: (catData.value || []).map((d) => d.category_name),
  datasets: [{
    data: (catData.value || []).map((d) => parseFloat(d.total)),
    backgroundColor: (catData.value || []).map((_, i) => COLORS[i % COLORS.length]),
    borderWidth: 0,
  }],
}))

const trendChartData = computed(() => {
  const data = trendData.value || []
  const lang = locale.value === 'de' ? 'de-DE' : 'en-US'
  return {
    labels: data.map((d) =>
      new Date(d.year, d.month - 1, 1).toLocaleDateString(lang, { month: 'short', year: '2-digit' })
    ),
    datasets: [
      {
        label: t('dashboard.income'),
        data: data.map((d) => parseFloat(d.income)),
        backgroundColor: 'rgba(16,185,129,0.7)',
        borderColor: '#10b981',
        borderWidth: 1,
        borderRadius: 4,
      },
      {
        label: t('dashboard.expenses'),
        data: data.map((d) => parseFloat(d.expenses)),
        backgroundColor: 'rgba(244,63,94,0.7)',
        borderColor: '#f43f5e',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  }
})

const sollIstFlat = computed(() => {
  const flat = []
  function walk(nodes) {
    for (const n of nodes) {
      if (parseFloat(n.soll) !== 0 || parseFloat(n.ist) !== 0) flat.push(n)
      if (n.children) walk(n.children)
    }
  }
  walk(sollIstData.value || [])
  return flat
})

const sollIstChartData = computed(() => ({
  labels: sollIstFlat.value.map((n) => n.name),
  datasets: [
    {
      label: t('dashboard.soll'),
      data: sollIstFlat.value.map((n) => parseFloat(n.soll)),
      backgroundColor: 'rgba(99,102,241,0.6)',
      borderColor: '#6366f1',
      borderWidth: 1,
      borderRadius: 4,
    },
    {
      label: t('dashboard.ist'),
      data: sollIstFlat.value.map((n) => Math.abs(parseFloat(n.ist))),
      backgroundColor: 'rgba(16,185,129,0.6)',
      borderColor: '#10b981',
      borderWidth: 1,
      borderRadius: 4,
    },
  ],
}))

const balanceChartData = computed(() => ({
  labels: (balanceData.value || []).map((d) => d.date),
  datasets: [{
    label: t('reports.chart.balanceHistory'),
    data: (balanceData.value || []).map((d) => parseFloat(d.balance)),
    borderColor: '#6366f1',
    backgroundColor: 'rgba(99,102,241,0.12)',
    fill: true,
    tension: 0.3,
  }],
}))

const barOptions = {
  responsive: true,
  plugins: { legend: { position: 'top' } },
  scales: { x: { grid: { display: false } }, y: { beginAtZero: true } },
}

const hBarOptions = {
  indexAxis: 'y',
  responsive: true,
  plugins: { legend: { position: 'top' } },
  scales: { x: { beginAtZero: true } },
}

function downloadCsv(data, filename) {
  if (!data?.length) return
  const headers = Object.keys(data[0]).join(',')
  const rows = data.map((r) => Object.values(r).map((v) => `"${v}"`).join(',')).join('\n')
  const blob = new Blob([headers + '\n' + rows], { type: 'text/csv' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

const years = Array.from({ length: 4 }, (_, i) => new Date().getFullYear() - 1 + i)

onMounted(async () => {
  const res = await api.get('/accounts')
  if (res.ok) accounts.value = await res.json()
  await loadData()
})
</script>

<template>
  <div class="min-h-dvh bg-background">
    <AppNav />
    <main class="max-w-screen-xl mx-auto px-4 py-6 space-y-6">
      <h1 class="text-2xl font-bold">{{ t('reports.title') }}</h1>

      <!-- Filter bar -->
      <Card>
        <CardContent class="p-4 flex flex-wrap items-center gap-3">
          <!-- Mode tabs -->
          <div class="flex rounded-md border overflow-hidden">
            <button
              v-for="m in ['month', 'year', 'custom']"
              :key="m"
              class="px-4 py-1.5 text-sm transition-colors"
              :class="mode === m ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted'"
              @click="mode = m; loadData()"
            >
              {{ t(`reports.period.${m}`) }}
            </button>
          </div>

          <!-- Month/Year pickers -->
          <template v-if="mode === 'month'">
            <Select v-model.number="month" @update:modelValue="loadData">
              <SelectTrigger class="w-32"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem v-for="m in 12" :key="m" :value="m">
                  {{ new Date(2000, m - 1).toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', { month: 'long' }) }}
                </SelectItem>
              </SelectContent>
            </Select>
          </template>

          <template v-if="mode !== 'custom'">
            <Select v-model.number="year" @update:modelValue="loadData">
              <SelectTrigger class="w-24"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem v-for="y in years" :key="y" :value="y">{{ y }}</SelectItem>
              </SelectContent>
            </Select>
          </template>

          <template v-if="mode === 'custom'">
            <Input v-model="fromDate" type="date" class="w-36" @change="loadData" />
            <span class="text-muted-foreground">→</span>
            <Input v-model="toDate" type="date" class="w-36" @change="loadData" />
          </template>

          <!-- Account filter -->
          <Select v-model="accountId" class="ml-auto" @update:modelValue="loadData">
            <SelectTrigger class="w-44"><SelectValue :placeholder="t('reports.filter.allAccounts')" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="">{{ t('reports.filter.allAccounts') }}</SelectItem>
              <SelectItem v-for="acc in accounts" :key="acc.id" :value="String(acc.id)">{{ acc.name }}</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <!-- Charts -->
      <Tabs v-model="activeTab">
        <TabsList>
          <TabsTrigger value="expenses">{{ t('reports.chart.expensesByCategory') }}</TabsTrigger>
          <TabsTrigger value="trend">{{ t('reports.chart.monthlyTrend') }}</TabsTrigger>
          <TabsTrigger value="balance">{{ t('reports.chart.balanceHistory') }}</TabsTrigger>
          <TabsTrigger value="sollist">{{ t('reports.chart.sollIst') }}</TabsTrigger>
        </TabsList>

        <TabsContent value="expenses">
          <Card>
            <CardHeader class="flex-row items-center justify-between pb-2">
              <CardTitle class="text-sm">{{ t('reports.chart.expensesByCategory') }}</CardTitle>
              <Button variant="outline" size="sm" @click="downloadCsv(catData, 'expenses-by-category.csv')">
                {{ t('reports.export.csv') }}
              </Button>
            </CardHeader>
            <CardContent>
              <Doughnut v-if="catData?.length" :data="donutChartData" :options="{ responsive: true, plugins: { legend: { position: 'right' } } }" class="max-h-80" />
              <p v-else class="text-center text-muted-foreground py-12">{{ t('reports.noData') }}</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trend">
          <Card>
            <CardHeader class="flex-row items-center justify-between pb-2">
              <CardTitle class="text-sm">{{ t('reports.chart.monthlyTrend') }}</CardTitle>
              <Button variant="outline" size="sm" @click="downloadCsv(trendData, 'monthly-trend.csv')">
                {{ t('reports.export.csv') }}
              </Button>
            </CardHeader>
            <CardContent>
              <Bar v-if="trendData?.length" :data="trendChartData" :options="barOptions" class="max-h-80" />
              <p v-else class="text-center text-muted-foreground py-12">{{ t('reports.noData') }}</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="balance">
          <Card>
            <CardHeader class="pb-2">
              <CardTitle class="text-sm">{{ t('reports.chart.balanceHistory') }}</CardTitle>
            </CardHeader>
            <CardContent>
              <Line v-if="balanceData?.length" :data="balanceChartData" :options="{ responsive: true, plugins: { legend: { display: false } } }" class="max-h-80" />
              <p v-else class="text-center text-muted-foreground py-12">
                {{ accountId ? t('reports.noData') : t('reports.selectAccount') }}
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sollist">
          <Card>
            <CardHeader class="flex-row items-center justify-between pb-2">
              <CardTitle class="text-sm">{{ t('reports.chart.sollIst') }}</CardTitle>
              <Button variant="outline" size="sm" @click="downloadCsv(sollIstFlat, 'soll-ist.csv')">
                {{ t('reports.export.csv') }}
              </Button>
            </CardHeader>
            <CardContent>
              <Bar v-if="sollIstFlat.length" :data="sollIstChartData" :options="hBarOptions" class="max-h-80" />
              <p v-else class="text-center text-muted-foreground py-12">{{ t('reports.noData') }}</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </main>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/ReportsView.vue
git commit -m "feat: add ReportsView with 4 chart tabs and CSV export"
```

---

## Task 14: ImportView

**Files:**
- Modify: `frontend/src/views/ImportView.vue`

API:
- `POST /import/upload` (multipart FormData: `file`, `account_id`) → `{ session_id, columns: [...] }`
- `POST /import/{session_id}/preview` (JSON: `{ column_map, date_format, decimal }`) → `{ rows: [...] }`
- `POST /import/{session_id}/execute` → `{ imported, duplicates, errors }`
- `GET /accounts`, `GET /categories`

- [ ] **Step 1: Replace `frontend/src/views/ImportView.vue`**

```vue
<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { useRouter } from 'vue-router'
import AppNav from '@/components/AppNav.vue'
import { useApi } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const { t } = useI18n()
const router = useRouter()
const api = useApi()
const auth = useAuthStore()

const step = ref(1)
const accounts = ref([])
const flatCategories = ref([])
const selectedAccountId = ref('')
const selectedFile = ref(null)
const dragging = ref(false)
const sessionId = ref(null)
const columns = ref([])
const columnMap = ref({ date: '', amount: '', description: '' })
const categoryId = ref('')
const dateFormat = ref('YYYY-MM-DD')
const decimal = ref('dot')
const previewRows = ref([])
const result = ref(null)
const loading = ref(false)

function flattenCats(list) {
  const out = []
  function walk(items) { for (const c of items) { out.push(c); if (c.children) walk(c.children) } }
  walk(list)
  return out
}

onMounted(async () => {
  const [accRes, catRes] = await Promise.all([api.get('/accounts'), api.get('/categories')])
  if (accRes.ok) accounts.value = await accRes.json()
  if (catRes.ok) flatCategories.value = flattenCats(await catRes.json())
  if (accounts.value.length) selectedAccountId.value = String(accounts.value[0].id)
})

function onDrop(e) {
  dragging.value = false
  const f = e.dataTransfer?.files[0]
  if (f) selectedFile.value = f
}

function onFileInput(e) {
  selectedFile.value = e.target.files[0] || null
}

async function uploadFile() {
  if (!selectedFile.value || !selectedAccountId.value) return
  loading.value = true
  const fd = new FormData()
  fd.append('file', selectedFile.value)
  fd.append('account_id', selectedAccountId.value)
  const res = await api.upload('/import/upload', fd)
  loading.value = false
  if (!res.ok) { toast.error(t('import.error.parseError')); return }
  const data = await res.json()
  sessionId.value = data.session_id
  columns.value = data.columns || []
  if (columns.value.length) {
    columnMap.value.date = columns.value[0]
    columnMap.value.amount = columns.value[1] || columns.value[0]
    columnMap.value.description = columns.value[2] || columns.value[0]
  }
  step.value = 2
}

async function loadPreview() {
  loading.value = true
  const res = await api.post(`/import/${sessionId.value}/preview`, {
    column_map: columnMap.value,
    date_format: dateFormat.value,
    decimal: decimal.value,
    category_id: categoryId.value ? parseInt(categoryId.value) : null,
  })
  loading.value = false
  if (res.ok) previewRows.value = (await res.json()).rows || []
}

async function runImport() {
  loading.value = true
  const res = await api.post(`/import/${sessionId.value}/execute`, {
    column_map: columnMap.value,
    date_format: dateFormat.value,
    decimal: decimal.value,
    category_id: categoryId.value ? parseInt(categoryId.value) : null,
  })
  loading.value = false
  if (!res.ok) { toast.error(t('errors.generic')); return }
  result.value = await res.json()
  step.value = 3
}

function restart() {
  step.value = 1
  selectedFile.value = null
  sessionId.value = null
  columns.value = []
  previewRows.value = []
  result.value = null
}
</script>

<template>
  <div class="min-h-dvh bg-background">
    <AppNav />
    <main class="max-w-3xl mx-auto px-4 py-6">
      <h1 class="text-2xl font-bold mb-6">{{ t('import.title') }}</h1>

      <!-- No household -->
      <div v-if="!auth.user?.active_household_id" class="text-center text-muted-foreground py-16">
        {{ t('import.noHousehold') }}
      </div>

      <template v-else>
        <!-- Stepper -->
        <div class="flex items-center gap-2 mb-8">
          <div v-for="(label, i) in [t('import.step.upload'), t('import.step.mapping'), t('import.step.result')]"
               :key="i"
               class="flex items-center gap-2">
            <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
                 :class="step > i + 1 ? 'bg-primary text-primary-foreground' : step === i + 1 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'">
              {{ i + 1 }}
            </div>
            <span class="text-sm" :class="step === i + 1 ? 'font-medium' : 'text-muted-foreground'">{{ label }}</span>
            <span v-if="i < 2" class="text-muted-foreground">→</span>
          </div>
        </div>

        <!-- Step 1: Upload -->
        <Card v-if="step === 1">
          <CardHeader><CardTitle>{{ t('import.step.upload') }}</CardTitle></CardHeader>
          <CardContent class="space-y-4">
            <div class="space-y-1">
              <Label>{{ t('import.account') }}</Label>
              <Select v-model="selectedAccountId">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="acc in accounts" :key="acc.id" :value="String(acc.id)">{{ acc.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div
              class="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors"
              :class="dragging ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'"
              @dragover.prevent="dragging = true"
              @dragleave="dragging = false"
              @drop.prevent="onDrop"
              @click="$refs.fileInput.click()"
            >
              <p class="text-sm text-muted-foreground">{{ t('import.dropzone') }}</p>
              <p v-if="selectedFile" class="text-sm font-medium text-primary mt-2">{{ selectedFile.name }}</p>
              <input ref="fileInput" type="file" accept=".csv,.ofx,.qfx" class="hidden" @change="onFileInput" />
            </div>
            <Button class="w-full" :disabled="!selectedFile || !selectedAccountId || loading" @click="uploadFile">
              {{ loading ? '...' : t('import.step.mapping') + ' →' }}
            </Button>
          </CardContent>
        </Card>

        <!-- Step 2: Mapping -->
        <Card v-if="step === 2">
          <CardHeader><CardTitle>{{ t('import.step.mapping') }}</CardTitle></CardHeader>
          <CardContent class="space-y-4">
            <div v-for="field in ['date', 'amount', 'description']" :key="field" class="space-y-1">
              <Label>{{ t(`import.field.${field}`) }}</Label>
              <Select v-model="columnMap[field]">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="col in columns" :key="col" :value="col">{{ col }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-1">
              <Label>{{ t('import.field.dateFormat') }}</Label>
              <Select v-model="dateFormat">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                  <SelectItem value="DD.MM.YYYY">DD.MM.YYYY</SelectItem>
                  <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-1">
              <Label>{{ t('import.field.decimal') }}</Label>
              <Select v-model="decimal">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="dot">{{ t('import.decimal.dot') }}</SelectItem>
                  <SelectItem value="comma">{{ t('import.decimal.comma') }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-1">
              <Label>{{ t('import.field.category') }}</Label>
              <Select v-model="categoryId">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">—</SelectItem>
                  <SelectItem v-for="cat in flatCategories" :key="cat.id" :value="String(cat.id)">{{ cat.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Preview -->
            <div v-if="previewRows.length" class="rounded-lg border overflow-hidden max-h-48 overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{{ t('transactions.date') }}</TableHead>
                    <TableHead>{{ t('transactions.description') }}</TableHead>
                    <TableHead class="text-right">{{ t('transactions.amount') }}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow v-for="(row, i) in previewRows.slice(0, 5)" :key="i">
                    <TableCell>{{ row.date }}</TableCell>
                    <TableCell>{{ row.description }}</TableCell>
                    <TableCell class="text-right">{{ row.amount }}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>

            <div class="flex gap-2">
              <Button variant="outline" @click="loadPreview" :disabled="loading">Vorschau</Button>
              <Button class="flex-1" @click="runImport" :disabled="loading">
                {{ loading ? '...' : t('import.btn.import') }}
              </Button>
            </div>
          </CardContent>
        </Card>

        <!-- Step 3: Result -->
        <Card v-if="step === 3 && result">
          <CardHeader><CardTitle>{{ t('import.step.result') }}</CardTitle></CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-3 gap-4 text-center">
              <div>
                <p class="text-2xl font-bold text-emerald-500">{{ result.imported }}</p>
                <p class="text-xs text-muted-foreground">{{ t('import.result.imported') }}</p>
              </div>
              <div>
                <p class="text-2xl font-bold text-amber-500">{{ result.duplicates }}</p>
                <p class="text-xs text-muted-foreground">{{ t('import.result.duplicates') }}</p>
              </div>
              <div>
                <p class="text-2xl font-bold text-rose-500">{{ result.errors }}</p>
                <p class="text-xs text-muted-foreground">{{ t('import.result.errors') }}</p>
              </div>
            </div>
            <div v-if="result.duplicates > 0" class="text-sm text-amber-600 bg-amber-50 dark:bg-amber-950 rounded-md p-3">
              {{ t('import.warn.duplicates') }}
            </div>
            <div class="flex gap-2">
              <Button variant="outline" @click="restart">{{ t('import.btn.restart') }}</Button>
              <Button @click="router.push('/transactions')">{{ t('import.btn.toTransactions') }}</Button>
            </div>
          </CardContent>
        </Card>
      </template>
    </main>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/ImportView.vue
git commit -m "feat: add ImportView with 3-step wizard"
```

---

## Task 15: SettingsView

**Files:**
- Modify: `frontend/src/views/SettingsView.vue`

API:
- `GET /households` → `[{ id, name }]`
- `PATCH /households/{id}` → update name
- `GET /households/{id}/members` → `[{ id, name, email, role }]`
- `POST /households/{id}/members` → add member by email
- `DELETE /households/{id}/members/{user_id}` → remove member

- [ ] **Step 1: Replace `frontend/src/views/SettingsView.vue`**

```vue
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import AppNav from '@/components/AppNav.vue'
import { useApi } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const { t } = useI18n()
const api = useApi()
const auth = useAuthStore()

const household = ref(null)
const members = ref([])
const householdName = ref('')
const memberEmail = ref('')

const activeHhId = computed(() => auth.user?.active_household_id)

async function load() {
  if (!activeHhId.value) return
  const [hhRes, membersRes] = await Promise.all([
    api.get('/households'),
    api.get(`/households/${activeHhId.value}/members`),
  ])
  if (hhRes.ok) {
    const all = await hhRes.json()
    household.value = all.find((h) => h.id === activeHhId.value) || null
    householdName.value = household.value?.name || ''
  }
  if (membersRes.ok) members.value = await membersRes.json()
}

async function saveName() {
  if (!activeHhId.value) return
  const res = await api.patch(`/households/${activeHhId.value}`, { name: householdName.value })
  if (res.ok) {
    await auth.fetchUser()
    toast.success(t('settings.save'))
  } else {
    toast.error(t('errors.generic'))
  }
}

async function addMember() {
  if (!memberEmail.value || !activeHhId.value) return
  const res = await api.post(`/households/${activeHhId.value}/members`, { email: memberEmail.value })
  if (res.ok) {
    memberEmail.value = ''
    await load()
    toast.success(t('settings.add'))
  } else {
    toast.error(t('errors.generic'))
  }
}

async function removeMember(userId) {
  if (!confirm(t('settings.remove') + '?')) return
  const res = await api.delete(`/households/${activeHhId.value}/members/${userId}`)
  if (res.ok) { await load(); toast.success(t('settings.remove')) }
  else toast.error(t('errors.generic'))
}

onMounted(load)
</script>

<template>
  <div class="min-h-dvh bg-background">
    <AppNav />
    <main class="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <h1 class="text-2xl font-bold">{{ t('settings.title') }}</h1>

      <!-- Household name -->
      <Card>
        <CardHeader><CardTitle>{{ t('settings.household') }}</CardTitle></CardHeader>
        <CardContent>
          <form @submit.prevent="saveName" class="flex gap-2">
            <div class="flex-1 space-y-1">
              <Label>{{ t('settings.householdName') }}</Label>
              <Input v-model="householdName" required />
            </div>
            <Button type="submit" class="self-end">{{ t('settings.save') }}</Button>
          </form>
        </CardContent>
      </Card>

      <!-- Members -->
      <Card>
        <CardHeader><CardTitle>{{ t('settings.members') }}</CardTitle></CardHeader>
        <CardContent class="space-y-4">
          <div class="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{{ t('auth.name') }}</TableHead>
                  <TableHead>{{ t('auth.email') }}</TableHead>
                  <TableHead>{{ t('accounts.type') }}</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="m in members" :key="m.id">
                  <TableCell class="font-medium">{{ m.name }}</TableCell>
                  <TableCell class="text-muted-foreground text-sm">{{ m.email }}</TableCell>
                  <TableCell>
                    <Badge :variant="m.role === 'owner' ? 'default' : 'secondary'">
                      {{ t(`settings.roles.${m.role}`) }}
                    </Badge>
                  </TableCell>
                  <TableCell class="text-right">
                    <Button
                      v-if="m.role !== 'owner'"
                      variant="ghost"
                      size="sm"
                      class="text-destructive hover:text-destructive"
                      @click="removeMember(m.id)"
                    >
                      {{ t('settings.remove') }}
                    </Button>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>

          <!-- Add member -->
          <form @submit.prevent="addMember" class="flex gap-2">
            <Input
              v-model="memberEmail"
              type="email"
              :placeholder="t('settings.memberEmail')"
              class="flex-1"
              required
            />
            <Button type="submit">{{ t('settings.add') }}</Button>
          </form>
        </CardContent>
      </Card>
    </main>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/SettingsView.vue
git commit -m "feat: add SettingsView with household and members management"
```

---

## Task 16: BackupView

**Files:**
- Modify: `frontend/src/views/BackupView.vue`

Admin-only. API:
- `GET /backup/settings` → `{ backup_retention_days }`
- `PATCH /backup/settings` → update retention
- `POST /backup/trigger` → trigger backup (201)
- `GET /backup/list` → `[{ filename, size_bytes, created_at }]`
- `GET /backup/{filename}/download` → file download
- `DELETE /backup/{filename}` → 204

- [ ] **Step 1: Replace `frontend/src/views/BackupView.vue`**

```vue
<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import AppNav from '@/components/AppNav.vue'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const { t } = useI18n()
const api = useApi()

const retentionDays = ref('7')
const backups = ref([])
const triggering = ref(false)

function fmtSize(bytes) {
  const mb = bytes / (1024 * 1024)
  return mb >= 1 ? mb.toFixed(1) + ' MB' : (bytes / 1024).toFixed(0) + ' KB'
}

function fmtDate(iso) {
  return new Date(iso).toLocaleString()
}

async function loadSettings() {
  const res = await api.get('/backup/settings')
  if (res.ok) {
    const data = await res.json()
    retentionDays.value = String(data.backup_retention_days)
  }
}

async function saveSettings() {
  const res = await api.patch('/backup/settings', { backup_retention_days: parseInt(retentionDays.value) })
  if (res.ok) toast.success(t('backup.saved'))
  else toast.error(t('errors.generic'))
}

async function triggerBackup() {
  triggering.value = true
  const res = await api.post('/backup/trigger', {})
  triggering.value = false
  if (res.status === 201) {
    toast.success(t('backup.triggerSuccess'))
    await loadBackups()
  } else {
    toast.error(t('errors.generic'))
  }
}

async function loadBackups() {
  const res = await api.get('/backup/list')
  if (res.ok) backups.value = await res.json()
}

function downloadBackup(filename) {
  const token = localStorage.getItem('helledger_token')
  const a = document.createElement('a')
  a.href = `/api/backup/${filename}/download`
  a.download = filename
  // Fetch with auth to trigger download
  fetch(a.href, { headers: { Authorization: `Bearer ${token}` } })
    .then((res) => res.blob())
    .then((blob) => {
      const url = URL.createObjectURL(blob)
      a.href = url
      a.click()
      URL.revokeObjectURL(url)
    })
}

async function deleteBackup(filename) {
  if (!confirm(t('backup.deleteConfirm'))) return
  const res = await api.delete(`/backup/${filename}`)
  if (res.ok) { await loadBackups(); toast.success(t('backup.delete')) }
  else toast.error(t('errors.generic'))
}

onMounted(async () => {
  await Promise.all([loadSettings(), loadBackups()])
})
</script>

<template>
  <div class="min-h-dvh bg-background">
    <AppNav />
    <main class="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <h1 class="text-2xl font-bold">{{ t('backup.title') }}</h1>

      <!-- Settings -->
      <Card>
        <CardHeader><CardTitle>{{ t('backup.settings') }}</CardTitle></CardHeader>
        <CardContent>
          <form @submit.prevent="saveSettings" class="flex gap-2 items-end">
            <div class="flex-1 space-y-1">
              <Label>{{ t('backup.retentionDays') }}</Label>
              <Input v-model="retentionDays" type="number" min="1" max="365" required />
            </div>
            <Button type="submit">{{ t('backup.save') }}</Button>
          </form>
        </CardContent>
      </Card>

      <!-- Trigger -->
      <Card>
        <CardContent class="p-6">
          <Button class="w-full" :disabled="triggering" @click="triggerBackup">
            {{ triggering ? '...' : t('backup.triggerBtn') }}
          </Button>
        </CardContent>
      </Card>

      <!-- Backup list -->
      <Card>
        <CardHeader><CardTitle>{{ t('backup.list') }}</CardTitle></CardHeader>
        <CardContent>
          <div v-if="backups.length === 0" class="text-center text-muted-foreground py-8">
            {{ t('backup.empty') }}
          </div>
          <div v-else class="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{{ t('backup.filename') }}</TableHead>
                  <TableHead>{{ t('backup.size') }}</TableHead>
                  <TableHead>{{ t('backup.createdAt') }}</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="b in backups" :key="b.filename">
                  <TableCell class="font-mono text-sm">{{ b.filename }}</TableCell>
                  <TableCell class="tabular-nums text-sm">{{ fmtSize(b.size_bytes) }}</TableCell>
                  <TableCell class="text-sm text-muted-foreground">{{ fmtDate(b.created_at) }}</TableCell>
                  <TableCell class="text-right space-x-1">
                    <Button variant="ghost" size="sm" @click="downloadBackup(b.filename)">{{ t('backup.download') }}</Button>
                    <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="deleteBackup(b.filename)">
                      {{ t('backup.delete') }}
                    </Button>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </main>
  </div>
</template>
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/BackupView.vue
git commit -m "feat: add BackupView with settings, trigger, and backup list"
```

---

## Task 17: Dockerfile + main.py Static Path

**Files:**
- Modify: `Dockerfile`
- Modify: `backend/app/main.py:93-95`

The current `main.py` static path resolves to `frontend/` relative to the project root locally, but fails in Docker (path depth mismatch). Fix by using an env var `HELLEDGER_FRONTEND` with fallback.

Current `main.py:93-95`:
```python
_frontend = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(_frontend):
    app.mount("/", StaticFiles(directory=_frontend, html=True), name="static")
```

Current `Dockerfile` stage 1 (lines 1-4):
```dockerfile
FROM node:20-alpine AS frontend-builder
WORKDIR /build
COPY frontend/ .
```

- [ ] **Step 1: Update `backend/app/main.py` static path**

Replace lines 93-95 with:

```python
_frontend = os.environ.get("HELLEDGER_FRONTEND") or os.path.join(
    os.path.dirname(__file__), "..", "..", "frontend", "dist"
)
if os.path.isdir(_frontend):
    app.mount("/", StaticFiles(directory=_frontend, html=True), name="static")
```

When `HELLEDGER_FRONTEND` env var is not set (local dev), the path resolves to `frontend/dist` relative to the project root. In Docker, `HELLEDGER_FRONTEND=/app/frontend/dist` is set explicitly.

- [ ] **Step 2: Update `Dockerfile`**

Replace the full Dockerfile with:

```dockerfile
# Stage 1: build frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /build
COPY frontend/ .
RUN npm ci && npm run build

# Stage 2: Python application
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --system --no-create-home --group helledger \
    && mkdir -p /data /backups \
    && chown helledger:helledger /data /backups

COPY backend/app/ ./app/
COPY backend/alembic/ ./alembic/
COPY backend/alembic.ini .
COPY --from=frontend-builder /build/dist ./frontend/dist/

ENV HELLEDGER_FRONTEND=/app/frontend/dist

USER helledger

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s \
    CMD curl -f http://localhost:3000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
```

Key changes vs. current Dockerfile:
- Added `RUN npm ci && npm run build` in builder stage
- Changed `COPY --from=frontend-builder /build ./frontend/` → `COPY --from=frontend-builder /build/dist ./frontend/dist/`
- Added `ENV HELLEDGER_FRONTEND=/app/frontend/dist`

- [ ] **Step 3: Verify frontend build locally**

```bash
cd frontend && npm run build
```

Expected: `frontend/dist/` created with `index.html`, `assets/`, etc.

- [ ] **Step 4: Verify Python backend starts without errors**

```bash
cd backend && python -m uvicorn app.main:app --port 3000
```

Expected: starts without import errors; static files mount at `frontend/dist/` if it exists.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile backend/app/main.py
git commit -m "feat: build vue frontend in docker and serve dist/"
```

---

## Self-Review

### Spec Coverage

| Spec requirement | Covered in task |
|---|---|
| Vue 3 + Vite + Tailwind CSS | Task 1 |
| shadcn-vue "New York" + CSS vars + indigo primary | Task 1, 2 |
| Inter Variable font (no CDN) | Task 1 (main.css) |
| Dark/Light mode toggle (Sun/Moon + Switch) | Task 7 (AppNav) |
| Default from prefers-color-scheme, persist to localStorage | Task 4 (theme store) |
| Pinia auth store (token, user, isAdmin) | Task 4 |
| API composable (localStorage token, refresh retry) | Task 3 |
| Vue Router hash mode, requiresAuth/requiresAdmin guards | Task 6 |
| vue-i18n (replaces i18next CDN) | Task 6 |
| AppNav responsive (desktop + mobile Sheet) | Task 7 |
| Household switcher DropdownMenu | Task 7 |
| LoginView: tabs, sonner toast errors | Task 8 |
| DashboardView: month nav, 3 cards, soll-ist bars, donut chart | Task 9 |
| AccountsView: table + dialog | Task 10 |
| CategoriesView: hierarchical table + dialog | Task 11 |
| TransactionsView: filters + table + dialog | Task 12 |
| ReportsView: 4 chart tabs, CSV export | Task 13 |
| ImportView: 3-step wizard | Task 14 |
| SettingsView: household + members | Task 15 |
| BackupView: settings + trigger + list | Task 16 |
| Dockerfile: npm build, serve dist | Task 17 |
| main.py: static path → frontend/dist | Task 17 |
| nav.import i18n key added | Task 5 |

### Placeholder Scan

No TBD or TODO items in any step. All steps contain complete code.

### Type Consistency

- `useApi()` returns `{ get, post, patch, delete, upload }` — used consistently in all views
- `useAuthStore()` exposes `token`, `user`, `isAuthenticated`, `isAdmin`, `login`, `register`, `fetchUser`, `logout`, `setToken`
- `useThemeStore()` exposes `isDark`, `toggle`, `init`
- shadcn components imported from `@/components/ui/<name>` throughout

### Edge Cases Noted

- `SollIstRow` in DashboardView is defined as an Options API component in the same file's `<script>` block (not `<script setup>`). Vue 3 supports this but the subagent must keep both script blocks. Alternatively, extract to `src/components/SollIstRow.vue` — either works.
- `Select v-model.number` in ReportsView for month/year — verify that shadcn-vue Select supports number model values, otherwise cast in handler.
- Import wizard `loadPreview` button shows German text "Vorschau" — replace with `t('import.step.mapping')` or add a new i18n key `import.btn.preview` if needed.
