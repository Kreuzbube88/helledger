# HELLEDGER M3: Transaktionen + Monats-Dashboard — Design

## Goal

Transaktionen erfassen (CRUD + Transfers), Monats-Dashboard mit Soll/Ist-Vergleich (hierarchisch, CSS Progress Bars), Kontostände, visuelles WOW-Design (Cinema Dark + Glassmorphism), Toast-System ohne Browser-Dialoge.

## Architecture

Backend: drei dedizierte Aggregations-Endpoints für Dashboard-Daten, ein Transactions-Router für CRUD + Transfer + Summary. Frontend: Dashboard komplett neu (Cinema Dark + Glassmorphism), neue Transactions-Seite, gemeinsame `animations.js` und `toast.js` Module. Alembic-Migration `003_transactions.py`.

---

## 1. Datenmodell

### Neue Tabelle `transactions`

| Feld | Typ | Notizen |
|------|-----|---------|
| id | Integer PK | |
| household_id | FK → households.id | CASCADE, indexed |
| account_id | FK → accounts.id | CASCADE, indexed |
| category_id | FK → categories.id | SET NULL on delete, **nullable** (nur NULL bei `transaction_type="transfer"`) |
| amount | Numeric(12,2) | Vorzeichenbehaftet: positiv = Einnahme aufs Konto, negativ = Ausgabe |
| date | Date | Buchungsdatum |
| description | String(255) | |
| transaction_type | String(20) | `income` / `expense` / `transfer` |
| transfer_peer_id | FK → transactions.id (self) | nullable, SET NULL on delete |
| created_at | DateTime | |
| updated_at | DateTime | |

**Vorzeichen-Konvention:**
- Einnahme: `+500.00`
- Ausgabe: `-120.00`
- Transfer: `-500.00` auf Quell-Konto + `+500.00` auf Ziel-Konto

**Kontostand:** `starting_balance + SUM(amount) WHERE account_id = X AND date <= target_date`

**Validierung (server-seitig):**
- `category_id` ist Pflicht wenn `transaction_type != "transfer"`
- Transfer-Erstellung: atomarer POST über dedizierten Endpoint (beide Rows in einer DB-Transaktion)
- `amount` im Request immer positiv (Frontend schickt unsigned); Backend setzt Vorzeichen basierend auf `transaction_type` und Kontext

---

## 2. API

### Transactions CRUD

| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | /api/transactions | Liste; Filter: `?year=&month=&account_id=&category_id=` (alle optional) |
| POST | /api/transactions | Einzelne Transaktion (income/expense) |
| POST | /api/transactions/transfer | Atomarer Transfer: zwei Rows, verknüpft per `transfer_peer_id` |
| GET | /api/transactions/{id} | Detail |
| PATCH | /api/transactions/{id} | Bearbeiten |
| DELETE | /api/transactions/{id} | Löschen (bei Transfer: auch Peer löschen) |

**POST /api/transactions Body:**
```json
{
  "account_id": 1,
  "category_id": 5,
  "amount": "120.00",
  "date": "2026-04-15",
  "description": "Strom April",
  "transaction_type": "expense"
}
```
Backend: `amount` im Request immer positiv; Backend setzt Vorzeichen: income → `+amount`, expense → `-amount`.

**PATCH /api/transactions/{id} Body** (alle Felder optional):
- `amount` immer positiv; wenn `transaction_type` mitgesendet wird, setzt Backend das Vorzeichen neu; wenn nur `amount` gesendet wird, wird der existierende Typ verwendet
- PATCH auf Transfer-Rows ist **nicht erlaubt** (HTTP 405) — Transfers müssen gelöscht und neu erstellt werden

**POST /api/transactions/transfer Body:**
```json
{
  "from_account_id": 1,
  "to_account_id": 2,
  "amount": "500.00",
  "date": "2026-04-01",
  "description": "Sparkasse"
}
```
Erstellt: Row A (`account_id=1, amount=-500.00, transfer_peer_id=B.id`) + Row B (`account_id=2, amount=+500.00, transfer_peer_id=A.id`).

### Dashboard-Endpoints

**GET /api/transactions/summary?year=2026&month=4**
```json
{ "income": "2500.00", "expenses": "1800.50", "balance": "699.50" }
```
`expenses` ist immer positiv (Absolutwert); Frontend setzt Vorzeichen für Anzeige.

