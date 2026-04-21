# HELLEDGER M5: CSV/OFX Import — Design

## Goal

Eigenständige Import-Seite `/import` mit 3-Schritt-Wizard: Datei-Upload (CSV, OFX, QFX) → Spalten-Mapping (CSV) → Ergebnis. Backend parst Dateien, erkennt Spalten automatisch, User kann Mapping korrigieren. Duplikate werden gewarnt, nicht blockiert.

## Architecture

Zwei-Schritt-API: `POST /import/parse` liefert Preview + Auto-Mapping-Vorschlag, Backend cached Parsed Rows per Session-Token (10 Min, In-Memory-Dict). `POST /import/confirm` nimmt Mapping-Config, importiert, gibt Duplikat-Warnung zurück. Kein neues DB-Modell. Kein Build-Step, keine neuen Abhängigkeiten.

---

## 1. API

### Router `backend/app/routers/import_.py`, Prefix `/import`

Alle Endpoints: haushaltsgebunden (`active_household_id` des eingeloggten Users, 400 wenn nicht gesetzt).

#### `POST /import/parse`

Multipart-Upload mit Feldern `file` und `account_id`.

**Response:**
```json
{
  "session_token": "uuid4",
  "format": "csv",
  "columns": ["Buchungsdatum", "Betrag", "Verwendungszweck"],
  "preview_rows": [["01.01.2026", "-45,00", "Rewe"], "..."],
  "suggested_mapping": {
    "date": "Buchungsdatum",
    "amount": "Betrag",
    "description": "Verwendungszweck"
  },
  "detected_date_format": "%d.%m.%Y",
  "detected_decimal_separator": ","
}
```

Für OFX/QFX: `columns` = `["date", "amount", "description"]` (fix), `suggested_mapping` = vollständig vorausgefüllt, kein Mapping-Schritt im Frontend nötig.

#### `POST /import/confirm`

```json
{
  "session_token": "uuid4",
  "account_id": 1,
  "category_id": 5,
  "field_map": {
    "date": "Buchungsdatum",
    "amount": "Betrag",
    "description": "Verwendungszweck"
  },
  "date_format": "%d.%m.%Y",
  "decimal_separator": ","
}
```

**Response:**
```json
{
  "imported": 42,
  "duplicates": [
    { "date": "2026-01-15", "amount": "-45.00", "description": "Rewe" }
  ],
  "errors": [
    { "row": 7, "reason": "Ungültiges Datum: '32.01.2026'" }
  ]
}
```

**Duplikat-Erkennung:** Hash aus `(account_id, date, amount, description)`. Für OFX zusätzlich: `FITID` wird gegen eine `external_id`-Spalte in der `transactions`-Tabelle geprüft (neue optionale Spalte, nullable). Duplikate werden **nicht importiert**, aber in der Response unter `duplicates` gelistet.

**`transaction_type`-Ableitung:** Betrag > 0 → `income`, Betrag < 0 → `expense`. `category_id` wird aus dem Request übernommen (eine Standard-Kategorie für alle importierten Zeilen), kann `null` sein.

### Validierung

- `session_token` existiert und ist noch nicht abgelaufen → 400 sonst
- `account_id` gehört zum aktiven Haushalt → 403 sonst
- `field_map` enthält `date`, `amount`, `description` → 422 sonst
- Datei-Upload: max. 10 MB, nur `.csv`/`.ofx`/`.qfx` → 400 sonst

---

## 2. Parser

### Datei: `backend/app/services/import_parser.py`

#### CSV

- **Delimiter:** `csv.Sniffer` auf den ersten 4096 Bytes, Fallback `;`
- **Spalten-Auto-Mapping** via Keyword-Dict:
  - `date`: `["datum", "date", "buchungsdatum", "buchung", "wertstellung", "valuta"]`
  - `amount`: `["betrag", "amount", "umsatz", "wert", "summe"]`
  - `description`: `["verwendungszweck", "beschreibung", "description", "memo", "text", "buchungstext"]`
  - Case-insensitiv, Partial-Match
- **Datumsformat-Erkennung:** Kandidatenliste `["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%y"]`, erstes das auf mind. 80 % der Preview-Zeilen passt
- **Dezimaltrennzeichen:** prüft Betrags-Spalte: wenn `,` nach letztem `.` vorkommt → `,`, sonst `.`
- **Encoding:** UTF-8, Fallback UTF-8-BOM, Fallback Latin-1

#### OFX/QFX

- Regex extrahiert alle `<STMTTRN>…</STMTTRN>` Blöcke (auch SGML ohne schließende Tags)
- Felder pro Block:
  - `DTPOSTED` → date (Format `YYYYMMDDHHMMSS` oder `YYYYMMDD`)
  - `TRNAMT` → amount (Punkt als Dezimaltrenner)
  - `MEMO` → description (Fallback: `NAME`)
  - `FITID` → external_id für Duplikat-Check
- `transaction_type`: wie bei CSV aus Vorzeichen

---

## 3. Frontend

### Route & Navigation

