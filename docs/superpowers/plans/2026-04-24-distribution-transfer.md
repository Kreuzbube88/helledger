# Distribution Transfer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second fixed-cost transfer type ("Kontoverteilung") that moves money from a fixed-costs account to a variable account — shown informatively in MonthView but not counted as income, expense, or savings.

**Architecture:** A new `cost_type='distribution'` value in the fixed_costs table (no migration needed — SQLite stores strings). Auto-booking creates the same paired `transfer` transactions as a savings transfer. The MonthView backend detects distributions by querying positive transfers into variable-role accounts. The Forecast router handles the new type explicitly.

**Tech Stack:** FastAPI + SQLAlchemy + SQLite (backend), Vue 3 + vue-i18n + Tailwind (frontend). No new dependencies.

---

## File Map

| File | Change |
|------|--------|
| `backend/app/schemas/fixed_costs.py` | Validate `distribution` cost_type same as `transfer` |
| `backend/app/schemas/dashboard.py` | Add `DistributionRow`, `distribution_rows` on `MonthViewResponse` |
| `backend/app/routers/fixed_costs.py` | `trigger_due`: handle `distribution` same as `transfer` |
| `backend/app/routers/dashboard.py` | `get_month_view`: query distribution rows from variable accounts |
| `backend/app/routers/forecast.py` | Handle `distribution` cost_type in balance simulation |
| `frontend/src/views/FixedCostsView.vue` | New type option, filtered account dropdowns, new section |
| `frontend/src/views/MonthView.vue` | Kontoverteilung card, Verfügbar KPI shows variable only on mobile |
| `frontend/src/locales/de.json` | New i18n keys |
| `frontend/src/locales/en.json` | New i18n keys |

---

## Context: Current Transfer Logic

- `cost_type='transfer'` in `fixed_costs` = savings transfer (any account → savings account)
- `trigger_due` in `fixed_costs.py` lines 99–123: creates debit+credit `transaction_type='transfer'` pair
- `get_month_view` in `dashboard.py` lines 283–341: savings counted by querying positive transfers INTO savings-role accounts
- Distribution detection in MonthView: positive transfers INTO variable-role accounts (mirrors savings logic)
- **No database migration needed** — `cost_type` is `String(20)`, `'distribution'` is just a new valid string value

---

## Task 1: Backend Schemas

**Files:**
- Modify: `backend/app/schemas/fixed_costs.py:27-32`
- Modify: `backend/app/schemas/dashboard.py`

- [ ] **Step 1: Update `FixedCostCreate` validator to accept `distribution`**

In `backend/app/schemas/fixed_costs.py`, replace the `validate_transfer` method:

```python
@model_validator(mode='after')
def validate_transfer(self) -> 'FixedCostCreate':
    if self.cost_type in ('transfer', 'distribution'):
        if not self.to_account_id:
            raise ValueError('to_account_id required for transfer and distribution types')
        self.interval_months = 1
    return self
```

- [ ] **Step 2: Add `DistributionRow` schema and extend `MonthViewResponse`**

In `backend/app/schemas/dashboard.py`, add after the `SavingsRow` class and update `MonthViewResponse`:

```python
class DistributionRow(BaseModel):
    description: str
    amount: float
    date: str


class MonthViewResponse(BaseModel):
    year: int
    month: int
    sections: list[MonthSection]
    summary: MonthSummary
    savings_rows: list[SavingsRow] = []
    distribution_rows: list[DistributionRow] = []
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/fixed_costs.py backend/app/schemas/dashboard.py
git commit -m "feat: add distribution cost_type validation and DistributionRow schema"
```

---

## Task 2: Backend Router — Fixed Costs Auto-Booking

**Files:**
- Modify: `backend/app/routers/fixed_costs.py:99`

- [ ] **Step 1: Handle `distribution` in `trigger_due`**

In `backend/app/routers/fixed_costs.py`, change line 99 from:

```python
        if fc.cost_type == 'transfer':
```

to:

```python
        if fc.cost_type in ('transfer', 'distribution'):
```

