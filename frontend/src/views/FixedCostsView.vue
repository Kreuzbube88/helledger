<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useConfirm } from '@/composables/useConfirm'
import { toast } from 'vue-sonner'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const { t } = useI18n()
const { confirm } = useConfirm()
const api = useApi()

const fixedCosts = ref([])
const categories = ref([])
const accounts = ref([])
const reserve = ref(null)

// Main dialog (create/edit)
const showDialog = ref(false)
const editingId = ref(null)
const form = ref({
  name: '',
  cost_type: 'expense',
  category_id: '__none__',
  account_id: '__none__',
  to_account_id: '',
  amount: '',
  interval_months: '1',
  show_split: false,
  start_date: new Date().toISOString().slice(0, 10),
  end_date: '',
})

// Change-amount dialog
const showAmountDialog = ref(false)
const amountDialogId = ref(null)
const amountForm = ref({ new_amount: '', valid_from: new Date().toISOString().slice(0, 10) })

// ── Helpers ──────────────────────────────────────────────────────────

function categoryName(id) {
  if (!id) return '—'
  return categories.value.find(c => c.id === Number(id))?.name || '—'
}

function intervalLabel(months) {
  return t('fixedCosts.intervals.' + months)
}

function fmtAmount(amount) {
  return parseFloat(amount).toFixed(2).replace('.', ',') + ' €'
}

function accountByRole(role) {
  return accounts.value.find(a => a.account_role === role)?.id ?? null
}

// ── Derived lists ─────────────────────────────────────────────────────

const filteredCategories = computed(() => {
  const typeMap = { expense: 'fixed', income: 'income' }
  const target = typeMap[form.value.cost_type]
  if (!target) return []
  return categories.value.filter(c => c.category_type === target)
})

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

const incomeItems = computed(() => fixedCosts.value.filter(fc => fc.cost_type === 'income' && !fc.loan_id))
const expenseItems = computed(() => fixedCosts.value.filter(fc => fc.cost_type === 'expense' && !fc.loan_id))
const transferItems = computed(() => fixedCosts.value.filter(fc => fc.cost_type === 'transfer' && !fc.loan_id))
const distributionItems = computed(() => fixedCosts.value.filter(fc => fc.cost_type === 'distribution' && !fc.loan_id))
const loanItems = computed(() => fixedCosts.value.filter(fc => fc.loan_id !== null && fc.loan_id !== undefined))

// ── Load data ─────────────────────────────────────────────────────────

async function load() {
  const [fcRes, catRes, accRes, resRes] = await Promise.all([
    api.get('/fixed-costs'),
    api.get('/categories'),
    api.get('/accounts'),
    api.get('/fixed-costs/reserve'),
  ])
  if (fcRes.ok) fixedCosts.value = await fcRes.json()
  if (catRes.ok) {
    const raw = await catRes.json()
    const flat = []
    function walk(list, depth) {
      for (const c of list) {
        flat.push({ ...c, _isChild: depth > 0 })
        if (c.children) walk(c.children, depth + 1)
      }
    }
    walk(raw, 0)
    categories.value = flat
  }
  if (accRes.ok) accounts.value = await accRes.json()
  if (resRes.ok) reserve.value = await resRes.json()
}

onMounted(load)

// ── Create / Edit ─────────────────────────────────────────────────────

function openCreate() {
  editingId.value = null
  form.value = {
    name: '',
    cost_type: 'expense',
    category_id: '__none__',
    account_id: '__none__',
    to_account_id: '',
    amount: '',
    interval_months: '1',
    show_split: false,
    start_date: new Date().toISOString().slice(0, 10),
    end_date: '',
  }
  const costType = form.value.cost_type
  if (costType === 'expense') {
    const id = accountByRole('fixed_costs')
    if (id) form.value.account_id = String(id)
  } else if (costType === 'income') {
    const id = accountByRole('fixed_costs')
    if (id) form.value.account_id = String(id)
  } else if (costType === 'transfer') {
    const fromId = accountByRole('fixed_costs') ?? accountByRole('variable')
    if (fromId) form.value.account_id = String(fromId)
    const toId = accountByRole('savings')
    if (toId) form.value.to_account_id = String(toId)
  } else if (costType === 'distribution') {
    const fromId = accountByRole('fixed_costs')
    if (fromId) form.value.account_id = String(fromId)
    const toId = accountByRole('variable')
    if (toId) form.value.to_account_id = String(toId)
  }
  showDialog.value = true
}

