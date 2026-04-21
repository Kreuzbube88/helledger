# HELLEDGER M4: Reporting & Charts — Design

## Goal

Eigene Berichte-Seite mit 4 interaktiven Charts (Donut, Balken, Linie, Soll/Ist), frei wählbarem Zeitraum (Monat / Jahr / frei), Konto-Filter und Export (PNG + CSV). Chart.js via CDN, Cinema Dark + Glassmorphism Design.

## Architecture

Backend: neuer Router `reports.py` mit 4 dedizierten Aggregations-Endpoints, kein neues DB-Modell (basiert auf bestehender `transactions`-Tabelle). Frontend: neue Seite `reports.js`, Chart.js CDN, gemeinsame Design-Tokens. Kein Build-Step, keine neuen Abhängigkeiten außer Chart.js CDN.

---

## 1. API

### Router `backend/app/routers/reports.py`, Prefix `/reports`

Alle Endpoints: haushaltsgebunden (`active_household_id` des eingeloggten Users, 400 wenn nicht gesetzt). Transfer-Transaktionen (`transaction_type = "transfer"`) werden in allen Endpoints herausgefiltert, außer `balance-history`.

| Method | Path | Query-Params | Beschreibung |
|--------|------|-------------|--------------|
| GET | `/reports/expenses-by-category` | `from_date`, `to_date`, `account_id?` | Ausgaben summiert pro Kategorie (absoluter Betrag) |
| GET | `/reports/monthly-trend` | `from_date`, `to_date`, `account_id?` | Einnahmen + Ausgaben pro Monat als Array |
| GET | `/reports/balance-history` | `from_date`, `to_date`, `account_id` | Kontostand-Verlauf täglich (Pflichtfeld: `account_id`) |
| GET | `/reports/soll-ist` | `from_date`, `to_date`, `account_id?` | Soll/Ist-Vergleich analog Dashboard-Endpoint, aber für beliebigen Zeitraum |

### Response-Schemas

**`expenses-by-category`:**
```json
[{ "category_id": 1, "category_name": "Lebensmittel", "total": "320.50" }]
```

**`monthly-trend`:**
```json
[{ "year": 2026, "month": 1, "income": "2500.00", "expenses": "1800.00" }]
```

**`balance-history`:**
```json
[{ "date": "2026-01-01", "balance": "1200.00" }]
```
Berechnung: `starting_balance + SUM(amount) WHERE account_id = X AND date <= target_date` — ein Eintrag pro Tag im Zeitraum.

**`soll-ist`:** Gleiche Struktur wie bestehender Dashboard-Endpoint `GET /accounts/soll-ist`, aber mit `from_date`/`to_date` statt `year`/`month`.

### Validierung

- `from_date` und `to_date`: ISO-Date-Strings (`YYYY-MM-DD`), `from_date <= to_date`
- `account_id` bei `balance-history`: Pflicht (400 wenn fehlt)
- Maximaler Zeitraum: keine serverseitige Begrenzung

---

## 2. Frontend

### Route & Navigation

- Route: `/reports`
- Nav-Eintrag: "Berichte" zwischen "Transaktionen" und "Einstellungen"
- Neue Datei: `frontend/js/views/reports.js`

### Filter-Leiste

Glassmorphism-Card oben auf der Seite:

- **Zeitraum-Buttons:** `Monat` | `Jahr` | `Frei`
  - `Monat`: zeigt Monat/Jahr-Picker (wie Dashboard), berechnet `from_date`/`to_date` automatisch
  - `Jahr`: zeigt Jahr-Picker, `from_date = YYYY-01-01`, `to_date = YYYY-12-31`
  - `Frei`: zeigt zwei Date-Inputs (`from_date`, `to_date`)
- **Konto-Dropdown:** "Alle Konten" (default) + einzelne Konten aus `GET /accounts`
- **Export-Dropdown:** "PNG herunterladen" / "CSV herunterladen"

Beim Ändern eines Filters werden alle Charts neu geladen.

### Chart-Layout

2 Spalten auf Desktop (≥ 768px), 1 Spalte auf Mobile. Jeder Chart in einer Glassmorphism-Card mit Titel und eigenem Export-Button.