The booking logic (lines 100–123) is identical for both types: debit from `account_id`, credit to `to_account_id`, both with `transaction_type='transfer'`. No other change needed here.

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/fixed_costs.py
git commit -m "feat: auto-book distribution transfers same as savings transfers"
```

---

## Task 3: Backend Router — MonthView Distribution Rows

**Files:**
- Modify: `backend/app/routers/dashboard.py:324-341` and return statement

- [ ] **Step 1: Query distribution rows in `get_month_view`**

In `backend/app/routers/dashboard.py`, add the distribution query after the `savings_rows` block (after line 341). Also add the import for `DistributionRow` at the top of the imports from `app.schemas.dashboard`.

First, add `DistributionRow` to the import at line 14:
```python
from app.schemas.dashboard import (
    DistributionRow,
    MonthCategoryRow,
    MonthSection,
    MonthSummary,
    MonthViewResponse,
    SavingsRow,
    YearCategoryRow,
    YearViewResponse,
)
```

Then after the `savings_rows` block (around line 341), add:

```python
    # distribution rows: positive transfers INTO variable accounts
    variable_acc_ids = [
        a.id for a in db.query(Account).filter(
            Account.household_id == hh_id,
            Account.account_role == "variable",
            Account.archived.is_(False),
        ).all()
    ]
    distribution_rows = []
    if variable_acc_ids:
        d_txs = db.query(Transaction).filter(
            Transaction.household_id == hh_id,
            Transaction.account_id.in_(variable_acc_ids),
            Transaction.transaction_type == "transfer",
            Transaction.amount > 0,
            func.strftime("%Y", Transaction.date) == year_str,
            func.strftime("%m", Transaction.date) == month_str,
        ).all()
        distribution_rows = [
            DistributionRow(
                description=t.description or "Kontoverteilung",
                amount=float(t.amount),
                date=str(t.date),
            )
            for t in d_txs
        ]
```

- [ ] **Step 2: Add `distribution_rows` to the return statement**

In `backend/app/routers/dashboard.py`, update the `MonthViewResponse(...)` call to include `distribution_rows=distribution_rows`.

The full updated return (around line 396):
```python
    return MonthViewResponse(
        year=year,
        month=month,
        sections=sections,
        summary=MonthSummary(
            total_income=total_income,
            total_expense=total_expense,
            savings_rate=real_savings_rate,
            savings_amount=savings_amount,
            debt_to_income=debt_to_income,
            emergency_months=emergency_months,
        ),
        savings_rows=savings_rows,
        distribution_rows=distribution_rows,
    )
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/dashboard.py
git commit -m "feat: return distribution_rows in month view"
```

---

## Task 4: Backend Router — Forecast

**Files:**
- Modify: `backend/app/routers/forecast.py:87-94`

- [ ] **Step 1: Handle `distribution` in forecast balance simulation**

In `backend/app/routers/forecast.py`, after the `elif fc.cost_type == "transfer":` block (lines 87–94), add:

```python
            elif fc.cost_type == "distribution":
                # debit from fixed_costs account, credit to variable account
                # does NOT count as savings or expenses — purely balance redistribution
                if fc.account_id is not None and fc.account_id in balances:
                    balances[fc.account_id] = balances.get(fc.account_id, 0.0) - amount
                if fc.to_account_id is not None and fc.to_account_id in balances:
                    balances[fc.to_account_id] = balances.get(fc.to_account_id, 0.0) + amount
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/forecast.py
git commit -m "feat: simulate distribution transfers in forecast balance calculation"
```

---

## Task 5: Frontend i18n

**Files:**
- Modify: `frontend/src/locales/de.json`
- Modify: `frontend/src/locales/en.json`

- [ ] **Step 1: Add German i18n keys**

In `frontend/src/locales/de.json`, find the `fixedCosts` section and add:
- `"distribution": "Kontoverteilung"` alongside the existing `"transfer"` key
- `"sections": { ..., "distribution": "Kontoverteilung" }` alongside existing section keys

Find the `monthView` section and add:
- `"distributionSection": "Kontoverteilung"`

Example — in `fixedCosts`:
```json
"transfer": "Umbuchung (Sparen)",
"distribution": "Kontoverteilung",
```

In `fixedCosts.sections`:
```json
"transfer": "Sparumbuchungen",
"distribution": "Kontoverteilung",
```

In `monthView`:
```json
"savingsSection": "Sparüberweisungen",
"distributionSection": "Kontoverteilung",
```

- [ ] **Step 2: Add English i18n keys**

In `frontend/src/locales/en.json`, add the same keys:

In `fixedCosts`:
```json
"transfer": "Transfer (Savings)",
"distribution": "Account Distribution",
```

In `fixedCosts.sections`:
```json
"transfer": "Savings Transfers",
"distribution": "Account Distribution",
```

In `monthView`:
```json
"savingsSection": "Savings Transfers",
"distributionSection": "Account Distribution",
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/locales/de.json frontend/src/locales/en.json
git commit -m "feat: add i18n keys for distribution transfer type"
```

---

## Task 6: Frontend FixedCostsView — Script Changes

**Files:**
- Modify: `frontend/src/views/FixedCostsView.vue` (script section)

- [ ] **Step 1: Add `distributionItems` computed and filtered account computeds**

After `transferItems` (line 75), add:

```js
const distributionItems = computed(() => fixedCosts.value.filter(fc => fc.cost_type === 'distribution' && !fc.loan_id))
```

After `filteredCategories`, add filtered account lists for the dialog:

```js
const sourceAccounts = computed(() => {
  if (form.value.cost_type === 'distribution') {
    return accounts.value.filter(a => a.account_role === 'fixed_costs')
  }
  if (form.value.cost_type === 'transfer') {
    return accounts.value.filter(a => ['fixed_costs', 'variable'].includes(a.account_role))
  }
  return accounts.value
})