function openEdit(fc) {
  editingId.value = fc.id
  form.value = {
    name: fc.name,
    cost_type: fc.cost_type,
    category_id: fc.category_id ? String(fc.category_id) : '__none__',
    account_id: fc.account_id ? String(fc.account_id) : '__none__',
    to_account_id: fc.to_account_id ? String(fc.to_account_id) : '',
    amount: String(parseFloat(String(fc.amount))),
    interval_months: String(fc.interval_months),
    show_split: fc.show_split,
    start_date: fc.start_date || new Date().toISOString().slice(0, 10),
    end_date: fc.end_date || '',
  }
  showDialog.value = true
}

watch(() => form.value.cost_type, (newType) => {
  if (!showDialog.value) return
  if (newType === 'expense') {
    const id = accountByRole('fixed_costs')
    if (id) form.value.account_id = String(id)
  } else if (newType === 'income') {
    const id = accountByRole('fixed_costs')
    if (id) form.value.account_id = String(id)
  } else if (newType === 'transfer') {
    const fromId = accountByRole('fixed_costs') ?? accountByRole('variable')
    if (fromId) form.value.account_id = String(fromId)
    const toId = accountByRole('savings')
    if (toId) form.value.to_account_id = String(toId)
  } else if (newType === 'distribution') {
    const fromId = accountByRole('fixed_costs')
    if (fromId) form.value.account_id = String(fromId)
    const toId = accountByRole('variable')
    if (toId) form.value.to_account_id = String(toId)
  }
})

async function save() {
  const body = {
    name: form.value.name,
    cost_type: form.value.cost_type,
    amount: parseFloat(form.value.amount),
    interval_months: parseInt(form.value.interval_months),
    show_split: form.value.show_split,
    start_date: form.value.start_date,
    end_date: form.value.end_date || null,
    category_id: form.value.category_id && form.value.category_id !== '__none__' ? parseInt(form.value.category_id) : null,
    account_id: form.value.account_id && form.value.account_id !== '__none__' ? parseInt(form.value.account_id) : null,
  }
  if (['transfer', 'distribution'].includes(form.value.cost_type) && form.value.to_account_id) {
    body.to_account_id = parseInt(form.value.to_account_id)
  }
  const res = editingId.value
    ? await api.patch(`/fixed-costs/${editingId.value}`, body)
    : await api.post('/fixed-costs', body)
  if (res.ok) {
    showDialog.value = false
    await load()
    toast.success(editingId.value ? t('fixedCosts.edit') : t('fixedCosts.add'))
  } else {
    toast.error(t('errors.generic'))
  }
}

// ── Deactivate ────────────────────────────────────────────────────────

async function deactivate(fc) {
  if (!await confirm(t('fixedCosts.confirmDeactivate'))) return
  const res = await api.delete(`/fixed-costs/${fc.id}`)
  if (res.ok) {
    await load()
    toast.success(t('fixedCosts.deactivated'))
  } else {
    toast.error(t('errors.generic'))
  }
}

// ── Change amount ─────────────────────────────────────────────────────

function openChangeAmount(fc) {
  amountDialogId.value = fc.id
  amountForm.value = {
    new_amount: String(parseFloat(fc.amount)),
    valid_from: new Date().toISOString().slice(0, 10),
  }
  showAmountDialog.value = true
}

async function saveAmount() {
  const res = await api.patch(`/fixed-costs/${amountDialogId.value}/amount`, {
    new_amount: parseFloat(amountForm.value.new_amount),
    valid_from: amountForm.value.valid_from,
  })
  if (res.ok) {
    showAmountDialog.value = false
    await load()
    toast.success(t('fixedCosts.changeAmount'))
  } else {
    toast.error(t('errors.generic'))
  }
}
</script>

