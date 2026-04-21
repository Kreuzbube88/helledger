# HELLEDGER M2: Stammdaten — Design

## Goal

Alle Stammdaten-Modelle anlegen (Haushalte, Konten, Kategorien, Sollwerte, Budgets), vollständige CRUD-API, und vollständige Frontend-Seiten für Konten, Kategorien (inkl. Sollwert- und Budget-Editoren), sowie Haushalts-Verwaltung und -Umschaltung in der Navigation.

## Architecture

Approach: Backend first (Modelle → Migrations → APIs + Tests → Frontend).

Alle neuen Endpunkte lesen `active_household_id` aus dem eingeloggten User — kein `household_id`-Query-Parameter nötig. Eine einzige Alembic-Migration (`002_master_data.py`) erstellt alle neuen Tabellen.

---

## 1. Datenmodell

### Änderungen an `users`
- Neues Feld: `active_household_id` (Integer, FK → households.id, nullable, SET NULL on delete)

### `households`
| Feld | Typ | Notizen |
|------|-----|---------|
| id | Integer PK | |
| name | String(100) | |
| owner_id | FK → users.id | CASCADE delete |
| created_at | DateTime | |
| updated_at | DateTime | |

### `household_members`
| Feld | Typ | Notizen |
|------|-----|---------|
| id | Integer PK | |
| household_id | FK → households.id | CASCADE |
| user_id | FK → users.id | CASCADE |
| role | String(20) | `owner` / `member` |
| created_at | DateTime | |

Unique constraint: (household_id, user_id)

### `accounts`
| Feld | Typ | Notizen |
|------|-----|---------|
| id | Integer PK | |
| household_id | FK → households.id | CASCADE, indexed |
| name | String(100) | |
| account_type | String(20) | `checking` / `savings` / `credit` |
| starting_balance | Numeric(12,2) | |
| currency | String(3) | default `EUR` |
| archived | Boolean | default False |
| created_at | DateTime | |
| updated_at | DateTime | |

### `categories`
| Feld | Typ | Notizen |
|------|-----|---------|
| id | Integer PK | |
| household_id | FK → households.id | CASCADE, indexed |
| name | String(100) | |
| category_type | String(20) | `income` / `fixed` / `variable` |
| parent_id | FK → categories.id (self) | nullable, SET NULL on delete |
| color | String(7) | hex, nullable |
| icon | String(50) | nullable |
| archived | Boolean | default False |
| created_at | DateTime | |
| updated_at | DateTime | |

Indizes: household_id, parent_id

### `expected_values`
| Feld | Typ | Notizen |
|------|-----|---------|
| id | Integer PK | |
| household_id | FK → households.id | CASCADE, indexed |
| category_id | FK → categories.id | CASCADE, indexed |
| amount | Numeric(12,2) | |
| valid_from | Date | |
| valid_until | Date | nullable = unbegrenzt |
| created_at | DateTime | |

Business-Regel: Beim POST eines neuen Eintrags für eine Kategorie wird ein offener Eintrag (valid_until IS NULL) automatisch auf `valid_from - 1 Tag` gesetzt.

### `budgets`
Identische Struktur wie `expected_values`, gleiche Autoclose-Logik. Nur für `variable`-Kategorien sinnvoll, wird aber nicht serverseitig erzwungen.

---

## 2. Registrierungs-Erweiterung

Nach dem User-Insert in `POST /api/auth/register`:
1. Haushalt „Mein Haushalt" (wenn `language=de`) oder „My Household" (wenn `language=en`) anlegen
2. `household_members`-Eintrag mit `role=owner` anlegen
3. `users.active_household_id` auf die neue Haushalt-ID setzen

---

## 3. API

Alle Endpunkte: JWT-Auth required, Datenisolation via `active_household_id`.

### Households

| Method | Path | Beschreibung | Auth |
|--------|------|-------------|------|
| GET | /api/households | Alle Haushalte des Users | any |
| POST | /api/households | Neuen Haushalt anlegen | any |
| PATCH | /api/households/{id} | Umbenennen | owner only |
| DELETE | /api/households/{id} | Löschen (nicht den letzten) | owner only |
| POST | /api/households/{id}/activate | Aktiven Haushalt wechseln | member |
| GET | /api/households/{id}/members | Mitgliederliste | member |
| POST | /api/households/{id}/members | User per E-Mail hinzufügen (muss existieren) | owner |
| PATCH | /api/households/{id}/members/{user_id} | Rolle ändern | owner |
| DELETE | /api/households/{id}/members/{user_id} | Mitglied entfernen | owner |

### Accounts

| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | /api/accounts | Liste (aktiver Haushalt, optional ?include_archived=true) |
| POST | /api/accounts | Anlegen |
| GET | /api/accounts/{id} | Detail |
| PATCH | /api/accounts/{id} | Bearbeiten |
| DELETE | /api/accounts/{id} | Soft-Delete (setzt archived=true) |

