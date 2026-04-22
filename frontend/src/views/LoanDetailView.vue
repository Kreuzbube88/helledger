<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useConfirm } from '@/composables/useConfirm'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { toast } from 'vue-sonner'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const { t } = useI18n()
const { confirm } = useConfirm()
const api = useApi()
const route = useRoute()
const router = useRouter()

const loanId = route.params.id
const loan = ref(null)
const amortization = ref([])
const extraPayments = ref([])
const stats = ref(null)
const activeTab = ref('overview')

const showEpDialog = ref(false)
const epForm = ref({ payment_date: new Date().toISOString().slice(0, 10), amount: '', effect: 'shorten_term', notes: '', interval_months: '0', end_date: '' })

async function load() {
  const [loanRes, amoRes, epsRes, statsRes] = await Promise.all([
    api.get(`/loans/${loanId}`),
    api.get(`/loans/${loanId}/amortization`),
    api.get(`/loans/${loanId}/extra-payments`),
    api.get(`/loans/${loanId}/stats`),
  ])
  if (loanRes.ok) loan.value = await loanRes.json()
  if (amoRes.ok) amortization.value = await amoRes.json()
  if (epsRes.ok) extraPayments.value = await epsRes.json()
  if (statsRes.ok) stats.value = await statsRes.json()
}

// Chart: balance over time
const balanceChartData = computed(() => {
  const rows = amortization.value
  const step = Math.max(1, Math.floor(rows.length / 60))
  const sampled = rows.filter((_, i) => i % step === 0 || i === rows.length - 1)
  return {
    labels: sampled.map(r => r.date.slice(0, 7)),
    datasets: [{
      label: t('loans.currentBalance'),
      data: sampled.map(r => r.balance),
      borderColor: '#6366f1',
      backgroundColor: 'rgba(99,102,241,0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 0,
    }],
  }
})

const lineOptions = {
  responsive: true,
  plugins: { legend: { display: false } },
  scales: { x: { ticks: { maxTicksLimit: 10 } }, y: { beginAtZero: true } },
}

async function addExtraPayment() {
  const intervalMonths = parseInt(epForm.value.interval_months) || 0
  const body = {
    payment_date: epForm.value.payment_date,
    amount: parseFloat(epForm.value.amount),
    effect: intervalMonths > 0 ? 'shorten_term' : epForm.value.effect,
    notes: epForm.value.notes || null,
    interval_months: intervalMonths > 0 ? intervalMonths : null,
    end_date: intervalMonths > 0 && epForm.value.end_date ? epForm.value.end_date : null,
  }
  const res = await api.post(`/loans/${loanId}/extra-payments`, body)
  if (res.ok) {
    showEpDialog.value = false
    await load()
    toast.success(t('loans.extraPayment.add'))
  } else {
    toast.error(t('errors.generic'))
  }
}

async function removeExtraPayment(epId) {
  if (!await confirm(t('loans.delete') + '?')) return
  const res = await api.delete(`/loans/${loanId}/extra-payments/${epId}`)
  if (res.ok) { await load(); toast.success(t('loans.delete')) }
  else toast.error(t('errors.generic'))
}

async function markPaidOff() {
  if (!await confirm(t('loans.confirmPaidOff'))) return
  const res = await api.patch(`/loans/${loanId}/mark-paid-off`, {})
  if (res.ok) {
    await load()
    toast.success(t('loans.markPaidOff'))
  } else {
    toast.error(t('errors.generic'))
  }
}

function downloadCsv() {
  api.get(`/loans/${loanId}/amortization/csv`).then(res => {
    if (!res.ok) return
    res.blob().then(blob => {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `tilgungsplan-${loan.value?.name || loanId}.csv`
      a.click()
      URL.revokeObjectURL(a.href)
    })
  })
}

