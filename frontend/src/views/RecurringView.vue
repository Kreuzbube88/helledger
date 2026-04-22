<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { RefreshCw } from 'lucide-vue-next'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const { t } = useI18n()
const api = useApi()

const templates = ref([])
const categories = ref([])
const accounts = ref([])
const showDialog = ref(false)
const editingId = ref(null)

const form = ref({
  name: '',
  amount: '',
  category_id: '',
  account_id: '',
  interval: 'monthly',
  day_of_month: 1,
  next_date: new Date().toISOString().slice(0, 10),
  show_as_monthly: false,
})

const showMonthlyOpt = computed(() => form.value.interval !== 'monthly')

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

const flatCategories = computed(() => flattenCats(categories.value))

async function load() {
  const res = await api.get('/recurring')
  if (res.ok) templates.value = await res.json()
}

async function loadMeta() {
  const [catRes, accRes] = await Promise.all([api.get('/categories'), api.get('/accounts')])
  if (catRes.ok) categories.value = await catRes.json()
  if (accRes.ok) accounts.value = await accRes.json()
}

function openCreate() {
  editingId.value = null
  form.value = {
    name: '',
    amount: '',
    category_id: '__none__',
    account_id: '__none__',
    interval: 'monthly',
    day_of_month: 1,
    next_date: new Date().toISOString().slice(0, 10),
    show_as_monthly: false,
  }
  showDialog.value = true
}

function openEdit(tmpl) {
  editingId.value = tmpl.id
  form.value = {
    name: tmpl.name,
    amount: String(Math.abs(parseFloat(tmpl.amount))),
    category_id: tmpl.category_id ? String(tmpl.category_id) : '__none__',
    account_id: tmpl.account_id ? String(tmpl.account_id) : '__none__',
    interval: tmpl.interval,
    day_of_month: tmpl.day_of_month,
    next_date: tmpl.next_date,
    show_as_monthly: tmpl.show_as_monthly,
  }
  showDialog.value = true
}

async function save() {
  const body = {
    name: form.value.name,
    amount: parseFloat(form.value.amount),
    category_id: (form.value.category_id && form.value.category_id !== '__none__') ? parseInt(form.value.category_id) : null,
    account_id: (form.value.account_id && form.value.account_id !== '__none__') ? parseInt(form.value.account_id) : null,
    interval: form.value.interval,
    day_of_month: parseInt(form.value.day_of_month),
    next_date: form.value.next_date,
    show_as_monthly: form.value.show_as_monthly,
  }
  const res = editingId.value
    ? await api.patch(`/recurring/${editingId.value}`, body)
    : await api.post('/recurring', body)
  if (res.ok) {
    showDialog.value = false
    await load()
    toast.success(t('common.actions'))
  } else {
    toast.error(t('errors.generic'))
  }
}

async function remove(id) {
  if (!confirm(t('recurring.noData'))) return
  const res = await api.delete(`/recurring/${id}`)
  if (res.ok) { await load() }
  else toast.error(t('errors.generic'))
}

async function triggerNow() {
  const res = await api.post('/recurring/trigger', {})
  if (res.ok) {
    const data = await res.json()
    toast.success(`${t('recurring.triggered')}: ${data.count}`)
    await load()
  } else {
    toast.error(t('errors.generic'))
  }
}

function monthlyEquiv(tmpl) {
  const map = { quarterly: 3, semi_annual: 6, annual: 12 }
  if (!tmpl.show_as_monthly || tmpl.interval === 'monthly') return null
  const months = map[tmpl.interval]
  if (!months) return null
  return (parseFloat(tmpl.amount) / months).toFixed(2).replace('.', ',') + ' €'
}

function fmtAmount(val) {
  return parseFloat(val).toFixed(2).replace('.', ',') + ' €'
}

onMounted(() => Promise.all([load(), loadMeta()]))
</script>