### Categories

| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | /api/categories | Baum-Struktur (children-Array, verschachtelt) |
| POST | /api/categories | Anlegen |
| GET | /api/categories/{id} | Detail (flach) |
| PATCH | /api/categories/{id} | Bearbeiten inkl. parent_id-Änderung |
| DELETE | /api/categories/{id} | Soft-Delete |

`GET /api/categories` Response-Format:
```json
[
  {
    "id": 1, "name": "Fixkosten", "category_type": "fixed",
    "parent_id": null, "color": "#6366f1", "icon": null, "archived": false,
    "children": [
      { "id": 3, "name": "Miete", "category_type": "fixed", "parent_id": 1, "children": [] }
    ]
  }
]
```

### Expected Values

| Method | Path | Beschreibung |
|--------|------|-------------|
| GET | /api/expected-values | Liste, optional ?category_id= |
| POST | /api/expected-values | Anlegen + Autoclose |
| PATCH | /api/expected-values/{id} | Bearbeiten |
| DELETE | /api/expected-values/{id} | Löschen |

### Budgets

Identisch zu Expected Values unter `/api/budgets`.

### Schemas

- Money-Felder: `Decimal` im Python, JSON-Übertragung als `str` mit 2 Dezimalstellen (via `model_config = {"json_encoders": {Decimal: str}}`)
- Datumsfelder: `date` (ISO-8601 `YYYY-MM-DD`)
- Alle PATCH-Schemas: alle Felder optional

---

## 4. Frontend

### Navigation (angepasst)

Das M1-Dashboard-Header wird um folgendes erweitert:
- Haushalt-Dropdown: zeigt Haushaltsname, Klick öffnet Liste aller Haushalte, Auswahl ruft `POST /api/households/{id}/activate` → Seitenreload
- Nav-Links: Dashboard | Konten | Kategorien | Einstellungen

### `#/accounts`

- Tabelle: Name, Typ (Badge), Starting Balance, Währung, Status (Aktiv/Archiviert)
- „Konto hinzufügen"-Button → Modal
- Bearbeiten-Icon → Modal prefilled
- Archivieren-Button → `DELETE /api/accounts/{id}` (soft)
- Modal-Felder: Name (Text), Typ (Select: Girokonto/Sparkonto/Kreditkonto), Starting Balance (Number), Währung (Text, default EUR)

### `#/categories`

- Drei Sektionen: Einnahmen / Fixkosten / Variable
- Baum-Ansicht: aufklappbare Knoten, Einrückung für Sub-Kategorien
- Pro Kategorie-Zeile: Farb-Punkt, Name, aktuell gültiger Sollwert oder Budget, Aktionen (Bearbeiten, Sub-Kategorie hinzufügen, Archivieren)
- Aufklappbarer Sollwert-Editor (nur für `income`/`fixed`):
  - Tabelle aller `expected_values` für diese Kategorie (Betrag, Von, Bis)
  - „Neuen Sollwert setzen"-Button → Inline-Formular (Betrag, gültig ab)
- Aufklappbarer Budget-Editor (nur für `variable`):
  - Analog zum Sollwert-Editor
- Sub-Kategorie hinzufügen öffnet das gleiche Bearbeiten-Modal mit `parent_id` vorbelegt

### `#/settings` (neuer Tab: Haushalt)

- Haushalt-Name bearbeiten
- Mitgliederliste (Name, E-Mail, Rolle)
- „Mitglied hinzufügen" — E-Mail-Eingabe → `POST /api/households/{id}/members`
- Mitglied entfernen / Rolle ändern

### Routing

Neue Routen in `router.js`:
```javascript
route("#/accounts", renderAccounts);
route("#/categories", renderCategories);
route("#/settings", renderSettings);
```

Alle Views: ES-Module in `frontend/js/views/`. DOM-Manipulation ausschließlich via `textContent` für User-Daten.

---

## 5. Testing

**Neue Test-Dateien:**
- `tests/test_households.py` — Anlegen, Aktivieren, Mitglieder, Owner-Schutz, letzten Haushalt nicht löschbar
- `tests/test_accounts.py` — CRUD, Soft-Delete, Household-Isolation
- `tests/test_categories.py` — CRUD, Baum-Rückgabe, Sub-Kategorien, parent_id-Änderung
- `tests/test_expected_values.py` — Autoclose-Logik beim POST
- `tests/test_budgets.py` — analog

**Household-Isolation in jedem Test-File:** User A sieht keine Daten von User B / Haushalt B.

**conftest.py-Erweiterungen:**
- Fixture `registered_client` — registrierter User mit auto-erstelltem Haushalt, eingeloggt
- Fixture `second_user_client` — zweiter User mit eigenem Haushalt
- Helper `auth_headers(token)` — gibt `{"Authorization": f"Bearer {token}"}` zurück

**Ziel:** alle bestehenden 21 Tests bleiben grün + neue Tests für M2.