**GET /api/categories/soll-ist?year=2026&month=4**
```json
[
  {
    "id": 1, "name": "Fixkosten", "category_type": "fixed",
    "soll": "1200.00", "ist": "1180.00", "diff": "20.00",
    "children": [
      { "id": 3, "name": "Miete", "soll": "1000.00", "ist": "1000.00", "diff": "0.00", "children": [] },
      { "id": 4, "name": "Internet", "soll": "50.00", "ist": "49.00", "diff": "1.00", "children": [] }
    ]
  }
]
```
- `soll`: aktiver ExpectedValue oder Budget für den Monat; `"0.00"` wenn keiner gesetzt
- `ist`: `ABS(SUM(amount))` aller Transaktionen dieser Kategorie **+ ihrer Kinder** im Monat; `"0.00"` wenn keine Transaktionen
- `diff`: `soll - ist` (positiv = unter Budget, negativ = überschritten)
- Eltern ohne eigene EV aggregieren `soll`/`ist` ihrer Kinder
- Transfers (`category_id IS NULL`) werden nie in Soll/Ist einbezogen
- **Welche Kategorien werden zurückgegeben:** alle nicht-archivierten Kategorien des Haushalts, auch wenn `soll=0` und `ist=0`

**GET /api/accounts/balances?until=2026-04-30**
```json
[
  { "id": 1, "name": "Girokonto", "account_type": "checking", "balance": "3245.80", "currency": "EUR", "archived": false }
]
```
Nur nicht-archivierte Accounts. `balance = starting_balance + SUM(amount WHERE date <= until)`.

---

## 3. Frontend

### Globale Design-Tokens (ergänzt in `index.html` `<style>`)

```css
:root {
  --surface:     rgba(255,255,255,0.05);
  --border:      rgba(255,255,255,0.08);
  --accent:      #6366f1;
  --accent-glow: rgba(99,102,241,0.25);
  --income:      #10b981;
  --expense:     #f43f5e;
  --transfer:    #8b5cf6;
  --easing:      cubic-bezier(0.16,1,0.3,1);
  --easing-spring: cubic-bezier(0.34,1.56,0.64,1);
}
body { background: linear-gradient(135deg, #020203 0%, #0a0a0f 50%, #020203 100%); }
```

**Ambient Blobs** (zwei absolute `<div>`s in `index.html`):
```html
<div class="blob" style="background:radial-gradient(circle,rgba(99,102,241,0.08),transparent 70%);
     width:600px;height:600px;top:-200px;left:-100px;animation:blobA 15s ease-in-out infinite alternate;"></div>
<div class="blob" style="background:radial-gradient(circle,rgba(139,92,246,0.06),transparent 70%);
     width:500px;height:500px;bottom:-100px;right:-100px;animation:blobB 18s ease-in-out infinite alternate;"></div>
```
```css
@keyframes blobA { from { transform: translate(0,0); } to { transform: translate(40px,30px); } }
@keyframes blobB { from { transform: translate(0,0); } to { transform: translate(-30px,40px); } }
.blob { position:fixed; pointer-events:none; z-index:0; border-radius:50%; }
```

### `frontend/js/toast.js`

**Kein `alert()`, `confirm()`, `prompt()` — niemals, nirgendwo.**

```javascript
export function toast(message, type = "success") // type: "success" | "error" | "info"
export function confirm(message, onConfirm)       // Custom Confirm-Modal (nicht window.confirm)
```

Toast: `position:fixed; bottom:1.5rem; right:1.5rem` — immer unten rechts.
Auto-dismiss nach 3s. Glassmorphism-Card mit farbigem Left-Border (emerald/rose/indigo je Typ).
Slide-in Animation von rechts unten (translateY(20px) → 0, opacity 0 → 1, 250ms expo.out).

`confirm()` rendert ein Custom-Modal mit Bestätigungs-Button (rot für Lösch-Aktionen).

Alle bestehenden `confirm()`-Aufrufe in accounts.js, categories.js, settings.js werden durch `toast.confirm()` ersetzt.

### `frontend/js/animations.js`

```javascript
export function countUp(el, targetValue, duration = 600, currency = true)
export function animateProgressBars(container)  // setzt alle [data-pct] bars von 0 auf target
export function fadeInUp(elements, stagger = 30) // staggered fadeInUp für Listen
```

