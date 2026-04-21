# M4 Reporting & Charts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/reports` page with 4 Chart.js charts (donut, bar, line, horizontal bar), date-range/account filters, and PNG + CSV export.

**Architecture:** Backend: new `reports.py` router with 4 dedicated aggregation endpoints (no new DB models). Frontend: `reports.js` view with Chart.js via CDN, Cinema Dark + Glassmorphism design matching existing pages.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, Chart.js 4.x (CDN), vanilla JS (ES modules), Tailwind CSS (CDN)

---

### Task 1: Backend Schemas

**Files:**
- Create: `backend/app/schemas/reports.py`

- [ ] **Step 1: Write `reports.py` schemas**

```python
# backend/app/schemas/reports.py
from pydantic import BaseModel


class ExpensesByCategoryItem(BaseModel):
    category_id: int
    category_name: str
    total: str


class MonthlyTrendItem(BaseModel):
    year: int
    month: int
    income: str
    expenses: str


class BalanceHistoryItem(BaseModel):
    date: str
    balance: str
```

`SollIstNode` is already defined in `app.schemas.transaction` — reuse it, do not redefine.

- [ ] **Step 2: Verify import**

```bash
cd backend
python -c "from app.schemas.reports import ExpensesByCategoryItem, MonthlyTrendItem, BalanceHistoryItem; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/reports.py
git commit -m "feat: add report schemas"
```

---

### Task 2: Backend Router + Tests

**Files:**
- Create: `backend/app/routers/reports.py`
- Create: `backend/tests/test_reports.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_reports.py
import pytest


def _acc(client, name="Checking", starting_balance="0.00"):
    return client.post("/api/accounts", json={
        "name": name, "account_type": "checking",
        "starting_balance": starting_balance, "currency": "EUR",
    }).json()


def _cat(client, name="Food", category_type="variable"):
    return client.post("/api/categories", json={"name": name, "category_type": category_type}).json()


def _tx(client, **kwargs):
    defaults = {
        "account_id": None, "category_id": None,
        "amount": "50.00", "date": "2026-04-01",
        "description": "Test", "transaction_type": "expense",
    }
    defaults.update(kwargs)
    return client.post("/api/transactions", json=defaults)


def test_expenses_by_category(registered_client):
    acc = _acc(registered_client)
    food = _cat(registered_client, "Food")
    rent = _cat(registered_client, "Rent", "fixed")
    _tx(registered_client, account_id=acc["id"], category_id=food["id"],
        amount="200.00", transaction_type="expense", date="2026-03-10")
    _tx(registered_client, account_id=acc["id"], category_id=food["id"],
        amount="100.00", transaction_type="expense", date="2026-03-20")
    _tx(registered_client, account_id=acc["id"], category_id=rent["id"],
        amount="800.00", transaction_type="expense", date="2026-03-01")
    inc_cat = _cat(registered_client, "Salary", "income")
    _tx(registered_client, account_id=acc["id"], category_id=inc_cat["id"],
        amount="3000.00", transaction_type="income", date="2026-03-25")

    r = registered_client.get(
        "/api/reports/expenses-by-category?from_date=2026-03-01&to_date=2026-03-31"
    )
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    totals = {i["category_name"]: i["total"] for i in items}
    assert totals["Food"] == "300.00"
    assert totals["Rent"] == "800.00"


def test_expenses_by_category_account_filter(registered_client):
    acc1 = _acc(registered_client, "A1")
    acc2 = _acc(registered_client, "A2")
    cat = _cat(registered_client)
    _tx(registered_client, account_id=acc1["id"], category_id=cat["id"],
        amount="100.00", transaction_type="expense", date="2026-03-01")
    _tx(registered_client, account_id=acc2["id"], category_id=cat["id"],
        amount="200.00", transaction_type="expense", date="2026-03-01")

    r = registered_client.get(
        f"/api/reports/expenses-by-category?from_date=2026-03-01&to_date=2026-03-31&account_id={acc1['id']}"
    )
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["total"] == "100.00"


def test_expenses_by_category_invalid_dates(registered_client):
    r = registered_client.get(
        "/api/reports/expenses-by-category?from_date=2026-04-30&to_date=2026-04-01"
    )
    assert r.status_code == 400


def test_monthly_trend(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client)
    inc_cat = _cat(registered_client, "Salary", "income")
    _tx(registered_client, account_id=acc["id"], category_id=inc_cat["id"],
        amount="2000.00", transaction_type="income", date="2026-01-15")
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="500.00", transaction_type="expense", date="2026-01-20")
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="600.00", transaction_type="expense", date="2026-02-10")

    r = registered_client.get(
        "/api/reports/monthly-trend?from_date=2026-01-01&to_date=2026-02-28"
    )
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 2
    jan = next(m for m in items if m["month"] == 1)
    assert jan["income"] == "2000.00"
    assert jan["expenses"] == "500.00"
    feb = next(m for m in items if m["month"] == 2)
    assert feb["income"] == "0.00"
    assert feb["expenses"] == "600.00"


def test_balance_history(registered_client):
    acc = _acc(registered_client, "Main", "1000.00")
    cat = _cat(registered_client)
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="200.00", transaction_type="expense", date="2026-03-01")
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="100.00", transaction_type="expense", date="2026-04-05")

    r = registered_client.get(
        f"/api/reports/balance-history?from_date=2026-04-01&to_date=2026-04-05&account_id={acc['id']}"
    )
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 5
    assert items[0]["balance"] == "800.00"  # April 1: 1000 - 200 pre-range
    assert items[4]["balance"] == "700.00"  # April 5: -100


def test_balance_history_requires_account_id(registered_client):
    r = registered_client.get(
        "/api/reports/balance-history?from_date=2026-04-01&to_date=2026-04-30"
    )
    assert r.status_code == 422


def test_balance_history_wrong_household(registered_client, second_user_client):
    acc = _acc(registered_client, "Mine")
    r = second_user_client.get(
        f"/api/reports/balance-history?from_date=2026-04-01&to_date=2026-04-30&account_id={acc['id']}"
    )
    assert r.status_code == 404


def test_reports_soll_ist_scales_by_months(registered_client):
    acc = _acc(registered_client)
    cat = _cat(registered_client, "Food")
    registered_client.post("/api/budgets", json={
        "category_id": cat["id"], "amount": "300.00", "valid_from": "2026-01-01",
    })
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="120.00", transaction_type="expense", date="2026-04-05")
    _tx(registered_client, account_id=acc["id"], category_id=cat["id"],
        amount="80.00", transaction_type="expense", date="2026-05-10")

    r = registered_client.get(
        "/api/reports/soll-ist?from_date=2026-04-01&to_date=2026-05-31"
    )
    assert r.status_code == 200
    nodes = r.json()
    node = next(n for n in nodes if n["id"] == cat["id"])
    assert node["soll"] == "600.00"   # 300 * 2 months
    assert node["ist"] == "-200.00"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend
pytest tests/test_reports.py -v
```