```
┌──────────────────────┬──────────────────────┐
│  Ausgaben nach       │  Einnahmen vs.       │
│  Kategorie (Donut)   │  Ausgaben (Balken)   │
├──────────────────────┼──────────────────────┤
│  Kontostand-Verlauf  │  Soll/Ist-Vergleich  │
│  (Linie)             │  (Balken horizontal) │
└──────────────────────┴──────────────────────┘
```

**Kontostand-Verlauf:** nur aktiv wenn ein spezifisches Konto gewählt ist. Bei "Alle Konten" zeigt die Card einen Hinweis: "Bitte ein Konto auswählen."

### Chart.js Konfiguration

- CDN-Einbindung in `index.html` (ein `<script>`-Tag)
- Gemeinsame Dark-Theme-Defaults: `Chart.defaults.color = '#94a3b8'`, transparente Grid-Lines
- Farbpalette aus bestehenden Design-Tokens:
  - Primär: `#6366f1` (Indigo)
  - Positiv/Einnahmen: `#10b981` (Emerald)
  - Negativ/Ausgaben: `#f43f5e` (Rose)
  - Kategorien-Donut: rotierendes Array aus 8 Farben der bestehenden Palette
- Soll/Ist-Chart: horizontales Balkendiagramm (`indexAxis: 'y'`)

### Export

- **PNG:** `chart.canvas.toDataURL('image/png')` → `<a download>` trigger
- **CSV:** Aus dem letzten API-Response-Objekt generiert, als Blob-Download
- "Alle Charts exportieren" im globalen Export-Dropdown lädt alle aktiven Charts als PNGs sequenziell herunter (deaktivierte/leere Charts werden übersprungen)

### Ladezustand & Fehler

- Laden: Skeleton-Shimmer in jeder Chart-Card (bestehende Glassmorphism-Animation)
- Keine Daten: Placeholder-Text mittig im Canvas ("Keine Daten für diesen Zeitraum")
- API-Fehler: Toast, Chart-Card zeigt Fehlerzustand

---

## 3. i18n

Neue Keys in `i18n.js` für `de` und `en`:

| Key | DE | EN |
|-----|----|----|
| `nav.reports` | Berichte | Reports |
| `reports.title` | Berichte | Reports |
| `reports.period.month` | Monat | Month |
| `reports.period.year` | Jahr | Year |
| `reports.period.custom` | Frei | Custom |
| `reports.filter.allAccounts` | Alle Konten | All Accounts |
| `reports.chart.expensesByCategory` | Ausgaben nach Kategorie | Expenses by Category |
| `reports.chart.monthlyTrend` | Einnahmen & Ausgaben | Income & Expenses |
| `reports.chart.balanceHistory` | Kontostand-Verlauf | Balance History |
| `reports.chart.sollIst` | Soll/Ist-Vergleich | Budget vs. Actual |
| `reports.export.png` | PNG herunterladen | Download PNG |
| `reports.export.csv` | CSV herunterladen | Download CSV |
| `reports.noData` | Keine Daten für diesen Zeitraum | No data for this period |
| `reports.selectAccount` | Bitte ein Konto auswählen | Please select an account |

---

## 4. Fehlerbehandlung & Edge Cases

- Kein aktiver Haushalt → Toast + Redirect zu `/settings`
- `balance-history` bei "Alle Konten": Chart deaktiviert mit Hinweistext
- Zeitraum-Validierung im Frontend: `to_date >= from_date`, sonst kein API-Call
- Transfer-Transaktionen werden serverseitig aus Kategorie-Chart und Soll/Ist herausgefiltert
- Kategorien ohne Budget erscheinen im Soll/Ist mit `soll = 0`
- Sehr große Zeiträume (>2 Jahre bei `balance-history`): Backend liefert wöchentliche Datenpunkte statt tägliche (Schwellwert: > 365 Tage → GROUP BY Woche)

---

## 5. Dateien

| Aktion | Pfad |
|--------|------|
| Neu | `backend/app/routers/reports.py` |
| Neu | `backend/app/schemas/reports.py` |
| Neu | `frontend/js/views/reports.js` |
| Ändern | `backend/app/main.py` — Router einbinden |
| Ändern | `frontend/index.html` — Chart.js CDN, neue Route |
| Ändern | `frontend/js/router.js` — Route `/reports` |
| Ändern | `frontend/js/nav.js` — Nav-Eintrag |
| Ändern | `frontend/js/i18n.js` — neue Keys |