const targetAccounts = computed(() => {
  if (form.value.cost_type === 'distribution') {
    return accounts.value.filter(a => a.account_role === 'variable')
  }
  if (form.value.cost_type === 'transfer') {
    return accounts.value.filter(a => a.account_role === 'savings')
  }
  return accounts.value
})
```

- [ ] **Step 2: Update `openCreate` to handle `distribution` defaults**

In the `openCreate` function (lines 109–137), add an `else if` for distribution after the transfer branch:

```js
  } else if (costType === 'distribution') {
    const fromId = accountByRole('fixed_costs')
    if (fromId) form.value.account_id = String(fromId)
    const toId = accountByRole('variable')
    if (toId) form.value.to_account_id = String(toId)
  }
```

- [ ] **Step 3: Update the `watch` for `cost_type` to handle `distribution`**

In the `watch(() => form.value.cost_type, ...)` (lines 156–170), add:

```js
  } else if (newType === 'distribution') {
    const fromId = accountByRole('fixed_costs')
    if (fromId) form.value.account_id = String(fromId)
    const toId = accountByRole('variable')
    if (toId) form.value.to_account_id = String(toId)
  }
```

- [ ] **Step 4: Update `save()` to send `to_account_id` for distribution**

In the `save` function (line 184), change:

```js
  if (form.value.cost_type === 'transfer' && form.value.to_account_id) {
    body.to_account_id = parseInt(form.value.to_account_id)
  }
```

to:

```js
  if (['transfer', 'distribution'].includes(form.value.cost_type) && form.value.to_account_id) {
    body.to_account_id = parseInt(form.value.to_account_id)
  }