Expected: `ERROR` or `ImportError` — router not yet registered.

- [ ] **Step 3: Implement the router**

```python
# backend/app/routers/reports.py
from datetime import date as date_type, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, extract, func, or_
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models.household import Account, Budget, Category, ExpectedValue
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.reports import BalanceHistoryItem, ExpensesByCategoryItem, MonthlyTrendItem
from app.schemas.transaction import SollIstNode

router = APIRouter(prefix="/reports", tags=["reports"])


def _require_active_hh(user: User) -> int:
    if user.active_household_id is None:
        raise HTTPException(status_code=400, detail="no_active_household")
    return user.active_household_id


def _validate_dates(from_date: date_type, to_date: date_type) -> None:
    if from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date_after_to_date")


@router.get("/expenses-by-category", response_model=list[ExpensesByCategoryItem])
async def expenses_by_category(
    from_date: date_type = Query(...),
    to_date: date_type = Query(...),
    account_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    _validate_dates(from_date, to_date)
    q = (
        db.query(
            Transaction.category_id,
            Category.name.label("category_name"),
            func.abs(func.sum(Transaction.amount)).label("total"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.household_id == hh_id,
            Transaction.date >= from_date,
            Transaction.date <= to_date,
            Transaction.transaction_type == "expense",
        )
    )
    if account_id is not None:
        q = q.filter(Transaction.account_id == account_id)
    rows = (
        q.group_by(Transaction.category_id, Category.name)
        .order_by(func.abs(func.sum(Transaction.amount)).desc())
        .all()
    )
    return [
        ExpensesByCategoryItem(
            category_id=r.category_id,
            category_name=r.category_name,
            total=f"{r.total:.2f}",
        )
        for r in rows
    ]


@router.get("/monthly-trend", response_model=list[MonthlyTrendItem])
async def monthly_trend(
    from_date: date_type = Query(...),
    to_date: date_type = Query(...),
    account_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    _validate_dates(from_date, to_date)
    income_col = func.sum(
        case((Transaction.transaction_type == "income", Transaction.amount), else_=0)
    )
    expense_col = func.abs(
        func.sum(
            case((Transaction.transaction_type == "expense", Transaction.amount), else_=0)
        )
    )
    q = (
        db.query(
            extract("year", Transaction.date).label("year"),
            extract("month", Transaction.date).label("month"),
            income_col.label("income"),
            expense_col.label("expenses"),
        )
        .filter(
            Transaction.household_id == hh_id,
            Transaction.date >= from_date,
            Transaction.date <= to_date,
            Transaction.transaction_type.in_(["income", "expense"]),
        )
    )
    if account_id is not None:
        q = q.filter(Transaction.account_id == account_id)
    rows = q.group_by("year", "month").order_by("year", "month").all()
    return [
        MonthlyTrendItem(
            year=int(r.year),
            month=int(r.month),
            income=f"{r.income or Decimal('0'):.2f}",
            expenses=f"{r.expenses or Decimal('0'):.2f}",
        )
        for r in rows
    ]


@router.get("/balance-history", response_model=list[BalanceHistoryItem])
async def balance_history(
    from_date: date_type = Query(...),
    to_date: date_type = Query(...),
    account_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    _validate_dates(from_date, to_date)
    acc = db.get(Account, account_id)
    if acc is None or acc.household_id != hh_id:
        raise HTTPException(status_code=404, detail="not_found")

    pre_sum = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.account_id == account_id, Transaction.date < from_date)
        .scalar()
    ) or Decimal("0")
    running = (acc.starting_balance or Decimal("0")) + pre_sum

    use_weekly = (to_date - from_date).days > 365

    if use_weekly:
        rows = (
            db.query(
                func.strftime("%Y-%W", Transaction.date).label("week"),
                func.sum(Transaction.amount).label("total"),
            )
            .filter(
                Transaction.account_id == account_id,
                Transaction.date >= from_date,
                Transaction.date <= to_date,
            )
            .group_by("week")
            .order_by("week")
            .all()
        )
        result = []
        for r in rows:
            running += r.total or Decimal("0")
            result.append(BalanceHistoryItem(date=r.week, balance=f"{running:.2f}"))
        return result

    tx_rows = (
        db.query(
            Transaction.date.label("day"),
            func.sum(Transaction.amount).label("total"),
        )
        .filter(
            Transaction.account_id == account_id,
            Transaction.date >= from_date,
            Transaction.date <= to_date,
        )
        .group_by(Transaction.date)
        .order_by(Transaction.date)
        .all()
    )
    tx_map: dict[str, Decimal] = {
        str(r.day): r.total or Decimal("0") for r in tx_rows
    }
    result = []
    current = from_date
    while current <= to_date:
        running += tx_map.get(str(current), Decimal("0"))
        result.append(BalanceHistoryItem(date=str(current), balance=f"{running:.2f}"))
        current += timedelta(days=1)
    return result


@router.get("/soll-ist", response_model=list[SollIstNode])
async def reports_soll_ist(
    from_date: date_type = Query(...),
    to_date: date_type = Query(...),
    account_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    hh_id = _require_active_hh(user)
    _validate_dates(from_date, to_date)
    months_in_range = (
        (to_date.year - from_date.year) * 12 + to_date.month - from_date.month + 1
    )
    cats = db.query(Category).filter(
        Category.household_id == hh_id,
        Category.archived.is_(False),
    ).all()
    if not cats:
        return []
    cat_ids = [c.id for c in cats]

    tx_q = (
        db.query(Transaction.category_id, func.sum(Transaction.amount))
        .filter(
            Transaction.household_id == hh_id,
            Transaction.date >= from_date,
            Transaction.date <= to_date,
            Transaction.transaction_type.in_(["income", "expense"]),
            Transaction.category_id.isnot(None),
        )
    )
    if account_id is not None:
        tx_q = tx_q.filter(Transaction.account_id == account_id)
    tx_map: dict[int, Decimal] = {
        cat_id: amt for cat_id, amt in tx_q.group_by(Transaction.category_id).all()
    }

    ev_rows = db.query(ExpectedValue).filter(
        ExpectedValue.category_id.in_(cat_ids),
        ExpectedValue.valid_from <= from_date,
        or_(ExpectedValue.valid_until.is_(None), ExpectedValue.valid_until >= from_date),
    ).all()
    ev_map: dict[int, Decimal] = {ev.category_id: ev.amount for ev in ev_rows}

    budget_rows = db.query(Budget).filter(
        Budget.category_id.in_(cat_ids),
        Budget.valid_from <= from_date,
        or_(Budget.valid_until.is_(None), Budget.valid_until >= from_date),
    ).all()
    budget_map: dict[int, Decimal] = {b.category_id: b.amount for b in budget_rows}

    def _build(parent_id: int | None) -> list[SollIstNode]:
        result = []
        for cat in cats:
            if cat.parent_id != parent_id:
                continue
            children = _build(cat.id)
            ist_self = tx_map.get(cat.id, Decimal("0"))
            ist_children = sum(Decimal(c.ist) for c in children)
            ist = ist_self + ist_children
            monthly_soll = ev_map.get(cat.id) or budget_map.get(cat.id) or Decimal("0")
            soll_self = monthly_soll * months_in_range
            soll_children = sum(Decimal(c.soll) for c in children)
            soll = soll_self if soll_self > Decimal("0") else soll_children
            result.append(
                SollIstNode(
                    id=cat.id,
                    name=cat.name,
                    category_type=cat.category_type,
                    soll=f"{soll:.2f}",
                    ist=f"{ist:.2f}",
                    diff=f"{soll - ist:.2f}",
                    children=children,
                )
            )
        return result

    return _build(None)
```