<template>
  <div class="min-h-dvh bg-background">
    <main class="max-w-4xl mx-auto px-4 py-6">

      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">{{ t('fixedCosts.title') }}</h1>
        <Button @click="openCreate">+ {{ t('fixedCosts.add') }}</Button>
      </div>

      <!-- ── Regular Income ─────────────────────────────────────────── -->
      <div class="mb-8">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {{ t('fixedCosts.sections.income') }}
        </h2>
        <!-- Mobile: income cards -->
        <div class="md:hidden space-y-2 mb-2">
          <div v-if="incomeItems.length === 0" class="text-center text-muted-foreground py-4 text-sm">
            {{ t('fixedCosts.noData') }}
          </div>
          <div v-for="fc in incomeItems" :key="fc.id" class="rounded-xl border bg-card px-4 py-3">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="font-medium text-sm truncate">{{ fc.name }}</p>
                <p class="text-xs text-muted-foreground mt-0.5">{{ categoryName(fc.category_id) }}</p>
                <Badge variant="outline" class="text-[10px] mt-1">{{ intervalLabel(fc.interval_months) }}</Badge>
              </div>
              <div class="text-right shrink-0">
                <p class="text-sm font-bold tabular-nums text-emerald-500">{{ fmtAmount(fc.amount) }}</p>
                <div class="flex gap-1 mt-2 justify-end">
                  <Button variant="ghost" size="sm" class="h-7 px-2 text-xs" @click="openChangeAmount(fc)">{{ t('fixedCosts.changeAmount') }}</Button>
                  <Button variant="ghost" size="sm" class="h-7 px-2 text-xs" @click="openEdit(fc)">{{ t('categories.edit') }}</Button>
                  <Button variant="ghost" size="sm" class="h-7 px-2 text-xs text-destructive hover:text-destructive" @click="deactivate(fc)">{{ t('categories.archive') }}</Button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="hidden md:block rounded-lg border bg-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{{ t('accounts.name') }}</TableHead>
                <TableHead>{{ t('transactions.category') }}</TableHead>
                <TableHead>{{ t('fixedCosts.intervalLabel') }}</TableHead>
                <TableHead class="text-right">{{ t('transactions.amount') }}</TableHead>
                <TableHead class="text-right w-52">{{ t('common.actions') }}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-if="incomeItems.length === 0">
                <TableCell colspan="5" class="text-center text-muted-foreground py-6">
                  {{ t('fixedCosts.noData') }}
                </TableCell>
              </TableRow>
              <TableRow v-for="fc in incomeItems" :key="fc.id">
                <TableCell class="font-medium">{{ fc.name }}</TableCell>
                <TableCell class="text-muted-foreground text-sm">{{ categoryName(fc.category_id) }}</TableCell>
                <TableCell>
                  <Badge variant="outline">{{ intervalLabel(fc.interval_months) }}</Badge>
                </TableCell>
                <TableCell class="text-right tabular-nums text-emerald-500 font-medium">{{ fmtAmount(fc.amount) }}</TableCell>
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

      <!-- ── Regular Expenses ───────────────────────────────────────── -->
      <div class="mb-8">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {{ t('fixedCosts.sections.expense') }}
        </h2>
        <!-- Mobile: expense cards -->
        <div class="md:hidden space-y-2 mb-2">
          <div v-if="expenseItems.length === 0" class="text-center text-muted-foreground py-4 text-sm">
            {{ t('fixedCosts.noData') }}
          </div>
          <div v-for="fc in expenseItems" :key="fc.id" class="rounded-xl border bg-card px-4 py-3">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="font-medium text-sm truncate">{{ fc.name }}</p>
                <p class="text-xs text-muted-foreground mt-0.5">{{ categoryName(fc.category_id) }}</p>
                <Badge variant="outline" class="text-[10px] mt-1">{{ intervalLabel(fc.interval_months) }}</Badge>
              </div>
              <div class="text-right shrink-0">
                <p class="text-sm font-bold tabular-nums text-rose-500">{{ fmtAmount(fc.amount) }}</p>
                <div class="flex gap-1 mt-2 justify-end">
                  <Button variant="ghost" size="sm" class="h-7 px-2 text-xs" @click="openChangeAmount(fc)">{{ t('fixedCosts.changeAmount') }}</Button>
                  <Button variant="ghost" size="sm" class="h-7 px-2 text-xs" @click="openEdit(fc)">{{ t('categories.edit') }}</Button>
                  <Button variant="ghost" size="sm" class="h-7 px-2 text-xs text-destructive hover:text-destructive" @click="deactivate(fc)">{{ t('categories.archive') }}</Button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="hidden md:block rounded-lg border bg-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{{ t('accounts.name') }}</TableHead>
                <TableHead>{{ t('transactions.category') }}</TableHead>
                <TableHead>{{ t('fixedCosts.intervalLabel') }}</TableHead>
                <TableHead class="text-right">{{ t('transactions.amount') }}</TableHead>
                <TableHead class="text-right w-52">{{ t('common.actions') }}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-if="expenseItems.length === 0">
                <TableCell colspan="5" class="text-center text-muted-foreground py-6">
                  {{ t('fixedCosts.noData') }}
                </TableCell>
              </TableRow>
              <TableRow v-for="fc in expenseItems" :key="fc.id">
                <TableCell class="font-medium">{{ fc.name }}</TableCell>
                <TableCell class="text-muted-foreground text-sm">{{ categoryName(fc.category_id) }}</TableCell>
                <TableCell>
                  <Badge variant="outline">{{ intervalLabel(fc.interval_months) }}</Badge>
                </TableCell>
                <TableCell class="text-right tabular-nums text-rose-500 font-medium">{{ fmtAmount(fc.amount) }}</TableCell>
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

      <!-- ── Savings Transfers ─────────────────────────────────────── -->
      <div v-if="transferItems.length > 0" class="mb-8">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {{ t('fixedCosts.sections.transfer') }}
        </h2>
        <!-- Mobile: transfer cards -->
        <div class="md:hidden space-y-2 mb-2">
          <div v-for="fc in transferItems" :key="fc.id" class="rounded-xl border bg-card px-4 py-3">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="font-medium text-sm truncate">{{ fc.name }}</p>
                <p class="text-xs text-muted-foreground mt-0.5">
                  {{ accounts.find(a => a.id === fc.account_id)?.name || '—' }}
                  → {{ accounts.find(a => a.id === fc.to_account_id)?.name || '—' }}
                </p>
              </div>
              <div class="text-right shrink-0">
                <p class="text-sm font-bold tabular-nums">{{ fmtAmount(fc.amount) }}</p>
                <div class="flex gap-1 mt-2 justify-end">
                  <Button variant="ghost" size="sm" class="h-7 px-2 text-xs" @click="openChangeAmount(fc)">{{ t('fixedCosts.changeAmount') }}</Button>
                  <Button variant="ghost" size="sm" class="h-7 px-2 text-xs" @click="openEdit(fc)">{{ t('categories.edit') }}</Button>
                  <Button variant="ghost" size="sm" class="h-7 px-2 text-xs text-destructive hover:text-destructive" @click="deactivate(fc)">{{ t('categories.archive') }}</Button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="hidden md:block rounded-lg border bg-card overflow-hidden">
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
              <TableRow v-for="fc in transferItems" :key="fc.id">
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

      <!-- ── Account Distributions ─────────────────────────────────── -->
      <div v-if="distributionItems.length > 0" class="mb-8">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {{ t('fixedCosts.sections.distribution') }}
        </h2>
        <!-- Mobile: distribution cards -->
        <div class="md:hidden space-y-2 mb-2">
          <div v-for="fc in distributionItems" :key="fc.id" class="rounded-xl border bg-card px-4 py-3">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="font-medium text-sm truncate">{{ fc.name }}</p>
                <p class="text-xs text-muted-foreground mt-0.5">
                  {{ accounts.find(a => a.id === fc.account_id)?.name || '—' }}
                  → {{ accounts.find(a => a.id === fc.to_account_id)?.name || '—' }}
                </p>
              </div>
              <div class="text-right shrink-0">
                <p class="text-sm font-bold tabular-nums">{{ fmtAmount(fc.amount) }}</p>
                <div class="flex gap-1 mt-2 justify-end">
                  <Button variant="ghost" size="sm" class="h-7 px-2 text-xs" @click="openChangeAmount(fc)">{{ t('fixedCosts.changeAmount') }}</Button>
                  <Button variant="ghost" size="sm" class="h-7 px-2 text-xs" @click="openEdit(fc)">{{ t('categories.edit') }}</Button>
                  <Button variant="ghost" size="sm" class="h-7 px-2 text-xs text-destructive hover:text-destructive" @click="deactivate(fc)">{{ t('categories.archive') }}</Button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="hidden md:block rounded-lg border bg-card overflow-hidden">
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

      <!-- ── Loan installments (read-only) ─────────────────────────── -->
      <div v-if="loanItems.length > 0" class="mb-8">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {{ t('fixedCosts.sections.loans') }}
        </h2>
        <!-- Mobile: loan cards -->
        <div class="md:hidden space-y-2 mb-2">
          <div v-for="fc in loanItems" :key="fc.id" class="rounded-xl border bg-card px-4 py-3">
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0">
                <p class="font-medium text-sm truncate">{{ fc.name }}</p>
                <Badge variant="outline" class="text-[10px] mt-1">{{ intervalLabel(fc.interval_months) }}</Badge>
              </div>
              <div class="text-right shrink-0">
                <p class="text-sm font-bold tabular-nums">{{ fmtAmount(fc.amount) }}</p>
                <span class="text-xs text-muted-foreground">{{ t('fixedCosts.managedByLoan') }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="hidden md:block rounded-lg border bg-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{{ t('accounts.name') }}</TableHead>
                <TableHead>{{ t('fixedCosts.intervalLabel') }}</TableHead>
                <TableHead class="text-right">{{ t('transactions.amount') }}</TableHead>
                <TableHead class="text-right w-32">{{ t('common.actions') }}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="fc in loanItems" :key="fc.id">
                <TableCell class="font-medium">{{ fc.name }}</TableCell>
                <TableCell>
                  <Badge variant="outline">{{ intervalLabel(fc.interval_months) }}</Badge>
                </TableCell>
                <TableCell class="text-right tabular-nums font-medium">{{ fmtAmount(fc.amount) }}</TableCell>
                <TableCell class="text-right">
                  <span class="text-xs text-muted-foreground">{{ t('fixedCosts.managedByLoan') }}</span>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>

      <!-- ── Reserve overview ───────────────────────────────────────── -->
      <div v-if="reserve && reserve.total_monthly > 0" class="mb-8">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {{ t('fixedCosts.reserve') }}
        </h2>
        <div class="rounded-lg border bg-card overflow-hidden">
          <div class="px-4 py-3 flex items-center justify-between border-b bg-muted/30">
            <span class="text-sm font-semibold">{{ t('fixedCosts.reserveTotal') }}</span>
            <span class="text-sm font-bold tabular-nums">
              {{ reserve.total_monthly.toFixed(2).replace('.', ',') }} €
            </span>
          </div>
          <div class="overflow-x-auto">
            <Table>
              <TableBody>
                <TableRow v-for="item in reserve.items" :key="item.id">
                  <TableCell class="font-medium">{{ item.name }}</TableCell>
                  <TableCell class="text-muted-foreground text-sm">
                    {{ fmtAmount(item.full_amount) }} / {{ t('fixedCosts.intervals.' + item.interval_months) }}
                  </TableCell>
                  <TableCell class="text-right tabular-nums">
                    = {{ item.monthly_share.toFixed(2).replace('.', ',') }} € / Mon.
                  </TableCell>
                  <TableCell class="text-right text-muted-foreground text-sm">
                    {{ t('fixedCosts.validFrom') }}: {{ item.next_billing }}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </div>
      </div>

    </main>

    <!-- ── Create / Edit dialog ───────────────────────────────────── -->
    <Dialog v-model:open="showDialog">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ editingId ? t('fixedCosts.edit') : t('fixedCosts.add') }}</DialogTitle>
        </DialogHeader>
        <form @submit.prevent="save" class="space-y-4">
          <div class="space-y-1">
            <Label>{{ t('accounts.name') }}</Label>
            <Input v-model="form.name" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('fixedCosts.type') }}</Label>
            <Select v-model="form.cost_type" @update:modelValue="form.category_id = '__none__'">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="income">{{ t('fixedCosts.income') }}</SelectItem>
                <SelectItem value="expense">{{ t('fixedCosts.expense') }}</SelectItem>
                <SelectItem value="transfer">{{ t('fixedCosts.transfer') }}</SelectItem>
                <SelectItem value="distribution">{{ t('fixedCosts.distribution') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div v-if="!['transfer', 'distribution'].includes(form.cost_type)" class="space-y-1">
            <Label>{{ t('transactions.category') }}</Label>
            <Select v-model="form.category_id">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">—</SelectItem>
                <SelectItem
                  v-for="cat in filteredCategories"
                  :key="cat.id"
                  :value="String(cat.id)"
                  :class="cat._isChild ? 'pl-6 text-muted-foreground' : ''"
                >{{ cat._isChild ? '— ' : '' }}{{ cat.name }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
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
          <div v-if="['transfer', 'distribution'].includes(form.cost_type)" class="space-y-1">
            <Label>{{ t('fixedCosts.toAccount') }}</Label>
            <Select v-model="form.to_account_id">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem v-for="acc in targetAccounts" :key="acc.id" :value="String(acc.id)">{{ acc.name }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-1">
            <Label>{{ t('transactions.amount') }}</Label>
            <Input v-model="form.amount" type="number" step="0.01" min="0" required />
          </div>
          <div v-if="!['transfer', 'distribution'].includes(form.cost_type)" class="space-y-1">
            <Label>{{ t('fixedCosts.intervalLabel') }}</Label>
            <Select v-model="form.interval_months">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="1">{{ t('fixedCosts.intervals.1') }}</SelectItem>
                <SelectItem value="3">{{ t('fixedCosts.intervals.3') }}</SelectItem>
                <SelectItem value="6">{{ t('fixedCosts.intervals.6') }}</SelectItem>
                <SelectItem value="12">{{ t('fixedCosts.intervals.12') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div v-if="!['transfer', 'distribution'].includes(form.cost_type) && parseInt(form.interval_months) > 1" class="flex items-center gap-2">
            <input id="showSplit" type="checkbox" v-model="form.show_split" class="h-4 w-4 rounded border-input accent-primary cursor-pointer" />
            <label for="showSplit" class="text-sm cursor-pointer select-none">{{ t('fixedCosts.showSplit') }}</label>
          </div>
          <div class="space-y-1">
            <Label>{{ t('fixedCosts.startDate') }}</Label>
            <Input v-model="form.start_date" type="date" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('fixedCosts.endDate') }}</Label>
            <Input v-model="form.end_date" type="date" />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" @click="showDialog = false">{{ t('common.cancel') }}</Button>
            <Button type="submit">{{ t('accounts.save') }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <!-- ── Change amount dialog ───────────────────────────────────── -->
    <Dialog v-model:open="showAmountDialog">
      <DialogContent class="max-w-sm">
        <DialogHeader>
          <DialogTitle>{{ t('fixedCosts.changeAmount') }}</DialogTitle>
        </DialogHeader>
        <form @submit.prevent="saveAmount" class="space-y-4">
          <div class="space-y-1">
            <Label>{{ t('fixedCosts.newAmount') }}</Label>
            <Input v-model="amountForm.new_amount" type="number" step="0.01" min="0" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('fixedCosts.validFrom') }}</Label>
            <Input v-model="amountForm.valid_from" type="date" required />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" @click="showAmountDialog = false">{{ t('common.cancel') }}</Button>
            <Button type="submit">{{ t('accounts.save') }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

  </div>
</template>