```

- [ ] **Step 5: Commit script changes**

```bash
git add frontend/src/views/FixedCostsView.vue
git commit -m "feat: distribution transfer script — computed items, account filters, defaults"
```

---

## Task 7: Frontend FixedCostsView — Template Changes

**Files:**
- Modify: `frontend/src/views/FixedCostsView.vue` (template section)

- [ ] **Step 1: Add `distribution` to type dropdown**

In the `<SelectContent>` for cost_type (line 446–451), add after the transfer item:

```html
<SelectItem value="distribution">{{ t('fixedCosts.distribution') }}</SelectItem>
```

- [ ] **Step 2: Exclude `distribution` from category and interval fields**

Change `v-if="form.cost_type !== 'transfer'"` on the category dropdown (line 453) to:

```html
<div v-if="!['transfer', 'distribution'].includes(form.cost_type)" class="space-y-1">
```

Change `v-if="form.cost_type !== 'transfer'"` on the interval dropdown (line 486) to:

```html
<div v-if="!['transfer', 'distribution'].includes(form.cost_type)" class="space-y-1">
```

Change `v-if="form.cost_type !== 'transfer' && parseInt(form.interval_months) > 1"` on the show_split checkbox (line 498) to:

```html
<div v-if="!['transfer', 'distribution'].includes(form.cost_type) && parseInt(form.interval_months) > 1" class="flex items-center gap-2">
```

- [ ] **Step 3: Filter account dropdowns using computed lists**

For the "Von Konto" / account_id selector (line 465–471), use `sourceAccounts` instead of `accounts`:

```html
<div class="space-y-1">
  <Label>{{ ['transfer', 'distribution'].includes(form.cost_type) ? t('fixedCosts.fromAccount') : t('transactions.account') }}</Label>
  <Select v-model="form.account_id">
    <SelectTrigger><SelectValue /></SelectTrigger>
    <SelectContent>
      <SelectItem value="__none__">—</SelectItem>
      <SelectItem v-for="acc in sourceAccounts" :key="acc.id" :value="String(acc.id)">{{ acc.name }}</SelectItem>
    </SelectContent>
  </Select>
</div>
```

For the "Zu Konto" / to_account_id selector (line 473–481), show for both types and use `targetAccounts`:

```html
<div v-if="['transfer', 'distribution'].includes(form.cost_type)" class="space-y-1">
  <Label>{{ t('fixedCosts.toAccount') }}</Label>
  <Select v-model="form.to_account_id">
    <SelectTrigger><SelectValue /></SelectTrigger>
    <SelectContent>
      <SelectItem v-for="acc in targetAccounts" :key="acc.id" :value="String(acc.id)">{{ acc.name }}</SelectItem>
    </SelectContent>
  </Select>
</div>
```

- [ ] **Step 4: Add Kontoverteilung section to the list**

After the savings transfers section (after line 365, before the loan items section), add:

```html
<!-- ── Account Distributions ─────────────────────────────── -->
<div v-if="distributionItems.length > 0" class="mb-8">
  <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
    {{ t('fixedCosts.sections.distribution') }}
  </h2>
  <div class="rounded-lg border bg-card overflow-hidden">
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>{{ t('accounts.name') }}</TableHead>
          <TableHead>{{ t('fixedCosts.fromAccount') }}</TableHead>
          <TableHead>{{ t('fixedCosts.toAccount') }}</TableHead>
          <TableHead class="text-right">{{ t('transactions.amount') }}</TableHead>
          <TableHead class="text-right w-52">{{ t('common.actions') }}</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow v-for="fc in distributionItems" :key="fc.id">
          <TableCell class="font-medium">{{ fc.name }}</TableCell>
          <TableCell class="text-muted-foreground text-sm">{{ accounts.find(a => a.id === fc.account_id)?.name || '—' }}</TableCell>
          <TableCell class="text-muted-foreground text-sm">{{ accounts.find(a => a.id === fc.to_account_id)?.name || '—' }}</TableCell>
          <TableCell class="text-right tabular-nums font-medium">{{ fmtAmount(fc.amount) }}</TableCell>
          <TableCell class="text-right space-x-1 whitespace-nowrap">
            <Button variant="ghost" size="sm" @click="openChangeAmount(fc)">{{ t('fixedCosts.changeAmount') }}</Button>
            <Button variant="ghost" size="sm" @click="openEdit(fc)">{{ t('categories.edit') }}</Button>
            <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="deactivate(fc)">
              {{ t('categories.archive') }}
            </Button>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</div>