- [ ] **Step 4: Register router in `main.py`**

Add after `from app.routers import transactions as tx_router`:

```python
from app.routers import reports as reports_router
```

Add after `app.include_router(tx_router.router, prefix="/api")`:

```python
app.include_router(reports_router.router, prefix="/api")
```

- [ ] **Step 5: Run all tests**

```bash
cd backend
pytest tests/test_reports.py -v
```

Expected: all 9 tests pass.

Also run the full suite to check for regressions:

```bash
pytest -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/reports.py backend/tests/test_reports.py backend/app/main.py
git commit -m "feat: add reports router with 4 aggregation endpoints"
```

---

### Task 3: i18n Locale Files

**Files:**
- Modify: `frontend/locales/de.json`
- Modify: `frontend/locales/en.json`

- [ ] **Step 1: Add keys to `de.json`**

Add `"reports"` key to the nav object (between `"transactions"` and `"settings"`):

```json
"nav": {
    "dashboard": "Dashboard",
    "accounts": "Konten",
    "categories": "Kategorien",
    "transactions": "Transaktionen",
    "reports": "Berichte",
    "settings": "Einstellungen",
    "logout": "Abmelden"
}
```

Add new top-level `"reports"` object (before the final `}` of the JSON file, after `"settings"`):

```json
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
    "export": { "png": "PNG herunterladen", "csv": "CSV herunterladen", "all": "Alle Charts (PNG)" },
    "noData": "Keine Daten für diesen Zeitraum",
    "selectAccount": "Bitte ein Konto auswählen"
}
```