function fmt(val, decimals = 2) {
  if (val == null) return '—'
  return parseFloat(val).toLocaleString('de-DE', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

onMounted(load)
</script>

<template>
  <div class="min-h-dvh bg-background">
    <main class="max-w-5xl mx-auto px-4 py-6 space-y-4">
      <!-- Header -->
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="sm" @click="router.push('/loans')">←</Button>
        <div class="flex-1 min-w-0">
          <h1 class="text-2xl font-bold truncate">{{ loan?.name || '…' }}</h1>
          <p class="text-sm text-muted-foreground">
            {{ loan ? t(`loans.types.${loan.loan_type}`) : '' }}
            <span v-if="loan?.lender"> · {{ loan.lender }}</span>
          </p>
        </div>
        <Badge v-if="loan" :variant="loan.status === 'active' ? 'default' : 'secondary'">
          {{ t(`loans.statuses.${loan.status}`) }}
        </Badge>
      </div>

      <Tabs v-model="activeTab">
        <TabsList>
          <TabsTrigger value="overview">{{ t('loans.detail.overview') }}</TabsTrigger>
          <TabsTrigger value="amortization">{{ t('loans.detail.amortization') }}</TabsTrigger>
          <TabsTrigger value="extraPayments">{{ t('loans.detail.extraPayments') }}</TabsTrigger>
          <TabsTrigger value="settings">{{ t('loans.detail.settings') }}</TabsTrigger>
        </TabsList>

        <!-- Overview tab -->
        <TabsContent value="overview" class="space-y-4">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4" v-if="loan && stats">
            <Card>
              <CardContent class="pt-4 pb-3 space-y-1">
                <p class="text-xs text-muted-foreground">{{ t('loans.currentBalance') }}</p>
                <p class="text-xl font-bold text-rose-500">{{ fmt(stats.current_balance) }} €</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent class="pt-4 pb-3 space-y-1">
                <p class="text-xs text-muted-foreground">{{ t('loans.monthlyRate') }}</p>
                <p class="text-xl font-bold">{{ fmt(loan.monthly_payment) }} €</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent class="pt-4 pb-3 space-y-1">
                <p class="text-xs text-muted-foreground">{{ t('loans.stats.totalInterest') }}</p>
                <p class="text-xl font-bold text-amber-500">{{ fmt(stats.total_interest) }} €</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent class="pt-4 pb-3 space-y-1">
                <p class="text-xs text-muted-foreground">{{ t('loans.stats.payoffDate') }}</p>
                <p class="text-xl font-bold">{{ stats.payoff_date?.slice(0, 7) || '—' }}</p>
              </CardContent>
            </Card>
            <Card v-if="stats.interest_saved > 0 || stats.months_saved > 0">
              <CardContent class="pt-4 pb-3 space-y-1">
                <p class="text-xs text-muted-foreground">{{ t('loans.stats.interestSaved') }}</p>
                <p class="text-xl font-bold text-emerald-500">{{ fmt(stats.interest_saved) }} €</p>
              </CardContent>
            </Card>
            <Card v-if="stats.months_saved > 0">
              <CardContent class="pt-4 pb-3 space-y-1">
                <p class="text-xs text-muted-foreground">{{ t('loans.stats.monthsSaved') }}</p>
                <p class="text-xl font-bold text-emerald-500">{{ stats.months_saved }} Mo.</p>
              </CardContent>
            </Card>
            <!-- Mortgage extras -->
            <template v-if="loan.loan_type === 'mortgage'">
              <Card v-if="loan.ltv">
                <CardContent class="pt-4 pb-3 space-y-1">
                  <p class="text-xs text-muted-foreground">{{ t('loans.ltv') }}</p>
                  <p class="text-xl font-bold">{{ fmt(loan.ltv, 1) }} %</p>
                </CardContent>
              </Card>
              <Card v-if="loan.fixed_rate_until">
                <CardContent class="pt-4 pb-3 space-y-1">
                  <p class="text-xs text-muted-foreground">{{ t('loans.fixedRateUntil') }}</p>
                  <p class="text-xl font-bold" :class="loan.fixed_rate_expiring_soon ? 'text-amber-500' : ''">
                    {{ loan.fixed_rate_until }}
                    <span v-if="loan.fixed_rate_expiring_soon" class="text-xs ml-1">⚠</span>
                  </p>
                </CardContent>
              </Card>
            </template>
          </div>

          <!-- Balance chart -->
          <Card v-if="amortization.length">
            <CardHeader class="pb-2">
              <CardTitle class="text-sm">{{ t('loans.currentBalance') }}</CardTitle>
            </CardHeader>
            <CardContent>
              <Line :data="balanceChartData" :options="lineOptions" class="max-h-64" />
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Amortization tab -->
        <TabsContent value="amortization">
          <Card>
            <CardHeader class="flex-row items-center justify-between pb-2">
              <CardTitle class="text-sm">{{ t('loans.detail.amortization') }}</CardTitle>
              <Button variant="outline" size="sm" @click="downloadCsv">{{ t('loans.exportCsv') }}</Button>
            </CardHeader>
            <CardContent class="p-0">
              <div class="overflow-x-auto max-h-[60vh] overflow-y-auto">
                <table class="w-full text-sm">
                  <thead class="sticky top-0 bg-card border-b">
                    <tr class="text-muted-foreground text-xs">
                      <th class="text-right px-3 py-2 w-12">#</th>
                      <th class="text-left px-3 py-2">{{ t('loans.amortization.date') }}</th>
                      <th class="text-right px-3 py-2">{{ t('loans.amortization.payment') }}</th>
                      <th class="text-right px-3 py-2">{{ t('loans.amortization.interest') }}</th>
                      <th class="text-right px-3 py-2">{{ t('loans.amortization.principal') }}</th>
                      <th class="text-right px-3 py-2">{{ t('loans.amortization.extra') }}</th>
                      <th class="text-right px-3 py-2">{{ t('loans.amortization.balance') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="row in amortization" :key="row.month"
                      class="border-b hover:bg-muted/40 tabular-nums"
                      :class="row.extra > 0 ? 'bg-violet-500/5' : ''"
                    >
                      <td class="text-right px-3 py-1.5 text-muted-foreground">{{ row.month }}</td>
                      <td class="px-3 py-1.5">{{ row.date.slice(0, 7) }}</td>
                      <td class="text-right px-3 py-1.5">{{ fmt(row.payment) }}</td>
                      <td class="text-right px-3 py-1.5 text-amber-600">{{ fmt(row.interest) }}</td>
                      <td class="text-right px-3 py-1.5 text-emerald-600">{{ fmt(row.principal) }}</td>
                      <td class="text-right px-3 py-1.5 text-violet-500">{{ row.extra > 0 ? fmt(row.extra) : '—' }}</td>
                      <td class="text-right px-3 py-1.5 font-medium">{{ fmt(row.balance) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Extra payments tab -->
        <TabsContent value="extraPayments" class="space-y-4">
          <div class="flex justify-end">
            <Button @click="showEpDialog = true" :disabled="loan?.status === 'paid_off'">{{ t('loans.extraPayment.add') }}</Button>
          </div>

          <Card>
            <CardContent class="p-0">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b text-muted-foreground text-xs">
                    <th class="text-left px-4 py-2">{{ t('loans.extraPayment.date') }}</th>
                    <th class="text-right px-4 py-2">{{ t('loans.extraPayment.amount') }}</th>
                    <th class="px-4 py-2">{{ t('loans.extraPayment.effect') }}</th>
                    <th class="px-4 py-2">{{ t('loans.extraPayment.notes') }}</th>
                    <th class="text-right px-4 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="extraPayments.length === 0">
                    <td colspan="5" class="text-center text-muted-foreground py-8 px-4">{{ t('loans.noData') }}</td>
                  </tr>
                  <tr v-for="ep in extraPayments" :key="ep.id" class="border-b hover:bg-muted/40">
                    <td class="px-4 py-2">{{ ep.payment_date }}</td>
                    <td class="text-right px-4 py-2 tabular-nums text-violet-500 font-medium">{{ fmt(ep.amount) }} €</td>
                    <td class="px-4 py-2 text-sm">
                      <span v-if="ep.interval_months" class="text-violet-500">
                        {{ t(`fixedCosts.intervals.${ep.interval_months}`) }}
                        <span v-if="ep.end_date" class="text-muted-foreground text-xs"> bis {{ ep.end_date }}</span>
                      </span>
                      <span v-else>{{ t(`loans.extraPayment.effects.${ep.effect}`) }}</span>
                    </td>
                    <td class="px-4 py-2 text-muted-foreground text-sm">{{ ep.notes || '—' }}</td>
                    <td class="text-right px-4 py-2 whitespace-nowrap">
                      <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="removeExtraPayment(ep.id)">
                        {{ t('loans.delete') }}
                      </Button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Settings tab -->
        <TabsContent value="settings" class="space-y-4">
          <Card>
            <CardContent class="pt-6 space-y-4">
              <div>
                <p class="font-medium mb-1">{{ t('loans.markPaidOff') }}</p>
                <p class="text-sm text-muted-foreground mb-3">{{ t('loans.confirmPaidOff') }}</p>
                <Button
                  variant="outline"
                  :disabled="loan?.status === 'paid_off'"
                  @click="markPaidOff"
                >{{ t('loans.markPaidOff') }}</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </main>

    <!-- Extra payment dialog -->
    <Dialog v-model:open="showEpDialog">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ t('loans.extraPayment.add') }}</DialogTitle>
        </DialogHeader>
        <form @submit.prevent="addExtraPayment" class="space-y-4">
          <div class="space-y-1">
            <Label>{{ t('loans.extraPayment.date') }}</Label>
            <Input v-model="epForm.payment_date" type="date" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('loans.extraPayment.amount') }}</Label>
            <Input v-model="epForm.amount" type="number" step="0.01" min="0.01" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('loans.extraPayment.intervalMonths') }}</Label>
            <Select v-model="epForm.interval_months">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="0">{{ t('loans.extraPayment.oneTime') }}</SelectItem>
                <SelectItem value="1">{{ t('fixedCosts.intervals.1') }}</SelectItem>
                <SelectItem value="3">{{ t('fixedCosts.intervals.3') }}</SelectItem>
                <SelectItem value="6">{{ t('fixedCosts.intervals.6') }}</SelectItem>
                <SelectItem value="12">{{ t('fixedCosts.intervals.12') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div v-if="parseInt(epForm.interval_months) > 0" class="space-y-1">
            <Label>{{ t('loans.extraPayment.endDate') }}</Label>
            <Input v-model="epForm.end_date" type="date" />
          </div>
          <div v-if="parseInt(epForm.interval_months) === 0" class="space-y-1">
            <Label>{{ t('loans.extraPayment.effect') }}</Label>
            <Select v-model="epForm.effect">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="shorten_term">{{ t('loans.extraPayment.effects.shorten_term') }}</SelectItem>
                <SelectItem value="reduce_payment">{{ t('loans.extraPayment.effects.reduce_payment') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-1">
            <Label>{{ t('loans.extraPayment.notes') }}</Label>
            <Input v-model="epForm.notes" />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" @click="showEpDialog = false">{{ t('loans.cancel') }}</Button>
            <Button type="submit">{{ t('loans.save') }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>
