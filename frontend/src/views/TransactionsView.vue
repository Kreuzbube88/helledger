<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
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
  transaction_type: 'expense',
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

function accountName(id) {
  return accounts.value.find(a => a.id === id)?.name || '—'
}
function categoryName(id) {
  return id ? (flatCategories.value.find(c => c.id === id)?.name || '—') : '—'
}

async function load() {
  const params = new URLSearchParams({ year: year.value, month: month.value })
  if (filterAccountId.value && filterAccountId.value !== '__all__') params.set('account_id', filterAccountId.value)
  if (filterCategoryId.value && filterCategoryId.value !== '__all__') params.set('category_id', filterCategoryId.value)
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
    transaction_type: 'expense',
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
    transaction_type: tx.transaction_type,
    date: tx.date,
    description: tx.description,
    amount: String(Math.abs(parseFloat(tx.amount))),
    account_id: tx.account_id ? String(tx.account_id) : '',
    category_id: tx.category_id ? String(tx.category_id) : '__none__',
    from_account_id: tx.from_account_id ? String(tx.from_account_id) : '',
    to_account_id: tx.to_account_id ? String(tx.to_account_id) : '',
  }
  showDialog.value = true
}

async function save() {
  let body
  if (form.value.transaction_type === 'transfer') {
    body = {
      transaction_type: 'transfer',
      date: form.value.date,
      description: form.value.description,
      amount: parseFloat(form.value.amount),
      from_account_id: parseInt(form.value.from_account_id),
      to_account_id: parseInt(form.value.to_account_id),
    }
  } else {
    body = {
      transaction_type: form.value.transaction_type,
      date: form.value.date,
      description: form.value.description,
      amount: parseFloat(form.value.amount),
      account_id: parseInt(form.value.account_id),
      category_id: (form.value.category_id && form.value.category_id !== '__none__') ? parseInt(form.value.category_id) : null,
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

onMounted(() => Promise.all([loadMeta(), load()]))
</script>

<template>
  <div class="min-h-dvh bg-background">
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
            <SelectItem value="__all__">{{ t('transactions.filterAccount') }}</SelectItem>
            <SelectItem v-for="acc in accounts" :key="acc.id" :value="String(acc.id)">{{ acc.name }}</SelectItem>
          </SelectContent>
        </Select>
        <Select v-model="filterCategoryId" @update:modelValue="load">
          <SelectTrigger class="w-48">
            <SelectValue :placeholder="t('transactions.filterCategory')" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">{{ t('transactions.filterCategory') }}</SelectItem>
            <SelectItem v-for="cat in flatCategories" :key="cat.id" :value="String(cat.id)">{{ cat.name }}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <!-- Table -->
      <div class="rounded-lg border bg-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead class="w-28">{{ t('transactions.date') }}</TableHead>
              <TableHead>{{ t('transactions.description') }}</TableHead>
              <TableHead>{{ t('transactions.account') }}</TableHead>
              <TableHead>{{ t('transactions.category') }}</TableHead>
              <TableHead class="w-28">{{ t('transactions.type') }}</TableHead>
              <TableHead class="text-right w-32">{{ t('transactions.amount') }}</TableHead>
              <TableHead class="w-32 text-right">{{ t('common.actions') }}</TableHead>
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
              <TableCell class="text-sm text-muted-foreground">{{ accountName(tx.account_id) }}</TableCell>
              <TableCell class="text-sm text-muted-foreground">{{ categoryName(tx.category_id) }}</TableCell>
              <TableCell>
                <Badge :variant="TYPE_BADGE[tx.transaction_type]">
                  {{ t(`transactions.${tx.transaction_type}`) }}
                </Badge>
              </TableCell>
              <TableCell class="text-right tabular-nums"
                :class="tx.transaction_type === 'income' ? 'text-emerald-500' : tx.transaction_type === 'transfer' ? 'text-violet-500' : 'text-rose-500'">
                {{ fmtAmount(tx) }}
              </TableCell>
              <TableCell class="text-right space-x-1 whitespace-nowrap">
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
            <Select v-model="form.transaction_type">
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
          <template v-if="form.transaction_type === 'transfer'">
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
                  <SelectItem value="__none__">—</SelectItem>
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