- [ ] **Step 2: Add keys to `en.json`**

Add `"reports"` to nav object:

```json
"nav": {
    "dashboard": "Dashboard",
    "accounts": "Accounts",
    "categories": "Categories",
    "transactions": "Transactions",
    "reports": "Reports",
    "settings": "Settings",
    "logout": "Sign Out"
}
```

Add top-level `"reports"` object:

```json
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
    "export": { "png": "Download PNG", "csv": "Download CSV", "all": "All Charts (PNG)" },
    "noData": "No data for this period",
    "selectAccount": "Please select an account"
}
```

- [ ] **Step 3: Validate JSON syntax**

```bash
python -c "import json; json.load(open('frontend/locales/de.json')); json.load(open('frontend/locales/en.json')); print('ok')"
```

Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add frontend/locales/de.json frontend/locales/en.json
git commit -m "feat: add M4 i18n keys for reports page"
```

---

### Task 4: Frontend Wiring (Nav + Route)

**Files:**
- Modify: `frontend/js/nav.js`
- Modify: `frontend/index.html`

- [ ] **Step 1: Add "reports" to nav links in `nav.js`**

Current line 45:

```javascript
const navLinks = ["dashboard", "accounts", "categories", "transactions", "settings"].map((page) => {
```

Replace with:

```javascript
const navLinks = ["dashboard", "accounts", "categories", "transactions", "reports", "settings"].map((page) => {
```

- [ ] **Step 2: Add Chart.js CDN to `index.html`**

Add after the i18next `<script>` tag (line 60) and before the module script:

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
```

- [ ] **Step 3: Add reports import and route to `index.html`**

In the module script, add import after the transactions import:

```javascript
import { renderReports } from "/js/views/reports.js";
```

Add route after `route("#/transactions", renderTransactions);`:

```javascript
route("#/reports", renderReports);
```

- [ ] **Step 4: Commit**

```bash
git add frontend/js/nav.js frontend/index.html
git commit -m "feat: wire reports route and Chart.js CDN"
```

---

### Task 5: Frontend Reports View

**Files:**
- Create: `frontend/js/views/reports.js`

- [ ] **Step 1: Create `reports.js`**

Important: use `el.replaceChildren()` to clear DOM nodes — never `el.innerHTML = ""`. The existing views use `container.textContent = ""` or DOM methods.

```javascript
// frontend/js/views/reports.js
import { getCurrentUser } from "../auth.js";
import { navigate } from "../router.js";
import { renderNav } from "../nav.js";
import { api } from "../api.js";
import { toast } from "../toast.js";
import { fadeInUp } from "../animations.js";

const DONUT_COLORS = [
    "#6366f1", "#10b981", "#f59e0b", "#3b82f6",
    "#ec4899", "#8b5cf6", "#14b8a6", "#f97316",
];

let _state = {
    mode: "month",
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    fromDate: null,
    toDate: null,
    accountId: null,
    accounts: [],
    charts: {},
    lastData: {},
};

function _isoDate(y, m, d) {
    return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

function _lastDayOfMonth(y, m) {
    return new Date(y, m, 0).getDate();
}

function _buildDateRange() {
    if (_state.mode === "month") {
        return {
            from_date: _isoDate(_state.year, _state.month, 1),
            to_date: _isoDate(_state.year, _state.month, _lastDayOfMonth(_state.year, _state.month)),
        };
    }
    if (_state.mode === "year") {
        return { from_date: `${_state.year}-01-01`, to_date: `${_state.year}-12-31` };
    }
    return { from_date: _state.fromDate, to_date: _state.toDate };
}

function _buildQs() {
    const { from_date, to_date } = _buildDateRange();
    const p = new URLSearchParams({ from_date, to_date });
    if (_state.accountId) p.set("account_id", String(_state.accountId));
    return p.toString();
}

function _destroyCharts() {
    for (const c of Object.values(_state.charts)) { if (c) c.destroy(); }
    _state.charts = {};
}

function _setChartDefaults() {
    if (!window.Chart) return;
    Chart.defaults.color = "#94a3b8";
    Chart.defaults.borderColor = "rgba(255,255,255,0.06)";
    Chart.defaults.font.family = "inherit";
}

function _showNoData(canvas) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#475569";
    ctx.font = "14px inherit";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(t("reports.noData"), canvas.width / 2, canvas.height / 2);
}

function _renderDonut(canvas, data) {
    if (_state.charts.donut) { _state.charts.donut.destroy(); delete _state.charts.donut; }
    if (!data || data.length === 0) { _showNoData(canvas); return; }
    _state.lastData["expenses-by-category"] = data;
    _state.charts.donut = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: data.map((d) => d.category_name),
            datasets: [{
                data: data.map((d) => parseFloat(d.total)),
                backgroundColor: data.map((_, i) => DONUT_COLORS[i % DONUT_COLORS.length]),
                borderWidth: 0,
                hoverOffset: 8,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: "right", labels: { boxWidth: 12, padding: 16 } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toFixed(2)} \u20ac`,
                    },
                },
            },
        },
    });
}

