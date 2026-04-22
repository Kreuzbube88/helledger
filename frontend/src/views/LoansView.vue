<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useConfirm } from '@/composables/useConfirm'
import { useRouter } from 'vue-router'
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
const router = useRouter()

const loans = ref([])
const showDialog = ref(false)

const form = ref({
  loan_type: 'consumer',
  name: '',
  lender: '',
  principal: '',
  interest_rate: '',
  monthly_payment: '',
  term_months: '',
  start_date: new Date().toISOString().slice(0, 10),
  is_existing: false,
  monthly_extra: '',
  include_in_net_worth: true,
  purchase_price: '',
  equity: '',
  property_value: '',
  fixed_rate_until: '',
  land_charge: '',
})

// 3-of-4 logic: track which field is being left empty for calculation
const lockedField = ref(null) // 'principal' | 'interest_rate' | 'monthly_payment' | 'term_months' | null

const fields4 = ['principal', 'interest_rate', 'monthly_payment', 'term_months']


function setLocked(field) {
  if (lockedField.value === field) {
    lockedField.value = null
  } else {
    lockedField.value = field
    form.value[field] = ''
  }
}

function isLocked(field) {
  return lockedField.value === field
}

async function load() {
  const res = await api.get('/loans')
  if (res.ok) loans.value = await res.json()
}

function openCreate() {
  form.value = {
    loan_type: 'consumer',
    name: '',
    lender: '',
    principal: '',
    interest_rate: '',
    monthly_payment: '',
    term_months: '',
    start_date: new Date().toISOString().slice(0, 10),
    is_existing: false,
    monthly_extra: '',
    include_in_net_worth: true,
    purchase_price: '',
    equity: '',
    property_value: '',
    fixed_rate_until: '',
    land_charge: '',
  }
  lockedField.value = null
  showDialog.value = true
}

async function save() {
  const body = {
    loan_type: form.value.loan_type,
    name: form.value.name,
    lender: form.value.lender || null,
    start_date: form.value.start_date,
    is_existing: form.value.is_existing,
    include_in_net_worth: form.value.include_in_net_worth,
    monthly_extra: form.value.monthly_extra ? parseFloat(form.value.monthly_extra) : null,
  }

  // Exactly 3 of 4 — send null for the locked/empty one
  for (const f of fields4) {
    body[f] = form.value[f] !== '' ? (f === 'term_months' ? parseInt(form.value[f]) : parseFloat(form.value[f])) : null
  }

  const nullCount = fields4.filter(f => body[f] === null).length
  if (nullCount !== 1) {
    toast.error(t('loans.provide3of4'))
    return
  }

  if (form.value.loan_type === 'mortgage') {
    body.purchase_price = form.value.purchase_price ? parseFloat(form.value.purchase_price) : null
    body.equity = form.value.equity ? parseFloat(form.value.equity) : null
    body.property_value = form.value.property_value ? parseFloat(form.value.property_value) : null
    body.fixed_rate_until = form.value.fixed_rate_until || null
    body.land_charge = form.value.land_charge ? parseFloat(form.value.land_charge) : null
  }

  const res = await api.post('/loans', body)
  if (res.ok) {
    const loan = await res.json()
    showDialog.value = false
    await load()
    toast.success(t('loans.save'))
    router.push(`/loans/${loan.id}`)
  } else {
    const err = await res.json().catch(() => ({}))
    if (err?.detail === 'payment_too_low') {
      toast.error(t('loans.paymentTooLow'))
    } else {
      toast.error(err?.detail || t('errors.generic'))
    }
  }
}

async function remove(id) {
  if (!await confirm(t('loans.delete') + '?')) return
  const res = await api.delete(`/loans/${id}`)
  if (res.ok) { await load(); toast.success(t('loans.delete')) }
  else toast.error(t('errors.generic'))
}

function fmtBalance(loan) {
  return parseFloat(loan.current_balance).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €'
}

function fmtRate(loan) {
  return parseFloat(loan.monthly_payment).toLocaleString('de-DE', { minimumFractionDigits: 2 }) + ' €'
}

function fmtInterest(loan) {
  return parseFloat(loan.interest_rate).toLocaleString('de-DE', { minimumFractionDigits: 2 }) + ' %'
}

onMounted(load)
</script>