```

- [ ] **Step 5: Commit template changes**

```bash
git add frontend/src/views/FixedCostsView.vue
git commit -m "feat: distribution transfer UI — type selector, account filters, list section"
```

---

## Task 8: Frontend MonthView Changes

**Files:**
- Modify: `frontend/src/views/MonthView.vue`

- [ ] **Step 1: Add `totalDistribution` computed in script**

In the script section (after `totalSavings` computed, around line 42), add:

```js
const totalDistribution = computed(() =>
  (data.value?.distribution_rows || []).reduce((s, r) => s + r.amount, 0)
)
```

- [ ] **Step 2: Update Verfügbar KPI — desktop removes Gesamt, mobile shows variable only**

Replace the entire 4th KPI column (lines 94–113) with:

```html
<!-- Variabel verfügbar -->
<div class="px-4 py-2 space-y-1 text-center">
  <p class="text-xs text-muted-foreground uppercase tracking-wide">{{ t('monthView.availableVariable') }}</p>
  <!-- Desktop: Fix + Variable split -->
  <div class="hidden md:grid grid-cols-2 gap-2 text-center">
    <div>
      <p class="text-xs text-muted-foreground">{{ t('monthView.availableFixed') }}</p>
      <p class="text-sm font-semibold tabular-nums">{{ fixedCostsBalance.toFixed(2) }}</p>
    </div>
    <div>
      <p class="text-xs text-muted-foreground">{{ t('monthView.availableVariable') }}</p>
      <p class="text-sm font-bold tabular-nums" :class="variableBalance >= 0 ? 'text-emerald-500' : 'text-rose-500'">{{ variableBalance.toFixed(2) }}</p>
    </div>
  </div>
  <!-- Mobile: variable only -->
  <p class="md:hidden text-xl font-bold tabular-nums" :class="variableBalance >= 0 ? 'text-emerald-500' : 'text-rose-500'">{{ variableBalance.toFixed(2) }}</p>
</div>
```

- [ ] **Step 3: Add Kontoverteilung card section**

After the Sparüberweisungen card (after line 174, before `</template>`), add:

```html
<!-- Kontoverteilung-Sektion -->
<Card v-if="data?.distribution_rows?.length">
  <CardHeader>
    <CardTitle>{{ t('monthView.distributionSection') }}</CardTitle>
  </CardHeader>
  <CardContent>
    <table class="w-full text-sm table-fixed">
      <thead>
        <tr class="border-b text-muted-foreground">
          <th class="text-left py-1">{{ t('monthView.distributionSection') }}</th>
          <th class="text-right py-1 w-32">{{ $t('monthView.ist') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in data.distribution_rows" :key="row.date + row.description" class="border-b hover:bg-muted/50">
          <td class="py-1">{{ row.description }}</td>
          <td class="text-right tabular-nums text-blue-500">{{ row.amount.toFixed(2) }}</td>
        </tr>
      </tbody>
      <tfoot>
        <tr class="font-semibold">
          <td class="pt-2">{{ $t('monthView.gesamt') }}</td>
          <td class="text-right pt-2 tabular-nums text-blue-500">{{ totalDistribution.toFixed(2) }}</td>
        </tr>
      </tfoot>
    </table>
  </CardContent>
</Card>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/MonthView.vue
git commit -m "feat: Kontoverteilung section + variable-only Verfügbar in MonthView"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Sparüberweisung (transfer): Fix/Variable → Savings, counts as savings — unchanged, still works
- [x] Kontoverteilung (distribution): Fix → Variable, NOT savings/expense — Tasks 1–8
- [x] Savings accounts NOT selectable as source — `sourceAccounts` computed (Task 6)
- [x] Savings accounts still selectable as source on Transactions page — not touched
- [x] Kontoverteilung shown in its own section in MonthView — Task 8
- [x] Kontoverteilung in Forecast — Task 4
- [x] Kontoverteilung in FixedCostsView list — Task 7
- [x] Verfügbar: Variable balance prominent on mobile, Fix+Variable split on desktop — Task 8
- [x] No migration: existing `transfer` entries unaffected, `distribution` is just a new string value
- [x] Fresh install + upgrade safe: no schema change required

**Placeholder scan:** None found.

**Type consistency:** `DistributionRow` defined in Task 1, used in Task 3. `distribution_rows` field defined in Task 1, populated in Task 3, returned in Task 3, consumed in Task 8. All consistent.