function _renderMonthlyTrend(canvas, data) {
    if (_state.charts.trend) { _state.charts.trend.destroy(); delete _state.charts.trend; }
    if (!data || data.length === 0) { _showNoData(canvas); return; }
    _state.lastData["monthly-trend"] = data;
    const lang = document.documentElement.lang === "de" ? "de-DE" : "en-US";
    const labels = data.map((d) =>
        new Date(d.year, d.month - 1, 1).toLocaleDateString(lang, { month: "short", year: "2-digit" })
    );
    _state.charts.trend = new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: t("dashboard.income"),
                    data: data.map((d) => parseFloat(d.income)),
                    backgroundColor: "rgba(16,185,129,0.7)",
                    borderColor: "#10b981",
                    borderWidth: 1,
                    borderRadius: 4,
                },
                {
                    label: t("dashboard.expenses"),
                    data: data.map((d) => parseFloat(d.expenses)),
                    backgroundColor: "rgba(244,63,94,0.7)",
                    borderColor: "#f43f5e",
                    borderWidth: 1,
                    borderRadius: 4,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: { legend: { position: "top" } },
            scales: {
                x: { grid: { color: "rgba(255,255,255,0.04)" } },
                y: { grid: { color: "rgba(255,255,255,0.04)" }, beginAtZero: true },
            },
        },
    });
}

function _renderBalanceHistory(canvas, data) {
    if (_state.charts.balance) { _state.charts.balance.destroy(); delete _state.charts.balance; }
    if (!data || data.length === 0) { _showNoData(canvas); return; }
    _state.lastData["balance-history"] = data;
    _state.charts.balance = new Chart(canvas, {
        type: "line",
        data: {
            labels: data.map((d) => d.date),
            datasets: [{
                label: t("reports.chart.balanceHistory"),
                data: data.map((d) => parseFloat(d.balance)),
                borderColor: "#6366f1",
                backgroundColor: "rgba(99,102,241,0.12)",
                fill: true,
                tension: 0.3,
                pointRadius: data.length > 60 ? 0 : 3,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    grid: { color: "rgba(255,255,255,0.04)" },
                    ticks: { maxTicksLimit: 8 },
                },
                y: { grid: { color: "rgba(255,255,255,0.04)" } },
            },
        },
    });
}