### `frontend/js/views/dashboard.js` (komplett neu)

**Layout:**
```
[Ambient Blobs] ← fixed, z-0
[Nav]
[Monat-Header]  ◀  April 2026  ▶         [+ Neu]
[3 Stat-Cards]  Einnahmen | Ausgaben | Saldo
[Soll/Ist]      Hierarchische Tabelle mit Progress Bars
[Kontostände]   Card-Grid
```

**Stat-Cards:**
- `background: var(--surface); backdrop-filter: blur(15px); border: 1px solid var(--border); border-radius: 16px`
- Einnahmen: `box-shadow: 0 0 40px rgba(16,185,129,0.15)`
- Ausgaben: `box-shadow: 0 0 40px rgba(244,63,94,0.15)`
- Saldo: `box-shadow: 0 0 40px rgba(99,102,241,0.15)`
- Zahlen: Count-up Animation beim Laden und bei Monatswechsel

**Monatswechsel:** Klick auf `◀`/`▶` → Content `opacity:0, transform:translateY(8px)` (150ms) → API-Calls → `opacity:1, transform:translateY(0)` (200ms expo.out)

**Soll/Ist Tabelle:**
- Pro Zeile: Kategoriename (eingerückt bei Kindern) | Soll | Ist | Diff | Progress Bar
- Progress Bar: `height: 6px; border-radius: 3px`
  - Im Budget (`ist ≤ soll`): `background: linear-gradient(to right, #6366f1, #10b981)`
  - Überschritten: `background: linear-gradient(to right, #f97316, #f43f5e)`
- Breite: `min(ist/soll * 100%, 100%)` — gekappt bei 100%, überschrittene Bars rot
- Animation: staggered `width: 0 → target` (400ms expo.out, 30ms Delay pro Zeile)
- Row-Hover: `background: rgba(255,255,255,0.03); border-left: 2px solid var(--accent)` mit 150ms transition
- Eltern-Zeilen: Toggle-Button `▶/▼` zum Ein-/Ausklappen der Kinder

**„+ Neu"-Button:**
- `background: linear-gradient(135deg, #6366f1, #8b5cf6)`
- `box-shadow: 0 0 24px rgba(99,102,241,0.4)`
- Hover: Scale 1.03, verstärkter Glow (200ms)
- Öffnet Transaktion-Modal

**Kontostände:**
- Card-Grid (2 pro Zeile auf Desktop)
- Glassmorphism-Cards mit Kontoname, Typ-Badge, Kontostand (Count-up)

### `frontend/js/views/transactions.js` (neu)

**Layout:**
```
[Filter-Bar]  [April 2026▾]  [Alle Konten▾]  [Alle Kategorien▾]     [+ Transaktion]
[Tabelle]     Datum | Konto | Kategorie | Beschreibung | Betrag | Aktionen
```

- `overflow-x: auto` Wrapper (Mobile)
- Zeilen farbcodiert per Left-Border: income=emerald, expense=rose, transfer=violet
- Beträge: positiv in `var(--income)`, negativ in `var(--expense)`, tabular-nums
- Transfer-Zeilen: Kategorie zeigt „→ Zielkonto" bzw. „← Quellkonto"
- Zeileneinfade: `fadeInUp` gestaffelt (30ms Delay)
- Bearbeiten-Icon + Löschen-Icon pro Zeile
  - Löschen: `toast.confirm()` Custom-Modal, kein `window.confirm()`

**Transaktion-Modal:**
- Backdrop: `backdrop-filter: blur(20px); background: rgba(0,0,0,0.6)`
- Karte: Glassmorphism, Spring-Animation von unten (`var(--easing-spring)`, 350ms)
- Typ-Toggle oben: `Ausgabe | Einnahme | Transfer` (Pill-Buttons, aktiver hervorgehoben)
- **Ausgabe/Einnahme-Felder:** Konto, Kategorie (Dropdown, nach Typ gefiltert), Betrag (positiv), Datum, Beschreibung
- **Transfer-Felder:** Von-Konto, Nach-Konto, Betrag, Datum, Beschreibung (keine Kategorie)
- Submit: Loading-Spinner im Button, dann Toast „Gespeichert ✓" oder Fehler inline
- Focus: Input-Felder leuchten beim Fokus mit Indigo-Glow (`box-shadow: 0 0 0 3px var(--accent-glow)`)