- Route: `/import`
- Nav-Eintrag: "Import" nach "Berichte"
- Neue Datei: `frontend/js/views/import.js`

### Wizard-Schritte

**Schritt 1 — Upload** (Glassmorphism-Card)
- Dropzone: Drag & Drop + Klick, akzeptiert `.csv`, `.ofx`, `.qfx`
- Konto-Dropdown (aus `GET /accounts`, nur nicht-archivierte)
- "Datei importieren"-Button → `POST /import/parse`
- Fehler bei unbekanntem Format oder Parse-Fehler: Toast

**Schritt 2 — Mapping** (nur CSV; OFX/QFX überspringt direkt zu Schritt 3)
- Vorschau-Tabelle: erste 5 Zeilen
- Pro Pflichtfeld (Datum, Betrag, Beschreibung): Dropdown mit allen Spaltennamen, vorbelegt durch `suggested_mapping`
- Datum-Format-Input (Text), vorbelegt durch `detected_date_format`
- Dezimaltrennzeichen-Auswahl (`, ` / `.`), vorbelegt
- Optional: Standard-Kategorie-Dropdown (aus `GET /categories`, leer = unkategorisiert)
- "Importieren"-Button → `POST /import/confirm`

**Schritt 3 — Ergebnis**
- `X Transaktionen erfolgreich importiert`
- Falls Duplikate > 0: aufklappbare Liste (Datum, Betrag, Beschreibung), gelber Toast
- Falls Errors > 0: aufklappbare Liste (Zeile, Grund), roter Toast
- Buttons: "Zu Transaktionen" (→ `/transactions`) / "Neuen Import starten" (Reset Wizard)

### Ladezustand

- Upload/Parse: Spinner im Dropzone-Bereich
- Confirm/Import: Spinner auf dem Importieren-Button

---

## 4. i18n

Neue Keys in `i18n.js` für `de` und `en`:

| Key | DE | EN |
|-----|----|----|
| `nav.import` | Import | Import |
| `import.title` | Transaktionen importieren | Import Transactions |
| `import.step.upload` | Datei auswählen | Select File |
| `import.step.mapping` | Spalten zuordnen | Map Columns |
| `import.step.result` | Ergebnis | Result |
| `import.dropzone` | CSV, OFX oder QFX hier ablegen | Drop CSV, OFX or QFX here |
| `import.field.date` | Datum | Date |
| `import.field.amount` | Betrag | Amount |
| `import.field.description` | Beschreibung | Description |
| `import.field.category` | Standard-Kategorie (optional) | Default Category (optional) |
| `import.field.dateFormat` | Datumsformat | Date Format |
| `import.field.decimal` | Dezimaltrennzeichen | Decimal Separator |
| `import.result.imported` | Transaktionen importiert | transactions imported |
| `import.result.duplicates` | Duplikate gefunden | duplicates found |
| `import.result.errors` | Fehler | errors |
| `import.btn.import` | Importieren | Import |
| `import.btn.restart` | Neuen Import starten | Start New Import |

---

## 5. Fehlerbehandlung & Edge Cases

- Kein aktiver Haushalt → Toast + Redirect zu `/settings`
- Session-Token abgelaufen (> 10 Min): `/import/confirm` gibt 400, Frontend zeigt Toast "Sitzung abgelaufen, bitte erneut hochladen" und springt zu Schritt 1
- Datei > 10 MB → 400 mit klarer Meldung
- CSV mit nur einer Zeile (nur Header, keine Daten) → 422 `"Keine Datenzeilen gefunden"`
- OFX ohne `<STMTTRN>`-Blöcke → 422 `"Keine Transaktionen gefunden"`
- Betrag-Parsing-Fehler in einzelner Zeile → Zeile in `errors`-Liste, Import der restlichen Zeilen läuft weiter
- Datum-Parsing-Fehler → gleich wie Betrag-Fehler
- Alle Zeilen Duplikate → `imported: 0`, Duplikat-Liste, kein Fehler

---

## 6. DB-Änderung

Eine neue optionale Spalte `external_id TEXT NULL` in der `transactions`-Tabelle für OFX-FITID-Duplikat-Erkennung. Migration als `ALTER TABLE transactions ADD COLUMN external_id TEXT NULL`. Kein neues Modell, nur Ergänzung in `backend/app/models/transaction.py` und Schema.

---

## 7. Dateien

| Aktion | Pfad |
|--------|------|
| Neu | `backend/app/routers/import_.py` |
| Neu | `backend/app/schemas/import_.py` |
| Neu | `backend/app/services/import_parser.py` |
| Neu | `frontend/js/views/import.js` |
| Ändern | `backend/app/main.py` — Router einbinden |
| Ändern | `backend/app/models/transaction.py` — `external_id` Spalte |
| Ändern | `frontend/index.html` — neue Route |
| Ändern | `frontend/js/router.js` — Route `/import` |
| Ändern | `frontend/js/nav.js` — Nav-Eintrag |
| Ändern | `frontend/js/i18n.js` — neue Keys |