function _renderSollIst(canvas, data) {
    if (_state.charts.sollIst) { _state.charts.sollIst.destroy(); delete _state.charts.sollIst; }
    const flat = (data || []).filter(
        (n) => parseFloat(n.soll) !== 0 || parseFloat(n.ist) !== 0
    );
    if (flat.length === 0) { _showNoData(canvas); return; }
    _state.lastData["soll-ist"] = data;
    _state.charts.sollIst = new Chart(canvas, {
        type: "bar",
        data: {
            labels: flat.map((n) => n.name),
            datasets: [
                {
                    label: t("dashboard.soll"),
                    data: flat.map((n) => parseFloat(n.soll)),
                    backgroundColor: "rgba(99,102,241,0.6)",
                    borderColor: "#6366f1",
                    borderWidth: 1,
                    borderRadius: 4,
                },
                {
                    label: t("dashboard.ist"),
                    data: flat.map((n) => Math.abs(parseFloat(n.ist))),
                    backgroundColor: "rgba(16,185,129,0.6)",
                    borderColor: "#10b981",
                    borderWidth: 1,
                    borderRadius: 4,
                },
            ],
        },
        options: {
            indexAxis: "y",
            responsive: true,
            plugins: { legend: { position: "top" } },
            scales: {
                x: { grid: { color: "rgba(255,255,255,0.04)" }, beginAtZero: true },
                y: { grid: { color: "rgba(255,255,255,0.04)" } },
            },
        },
    });
}

async function _loadAllCharts() {
    const { from_date, to_date } = _buildDateRange();
    if (!from_date || !to_date || from_date > to_date) return;

    const qs = _buildQs();
    const [catRes, trendRes, sollIstRes] = await Promise.all([
        api.get(`/reports/expenses-by-category?${qs}`),
        api.get(`/reports/monthly-trend?${qs}`),
        api.get(`/reports/soll-ist?${qs}`),
    ]);

    if (catRes.ok) _renderDonut(document.getElementById("canvas-donut"), await catRes.json());
    else toast(t("errors.generic"), "error");

    if (trendRes.ok) _renderMonthlyTrend(document.getElementById("canvas-trend"), await trendRes.json());
    else toast(t("errors.generic"), "error");

    if (sollIstRes.ok) _renderSollIst(document.getElementById("canvas-sollist"), await sollIstRes.json());
    else toast(t("errors.generic"), "error");

    const balCanvas = document.getElementById("canvas-balance");
    const balPlaceholder = document.getElementById("balance-placeholder");

    if (_state.accountId) {
        balCanvas.style.display = "";
        if (balPlaceholder) balPlaceholder.style.display = "none";
        const balRes = await api.get(
            `/reports/balance-history?from_date=${from_date}&to_date=${to_date}&account_id=${_state.accountId}`
        );
        if (balRes.ok) _renderBalanceHistory(balCanvas, await balRes.json());
        else toast(t("errors.generic"), "error");
    } else {
        if (_state.charts.balance) { _state.charts.balance.destroy(); delete _state.charts.balance; }
        balCanvas.style.display = "none";
        if (balPlaceholder) balPlaceholder.style.display = "";
    }
}

function _downloadPng(chartKey, filename) {
    const chart = _state.charts[chartKey];
    if (!chart) return;
    const a = document.createElement("a");
    a.href = chart.canvas.toDataURL("image/png");
    a.download = filename;
    a.click();
}