<template>
  <div class="min-h-dvh bg-background">
    <main class="max-w-5xl mx-auto px-4 py-6">
      <div class="flex items-center justify-between mb-6 flex-wrap gap-3">
        <h1 class="text-xl font-bold">{{ t('recurring.title') }}</h1>
        <div class="flex gap-2">
          <Button variant="outline" @click="triggerNow">
            <RefreshCw class="h-4 w-4 mr-2" />
            {{ t('recurring.triggerNow') }}
          </Button>
          <Button @click="openCreate">{{ t('recurring.add') }}</Button>
        </div>
      </div>

      <div class="rounded-lg border bg-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{{ t('recurring.name') }}</TableHead>
              <TableHead class="text-right">{{ t('recurring.amount') }}</TableHead>
              <TableHead>{{ t('recurring.interval') }}</TableHead>
              <TableHead>{{ t('recurring.nextDate') }}</TableHead>
              <TableHead>{{ t('recurring.monthlyEquiv') }}</TableHead>
              <TableHead class="text-right">{{ t('common.actions') }}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-if="templates.length === 0">
              <TableCell colspan="6" class="text-center text-muted-foreground py-8">
                {{ t('recurring.noData') }}
              </TableCell>
            </TableRow>
            <TableRow v-for="tmpl in templates" :key="tmpl.id">
              <TableCell>{{ tmpl.name }}</TableCell>
              <TableCell class="text-right tabular-nums">{{ fmtAmount(tmpl.amount) }}</TableCell>
              <TableCell>{{ t(`recurring.intervals.${tmpl.interval}`) }}</TableCell>
              <TableCell class="tabular-nums text-sm">{{ tmpl.next_date }}</TableCell>
              <TableCell class="text-sm text-muted-foreground tabular-nums">
                {{ monthlyEquiv(tmpl) || '—' }}
              </TableCell>
              <TableCell class="text-right space-x-1 whitespace-nowrap">
                <Button variant="ghost" size="sm" @click="openEdit(tmpl)">{{ t('transactions.edit') }}</Button>
                <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="remove(tmpl.id)">
                  {{ t('transactions.delete') }}
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
          <DialogTitle>{{ editingId ? t('transactions.edit') : t('recurring.add') }}</DialogTitle>
        </DialogHeader>
        <form @submit.prevent="save" class="space-y-4">
          <div class="space-y-1">
            <Label>{{ t('recurring.name') }}</Label>
            <Input v-model="form.name" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('recurring.amount') }}</Label>
            <Input v-model="form.amount" type="number" step="0.01" min="0" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('categories.title') }}</Label>
            <Select v-model="form.category_id">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">{{ t('categories.noAccount') }}</SelectItem>
                <SelectItem v-for="cat in flatCategories" :key="cat.id" :value="String(cat.id)">
                  {{ cat.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-1">
            <Label>{{ t('transactions.account') }}</Label>
            <Select v-model="form.account_id">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">{{ t('categories.noAccount') }}</SelectItem>
                <SelectItem v-for="acc in accounts" :key="acc.id" :value="String(acc.id)">
                  {{ acc.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-1">
            <Label>{{ t('recurring.interval') }}</Label>
            <Select v-model="form.interval">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="monthly">{{ t('recurring.intervals.monthly') }}</SelectItem>
                <SelectItem value="quarterly">{{ t('recurring.intervals.quarterly') }}</SelectItem>
                <SelectItem value="semi_annual">{{ t('recurring.intervals.semi_annual') }}</SelectItem>
                <SelectItem value="annual">{{ t('recurring.intervals.annual') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-1">
            <Label>{{ t('recurring.dayOfMonth') }}</Label>
            <Input v-model="form.day_of_month" type="number" min="1" max="28" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('recurring.nextDate') }}</Label>
            <Input v-model="form.next_date" type="date" required />
          </div>
          <div v-if="showMonthlyOpt" class="flex items-center gap-2">
            <input id="show-as-monthly" type="checkbox" v-model="form.show_as_monthly" class="h-4 w-4 rounded border" />
            <Label for="show-as-monthly">{{ t('recurring.showAsMonthly') }}</Label>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" @click="showDialog = false">{{ t('transactions.cancel') }}</Button>
            <Button type="submit">{{ t('transactions.save') }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>