### Nav-Erweiterung

Link **„Transaktionen"** wird zwischen Dashboard und Konten eingefügt (in `nav.js`).

### Locale-Keys (Ergänzung)

**de.json:**
```json
{
  "nav": { "transactions": "Transaktionen" },
  "transactions": {
    "title": "Transaktionen",
    "add": "Transaktion hinzufügen",
    "type": { "income": "Einnahme", "expense": "Ausgabe", "transfer": "Überweisung" },
    "fields": {
      "account": "Konto", "toAccount": "Ziel-Konto", "fromAccount": "Quell-Konto",
      "category": "Kategorie", "amount": "Betrag", "date": "Datum", "description": "Beschreibung"
    },
    "filters": { "allAccounts": "Alle Konten", "allCategories": "Alle Kategorien" },
    "saved": "Transaktion gespeichert", "deleted": "Transaktion gelöscht",
    "confirmDelete": "Transaktion wirklich löschen?", "empty": "Keine Transaktionen in diesem Monat"
  },
  "dashboard": {
    "income": "Einnahmen", "expenses": "Ausgaben", "balance": "Saldo",
    "sollIst": "Soll / Ist", "accounts": "Kontostände",
    "soll": "Soll", "ist": "Ist", "diff": "Differenz"
  }
}
```

**en.json:** Englische Entsprechungen, gleiche Struktur.

---

## 4. Testing

**`backend/tests/test_transactions.py`:**
- CRUD (income, expense): Vorzeichen korrekt gesetzt
- Transfer: zwei Rows mit `transfer_peer_id`, atomarer Rollback bei Fehler
- DELETE Transfer: löscht auch Peer
- Filter: Jahr/Monat, Account, Kategorie
- Household-Isolation: User B sieht keine Transaktionen von User A
- Validation: `category_id` Pflicht für income/expense, nicht für transfer

**`backend/tests/test_dashboard.py`:**
- Summary: korrekte Summierung income/expense/balance
- Soll/Ist: Eltern aggregieren Kinder; `diff` korrekt; keine Transfers in Soll/Ist
- Kontostände: `starting_balance + SUM(amount)` bis `until`-Datum
- Korrekter Monatsbezug (Transaktion am Monatsletzten zählt, am Ersten des Folgemonats nicht)

**Ziel:** alle 69 bestehenden Tests + neue M3-Tests bleiben grün.

---

## 5. Datei-Struktur

**Neu (Backend):**
- `backend/app/models/transaction.py`
- `backend/alembic/versions/003_transactions.py`
- `backend/app/schemas/transaction.py`
- `backend/app/routers/transactions.py`
- `backend/tests/test_transactions.py`
- `backend/tests/test_dashboard.py`

**Neu (Frontend):**
- `frontend/js/toast.js`
- `frontend/js/animations.js`
- `frontend/js/views/transactions.js`

**Geändert (Frontend):**
- `frontend/js/views/dashboard.js` — komplett neu
- `frontend/js/views/accounts.js` — `confirm()` → `toast.confirm()`
- `frontend/js/views/categories.js` — `confirm()` → `toast.confirm()`
- `frontend/js/views/settings.js` — `confirm()` → `toast.confirm()`
- `frontend/js/nav.js` — „Transaktionen"-Link ergänzen
- `frontend/index.html` — Ambient Blobs, Design Tokens, neue Route `#/transactions`
- `frontend/locales/de.json` / `en.json` — M3-Keys ergänzen

**Geändert (Backend):**
- `backend/app/models/__init__.py` — Transaction importieren
- `backend/app/main.py` — transactions-Router einbinden
- `backend/app/routers/categories.py` — Soll/Ist-Endpoint ergänzen
- `backend/app/routers/accounts.py` — Balances-Endpoint ergänzen

---

## 6. No-Browser-Dialogs Regel

**Absolut verboten:** `window.alert()`, `window.confirm()`, `window.prompt()` — in keiner Datei, niemals.

Stattdessen:
- Fehler → Inline unter Feld oder Toast (rot)
- Bestätigung vor Löschen → `toast.confirm()` Custom-Modal
- Erfolg → Toast grün (3s auto-dismiss, unten rechts)
- Info → Toast blau

Diese Regel gilt für alle bestehenden und neuen Dateien.