function _downloadCsv(dataKey, filename) {
    const raw = _state.lastData[dataKey];
    if (!raw) return;
    let rows = raw;
    if (dataKey === "soll-ist") {
        function flatten(nodes) {
            return nodes.flatMap((n) => [
                { id: n.id, name: n.name, category_type: n.category_type, soll: n.soll, ist: n.ist, diff: n.diff },
                ...flatten(n.children || []),
            ]);
        }
        rows = flatten(raw);
    }
    if (!rows.length) return;
    const headers = Object.keys(rows[0]).join(",");
    const body = rows.map((r) => Object.values(r).map((v) => `"${v}"`).join(",")).join("\n");
    const blob = new Blob([headers + "\n" + body], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
}

function _exportBtn(label, onClick) {
    const btn = document.createElement("button");
    btn.textContent = label;
    btn.className = "text-xs text-gray-400 hover:text-indigo-400 transition-colors";
    btn.addEventListener("click", onClick);
    return btn;
}

function _chartCard(canvasId, titleKey, placeholderId) {
    const chartKeyMap = {
        "canvas-donut": "donut",
        "canvas-trend": "trend",
        "canvas-balance": "balance",
        "canvas-sollist": "sollIst",
    };
    const dataKeyMap = {
        "canvas-donut": "expenses-by-category",
        "canvas-trend": "monthly-trend",
        "canvas-balance": "balance-history",
        "canvas-sollist": "soll-ist",
    };
    const chartKey = chartKeyMap[canvasId];
    const dataKey = dataKeyMap[canvasId];

    const card = document.createElement("div");
    card.className = "glass rounded-2xl p-6 flex flex-col gap-3";

    const header = document.createElement("div");
    header.className = "flex items-center justify-between";

    const title = document.createElement("h3");
    title.className = "text-xs font-semibold text-gray-400 uppercase tracking-wider";
    title.textContent = t(titleKey);
    header.appendChild(title);

    const exportWrap = document.createElement("div");
    exportWrap.className = "flex gap-3";
    exportWrap.appendChild(_exportBtn(t("reports.export.png"), () => _downloadPng(chartKey, `${dataKey}.png`)));
    exportWrap.appendChild(_exportBtn(t("reports.export.csv"), () => _downloadCsv(dataKey, `${dataKey}.csv`)));
    header.appendChild(exportWrap);
    card.appendChild(header);

    if (placeholderId) {
        const placeholder = document.createElement("div");
        placeholder.id = placeholderId;
        placeholder.className = "flex items-center justify-center h-40 text-gray-500 text-sm";
        placeholder.textContent = t("reports.selectAccount");
        placeholder.style.display = _state.accountId ? "none" : "";
        card.appendChild(placeholder);
    }

    const canvas = document.createElement("canvas");
    canvas.id = canvasId;
    if (placeholderId) canvas.style.display = _state.accountId ? "" : "none";
    card.appendChild(canvas);

    return card;
}

function _renderPickers(wrap) {
    wrap.replaceChildren();
    const lang = document.documentElement.lang === "de" ? "de-DE" : "en-US";

    if (_state.mode === "month") {
        const mSel = document.createElement("select");
        mSel.className = "bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300";
        for (let m = 1; m <= 12; m++) {
            const opt = document.createElement("option");
            opt.value = String(m);
            opt.textContent = new Date(2000, m - 1, 1).toLocaleDateString(lang, { month: "long" });
            opt.selected = m === _state.month;
            mSel.appendChild(opt);
        }
        mSel.addEventListener("change", () => { _state.month = parseInt(mSel.value); _loadAllCharts(); });
        wrap.appendChild(mSel);
    }

    if (_state.mode === "month" || _state.mode === "year") {
        const ySel = document.createElement("select");
        ySel.className = "bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300";
        const curYear = new Date().getFullYear();
        for (let y = curYear - 2; y <= curYear + 1; y++) {
            const opt = document.createElement("option");
            opt.value = String(y);
            opt.textContent = String(y);
            opt.selected = y === _state.year;
            ySel.appendChild(opt);
        }
        ySel.addEventListener("change", () => { _state.year = parseInt(ySel.value); _loadAllCharts(); });
        wrap.appendChild(ySel);
    }

    if (_state.mode === "custom") {
        if (!_state.fromDate) _state.fromDate = _isoDate(_state.year, _state.month, 1);
        if (!_state.toDate) _state.toDate = _isoDate(_state.year, _state.month, _lastDayOfMonth(_state.year, _state.month));

        const fromIn = document.createElement("input");
        fromIn.type = "date";
        fromIn.className = "bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300";
        fromIn.value = _state.fromDate;

        const sep = document.createElement("span");
        sep.className = "text-gray-500 text-sm";
        sep.textContent = "\u2192";

        const toIn = document.createElement("input");
        toIn.type = "date";
        toIn.className = "bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300";
        toIn.value = _state.toDate;

        function onDateChange() {
            if (fromIn.value && toIn.value && fromIn.value <= toIn.value) {
                _state.fromDate = fromIn.value;
                _state.toDate = toIn.value;
                _loadAllCharts();
            }
        }
        fromIn.addEventListener("change", onDateChange);
        toIn.addEventListener("change", onDateChange);
        wrap.appendChild(fromIn);
        wrap.appendChild(sep);
        wrap.appendChild(toIn);
    }
}

export async function renderReports() {
    const user = getCurrentUser();
    if (!user) { navigate("#/login"); return; }

    _destroyCharts();
    _state.lastData = {};

    const app = document.getElementById("app");
    app.replaceChildren();

    const navContainer = document.createElement("div");
    app.appendChild(navContainer);
    await renderNav(navContainer);

    const accRes = await api.get("/accounts");
    if (!accRes.ok) { navigate("#/settings"); return; }
    _state.accounts = await accRes.json();

    const main = document.createElement("main");
    main.className = "relative z-10 max-w-screen-xl mx-auto px-4 py-8 space-y-6";

    const pageTitle = document.createElement("h1");
    pageTitle.className = "text-2xl font-bold text-white";
    pageTitle.textContent = t("reports.title");
    main.appendChild(pageTitle);

    // Filter bar
    const filterCard = document.createElement("div");
    filterCard.className = "glass rounded-2xl p-4 flex flex-wrap items-center gap-4";

    const modeWrap = document.createElement("div");
    modeWrap.className = "flex rounded-lg overflow-hidden border border-gray-700";
    const MODES = ["month", "year", "custom"];
    const MODE_KEYS = {
        month: "reports.period.month",
        year: "reports.period.year",
        custom: "reports.period.custom",
    };
    const modeBtns = [];
    MODES.forEach((mode) => {
        const btn = document.createElement("button");
        btn.className = `px-4 py-2 text-sm transition-colors ${_state.mode === mode ? "bg-indigo-600 text-white" : "bg-transparent text-gray-400 hover:text-white"}`;
        btn.textContent = t(MODE_KEYS[mode]);
        btn.addEventListener("click", () => {
            _state.mode = mode;
            modeBtns.forEach((b, i) => {
                b.className = `px-4 py-2 text-sm transition-colors ${MODES[i] === mode ? "bg-indigo-600 text-white" : "bg-transparent text-gray-400 hover:text-white"}`;
            });
            _renderPickers(pickerWrap);
            _loadAllCharts();
        });
        modeBtns.push(btn);
        modeWrap.appendChild(btn);
    });
    filterCard.appendChild(modeWrap);

    const pickerWrap = document.createElement("div");
    pickerWrap.className = "flex items-center gap-2";
    filterCard.appendChild(pickerWrap);

    const accSel = document.createElement("select");
    accSel.className = "bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-300 ml-auto";
    const allOpt = document.createElement("option");
    allOpt.value = "";
    allOpt.textContent = t("reports.filter.allAccounts");
    accSel.appendChild(allOpt);
    _state.accounts.forEach((acc) => {
        const opt = document.createElement("option");
        opt.value = String(acc.id);
        opt.textContent = acc.name;
        accSel.appendChild(opt);
    });
    accSel.addEventListener("change", () => {
        _state.accountId = accSel.value ? parseInt(accSel.value) : null;
        const balCanvas = document.getElementById("canvas-balance");
        const balPh = document.getElementById("balance-placeholder");
        if (balCanvas) balCanvas.style.display = _state.accountId ? "" : "none";
        if (balPh) balPh.style.display = _state.accountId ? "none" : "";
        _loadAllCharts();
    });
    filterCard.appendChild(accSel);

    const dlAllBtn = document.createElement("button");
    dlAllBtn.textContent = t("reports.export.all");
    dlAllBtn.className = "text-sm text-gray-400 hover:text-indigo-400 transition-colors border border-gray-700 rounded-lg px-3 py-2";
    dlAllBtn.addEventListener("click", () => {
        [
            ["donut", "expenses-by-category.png"],
            ["trend", "monthly-trend.png"],
            ["balance", "balance-history.png"],
            ["sollIst", "soll-ist.png"],
        ].forEach(([key, name]) => _downloadPng(key, name));
    });
    filterCard.appendChild(dlAllBtn);

    main.appendChild(filterCard);

    const grid = document.createElement("div");
    grid.className = "grid grid-cols-1 md:grid-cols-2 gap-6";
    grid.appendChild(_chartCard("canvas-donut", "reports.chart.expensesByCategory"));
    grid.appendChild(_chartCard("canvas-trend", "reports.chart.monthlyTrend"));
    grid.appendChild(_chartCard("canvas-balance", "reports.chart.balanceHistory", "balance-placeholder"));
    grid.appendChild(_chartCard("canvas-sollist", "reports.chart.sollIst"));
    main.appendChild(grid);

    app.appendChild(main);

    _setChartDefaults();
    _renderPickers(pickerWrap);
    await _loadAllCharts();
    fadeInUp(main);
}
```

- [ ] **Step 2: Start the dev server**

```bash
cd backend
uvicorn app.main:app --reload --port 3000
```

Open http://localhost:3000 in the browser.

- [ ] **Step 3: Manual browser tests**

Verify the following:

1. Navigate to `#/reports` — page renders with nav, filter bar, 4 chart cards
2. Default state (current month, all accounts): 3 charts render data; balance card shows "Bitte ein Konto auswählen"
3. Switch to "Jahr" — year picker only, charts reload
4. Switch to "Frei" — two date inputs appear; valid range reloads charts
5. Select a specific account — balance history chart renders
6. "PNG herunterladen" on a chart downloads a PNG file
7. "CSV herunterladen" downloads a CSV file with the chart data
8. "Alle Charts (PNG)" downloads active charts as PNGs
9. Nav shows "Berichte"/"Reports" between "Transaktionen" and "Einstellungen"
10. "Berichte" link is highlighted (white + font-medium) when on the reports page

- [ ] **Step 4: Commit**

```bash
git add frontend/js/views/reports.js
git commit -m "feat: add reports view with 4 charts, filters, and export"
```

---

### Task 6: Push

- [ ] **Step 1: Run full backend test suite**

```bash
cd backend
pytest -v
```

Expected: all tests pass.

- [ ] **Step 2: Push**

```bash
git push
```