<template>
  <div class="min-h-dvh bg-background">
    <main class="max-w-5xl mx-auto px-4 py-6">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">{{ t('loans.title') }}</h1>
        <Button @click="openCreate">{{ t('loans.add') }}</Button>
      </div>

      <div class="rounded-lg border bg-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{{ t('loans.name') }}</TableHead>
              <TableHead class="w-28">{{ t('accounts.type') }}</TableHead>
              <TableHead class="text-right w-36">{{ t('loans.currentBalance') }}</TableHead>
              <TableHead class="text-right w-32">{{ t('loans.monthlyRate') }}</TableHead>
              <TableHead class="w-24">{{ t('loans.interestRateLabel') }}</TableHead>
              <TableHead class="w-32">{{ t('loans.payoffDate') }}</TableHead>
              <TableHead class="w-24">Status</TableHead>
              <TableHead class="w-36 text-right">{{ t('common.actions') }}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-if="loans.length === 0">
              <TableCell colspan="8" class="text-center text-muted-foreground py-8">
                {{ t('loans.noData') }}
              </TableCell>
            </TableRow>
            <TableRow v-for="loan in loans" :key="loan.id" class="cursor-pointer hover:bg-muted/50" @click="router.push(`/loans/${loan.id}`)">
              <TableCell class="font-medium">
                {{ loan.name }}
                <span v-if="loan.fixed_rate_expiring_soon" class="ml-2 text-xs text-amber-500">⚠ {{ t('loans.fixedRateExpiringSoon') }}</span>
              </TableCell>
              <TableCell>{{ t(`loans.types.${loan.loan_type}`) }}</TableCell>
              <TableCell class="text-right tabular-nums text-rose-500">{{ fmtBalance(loan) }}</TableCell>
              <TableCell class="text-right tabular-nums">{{ fmtRate(loan) }}</TableCell>
              <TableCell class="tabular-nums">{{ fmtInterest(loan) }}</TableCell>
              <TableCell class="text-sm text-muted-foreground">{{ loan.payoff_date?.slice(0, 7) || '—' }}</TableCell>
              <TableCell>
                <Badge :variant="loan.status === 'active' ? 'default' : 'secondary'">
                  {{ t(`loans.statuses.${loan.status}`) }}
                </Badge>
              </TableCell>
              <TableCell class="text-right whitespace-nowrap" @click.stop>
                <Button variant="ghost" size="sm" @click="router.push(`/loans/${loan.id}`)">{{ t('loans.detail.overview') }}</Button>
                <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="remove(loan.id)">{{ t('loans.delete') }}</Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </main>

    <Dialog v-model:open="showDialog">
      <DialogContent class="max-w-lg">
        <DialogHeader>
          <DialogTitle>{{ t('loans.add') }}</DialogTitle>
        </DialogHeader>
        <form @submit.prevent="save" class="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
          <!-- Type toggle -->
          <div class="space-y-1">
            <Label>{{ t('accounts.type') }}</Label>
            <div class="flex rounded-md border overflow-hidden">
              <button type="button"
                v-for="lt in ['consumer', 'mortgage']" :key="lt"
                class="flex-1 px-4 py-1.5 text-sm transition-colors"
                :class="form.loan_type === lt ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted'"
                @click="form.loan_type = lt"
              >{{ t(`loans.types.${lt}`) }}</button>
            </div>
          </div>

          <!-- Existing vs new -->
          <div class="flex items-center gap-2">
            <input type="checkbox" id="is_existing" v-model="form.is_existing" class="h-4 w-4" />
            <Label for="is_existing" class="cursor-pointer">{{ t('loans.isExisting') }}</Label>
          </div>

          <div class="space-y-1">
            <Label>{{ t('loans.name') }}</Label>
            <Input v-model="form.name" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('loans.lender') }}</Label>
            <Input v-model="form.lender" />
          </div>
          <div class="space-y-1">
            <Label>{{ t('loans.startDate') }}</Label>
            <Input v-model="form.start_date" type="date" required />
          </div>

          <!-- 3-of-4 fields -->
          <p class="text-xs text-muted-foreground">{{ t('loans.provide3of4') }}</p>
          <div class="grid grid-cols-2 gap-3">
            <div v-for="f in fields4" :key="f" class="space-y-1">
              <div class="flex items-center justify-between">
                <Label>{{ t(`loans.${f === 'principal' ? 'principal' : f === 'interest_rate' ? 'interestRate' : f === 'monthly_payment' ? 'monthlyPayment' : 'termMonths'}`) }}</Label>
                <button type="button"
                  class="text-[10px] px-1.5 py-0.5 rounded border transition-colors"
                  :class="isLocked(f) ? 'bg-primary text-primary-foreground border-primary' : 'text-muted-foreground border-border hover:bg-muted'"
                  @click="setLocked(f)"
                >{{ t('loans.computed') }}</button>
              </div>
              <Input
                v-model="form[f]"
                :type="f === 'term_months' ? 'number' : 'number'"
                :step="f === 'term_months' ? '1' : '0.01'"
                :min="0"
                :disabled="isLocked(f)"
                :class="isLocked(f) ? 'opacity-40' : ''"
              />
            </div>
          </div>

          <div class="space-y-1">
            <Label>{{ t('loans.monthlyExtra') }}</Label>
            <Input v-model="form.monthly_extra" type="number" step="0.01" min="0" />
          </div>

          <div class="flex items-center gap-2">
            <input type="checkbox" id="in_nw" v-model="form.include_in_net_worth" class="h-4 w-4" />
            <Label for="in_nw" class="cursor-pointer">{{ t('loans.includeInNetWorth') }}</Label>
          </div>

          <!-- Mortgage extras -->
          <template v-if="form.loan_type === 'mortgage'">
            <hr class="border-border" />
            <p class="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{{ t(`loans.types.mortgage`) }}</p>
            <div class="grid grid-cols-2 gap-3">
              <div class="space-y-1">
                <Label>{{ t('loans.purchasePrice') }}</Label>
                <Input v-model="form.purchase_price" type="number" step="0.01" min="0" />
              </div>
              <div class="space-y-1">
                <Label>{{ t('loans.equity') }}</Label>
                <Input v-model="form.equity" type="number" step="0.01" min="0" />
              </div>
              <div class="space-y-1">
                <Label>{{ t('loans.propertyValue') }}</Label>
                <Input v-model="form.property_value" type="number" step="0.01" min="0" />
              </div>
              <div class="space-y-1">
                <Label>{{ t('loans.landCharge') }}</Label>
                <Input v-model="form.land_charge" type="number" step="0.01" min="0" />
              </div>
              <div class="space-y-1 col-span-2">
                <Label>{{ t('loans.fixedRateUntil') }}</Label>
                <Input v-model="form.fixed_rate_until" type="date" />
              </div>
            </div>
          </template>

          <DialogFooter>
            <Button type="button" variant="outline" @click="showDialog = false">{{ t('loans.cancel') }}</Button>
            <Button type="submit">{{ t('loans.save') }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>
