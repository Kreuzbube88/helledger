<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Doughnut, Bar, Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement, CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'

ChartJS.register(
  ArcElement, CategoryScale, LinearScale, BarElement, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
)

const COLORS = ['#6366f1','#10b981','#f59e0b','#3b82f6','#ec4899','#8b5cf6','#14b8a6','#f97316']

const { t, locale } = useI18n()
const api = useApi()

const mode = ref('month')
const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const fromDate = ref('')
const toDate = ref('')
const accountId = ref('')
const accounts = ref([])
const activeTab = ref('expenses')

const catData = ref(null)
const trendData = ref(null)
const sollIstData = ref(null)
const balanceData = ref(null)
const loanList = ref([])
const selectedLoanId = ref('')
const loanAmortization = ref([])

function lastDayOf(y, m) {
  return new Date(y, m, 0).getDate()
}

function pad(n) { return String(n).padStart(2, '0') }

const dateRange = computed(() => {
  if (mode.value === 'month') {
    return {
      from: `${year.value}-${pad(month.value)}-01`,
      to: `${year.value}-${pad(month.value)}-${pad(lastDayOf(year.value, month.value))}`,
    }
  }
  if (mode.value === 'year') {
    return { from: `${year.value}-01-01`, to: `${year.value}-12-31` }
  }
  return { from: fromDate.value, to: toDate.value }
})

function buildQs() {
  const p = new URLSearchParams({ from_date: dateRange.value.from, to_date: dateRange.value.to })
  if (accountId.value && accountId.value !== '__all__') p.set('account_id', accountId.value)
  return p.toString()
}

async function loadData() {
  const { from, to } = dateRange.value
  if (!from || !to || from > to) return
  const [catRes, trendRes, siRes] = await Promise.all([
    api.get(`/reports/expenses-by-category?${buildQs()}`),
    api.get(`/reports/monthly-trend?${buildQs()}`),
    api.get(`/reports/soll-ist?${buildQs()}`),
  ])
  if (catRes.ok) catData.value = await catRes.json()
  if (trendRes.ok) trendData.value = await trendRes.json()
  if (siRes.ok) sollIstData.value = await siRes.json()

  if (accountId.value && accountId.value !== '__all__') {
    const balRes = await api.get(`/reports/balance-history?from_date=${from}&to_date=${to}&account_id=${accountId.value}`)
    if (balRes.ok) balanceData.value = await balRes.json()
  } else {
    balanceData.value = null
  }
}

const donutChartData = computed(() => ({
  labels: (catData.value || []).map((d) => d.category_name),
  datasets: [{
    data: (catData.value || []).map((d) => parseFloat(d.total)),
    backgroundColor: (catData.value || []).map((_, i) => COLORS[i % COLORS.length]),
    borderWidth: 0,
  }],
}))

const trendChartData = computed(() => {
  const data = trendData.value || []
  const lang = locale.value === 'de' ? 'de-DE' : 'en-US'
  return {
    labels: data.map((d) =>
      new Date(d.year, d.month - 1, 1).toLocaleDateString(lang, { month: 'short', year: '2-digit' })
    ),
    datasets: [
      {
        label: t('dashboard.income'),
        data: data.map((d) => parseFloat(d.income)),
        backgroundColor: 'rgba(16,185,129,0.7)',
        borderColor: '#10b981',
        borderWidth: 1,
        borderRadius: 4,
      },
      {
        label: t('dashboard.expenses'),
        data: data.map((d) => parseFloat(d.expenses)),
        backgroundColor: 'rgba(244,63,94,0.7)',
        borderColor: '#f43f5e',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  }
})

const sollIstFlat = computed(() => {
  const flat = []
  function walk(nodes) {
    for (const n of nodes) {
      if (parseFloat(n.soll) !== 0 || parseFloat(n.ist) !== 0) flat.push(n)
      if (n.children) walk(n.children)
    }
  }
  walk(sollIstData.value || [])
  return flat
})

const sollIstChartData = computed(() => ({
  labels: sollIstFlat.value.map((n) => n.name),
  datasets: [
    {
      label: t('dashboard.soll'),
      data: sollIstFlat.value.map((n) => parseFloat(n.soll)),
      backgroundColor: 'rgba(99,102,241,0.6)',
      borderColor: '#6366f1',
      borderWidth: 1,
      borderRadius: 4,
    },
    {
      label: t('dashboard.ist'),
      data: sollIstFlat.value.map((n) => Math.abs(parseFloat(n.ist))),
      backgroundColor: 'rgba(16,185,129,0.6)',
      borderColor: '#10b981',
      borderWidth: 1,
      borderRadius: 4,
    },
  ],
}))

const balanceChartData = computed(() => ({
  labels: (balanceData.value || []).map((d) => d.date),
  datasets: [{
    label: t('reports.chart.balanceHistory'),
    data: (balanceData.value || []).map((d) => parseFloat(d.balance)),
    borderColor: '#6366f1',
    backgroundColor: 'rgba(99,102,241,0.12)',
    fill: true,
    tension: 0.3,
  }],
}))

const barOptions = {
  responsive: true,
  plugins: { legend: { position: 'top' } },
  scales: { x: { grid: { display: false } }, y: { beginAtZero: true } },
}

const hBarOptions = {
  indexAxis: 'y',
  responsive: true,
  plugins: { legend: { position: 'top' } },
  scales: { x: { beginAtZero: true } },
}

const donutOptions = { responsive: true, plugins: { legend: { position: 'right' } } }
const lineOptions = { responsive: true, plugins: { legend: { display: false } } }

function downloadCsv(data, filename) {
  if (!data?.length) return
  const headers = Object.keys(data[0]).join(',')
  const rows = data.map((r) => Object.values(r).map((v) => `"${v}"`).join(',')).join('\n')
  const blob = new Blob([headers + '\n' + rows], { type: 'text/csv' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

const years = Array.from({ length: 4 }, (_, i) => new Date().getFullYear() - 1 + i)

async function loadLoanAmortization() {
  if (!selectedLoanId.value) { loanAmortization.value = []; return }
  const res = await api.get(`/loans/${selectedLoanId.value}/amortization`)
  if (res.ok) loanAmortization.value = await res.json()
}

const loanBalanceChartData = computed(() => {
  const rows = loanAmortization.value
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

onMounted(async () => {
  const [accRes, loanRes] = await Promise.all([api.get('/accounts'), api.get('/loans')])
  if (accRes.ok) accounts.value = await accRes.json()
  if (loanRes.ok) loanList.value = await loanRes.json()
  await loadData()
})
</script>

<template>
  <div class="min-h-dvh bg-background">
    <main class="max-w-screen-xl mx-auto px-4 py-6 space-y-6">
      <h1 class="text-2xl font-bold">{{ t('reports.title') }}</h1>

      <!-- Filter bar -->
      <Card>
        <CardContent class="p-4 flex flex-wrap items-center gap-3">
          <!-- Mode tabs -->
          <div class="flex rounded-md border overflow-hidden">
            <button
              v-for="m in ['month', 'year', 'custom']"
              :key="m"
              class="px-4 py-1.5 text-sm transition-colors"
              :class="mode === m ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted'"
              @click="mode = m; loadData()"
            >
              {{ t(`reports.period.${m}`) }}
            </button>
          </div>

          <!-- Month/Year pickers -->
          <template v-if="mode === 'month'">
            <Select v-model="month" @update:modelValue="loadData">
              <SelectTrigger class="w-32"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem v-for="m in 12" :key="m" :value="m">
                  {{ new Date(2000, m - 1).toLocaleDateString(locale === 'de' ? 'de-DE' : 'en-US', { month: 'long' }) }}
                </SelectItem>
              </SelectContent>
            </Select>
          </template>

          <template v-if="mode !== 'custom'">
            <Select v-model="year" @update:modelValue="loadData">
              <SelectTrigger class="w-24"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem v-for="y in years" :key="y" :value="y">{{ y }}</SelectItem>
              </SelectContent>
            </Select>
          </template>

          <template v-if="mode === 'custom'">
            <Input v-model="fromDate" type="date" class="w-36" @change="loadData" />
            <span class="text-muted-foreground">→</span>
            <Input v-model="toDate" type="date" class="w-36" @change="loadData" />
          </template>

          <!-- Account filter -->
          <Select v-model="accountId" class="ml-auto" @update:modelValue="loadData">
            <SelectTrigger class="w-44"><SelectValue :placeholder="t('reports.filter.allAccounts')" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">{{ t('reports.filter.allAccounts') }}</SelectItem>
              <SelectItem v-for="acc in accounts" :key="acc.id" :value="String(acc.id)">{{ acc.name }}</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      <!-- Charts -->
      <Tabs v-model="activeTab">
        <TabsList>
          <TabsTrigger value="expenses">{{ t('reports.chart.expensesByCategory') }}</TabsTrigger>
          <TabsTrigger value="trend">{{ t('reports.chart.monthlyTrend') }}</TabsTrigger>
          <TabsTrigger value="balance">{{ t('reports.chart.balanceHistory') }}</TabsTrigger>
          <TabsTrigger value="sollist">{{ t('reports.chart.sollIst') }}</TabsTrigger>
          <TabsTrigger value="loans">{{ t('loans.title') }}</TabsTrigger>
        </TabsList>

        <TabsContent value="expenses">
          <Card>
            <CardHeader class="flex-row items-center justify-between pb-2">
              <CardTitle class="text-sm">{{ t('reports.chart.expensesByCategory') }}</CardTitle>
              <Button variant="outline" size="sm" @click="downloadCsv(catData, 'expenses-by-category.csv')">
                {{ t('reports.export.csv') }}
              </Button>
            </CardHeader>
            <CardContent>
              <Doughnut v-if="catData?.length" :data="donutChartData" :options="donutOptions" class="max-h-80" />
              <p v-else class="text-center text-muted-foreground py-12">{{ t('reports.noData') }}</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trend">
          <Card>
            <CardHeader class="flex-row items-center justify-between pb-2">
              <CardTitle class="text-sm">{{ t('reports.chart.monthlyTrend') }}</CardTitle>
              <Button variant="outline" size="sm" @click="downloadCsv(trendData, 'monthly-trend.csv')">
                {{ t('reports.export.csv') }}
              </Button>
            </CardHeader>
            <CardContent>
              <Bar v-if="trendData?.length" :data="trendChartData" :options="barOptions" class="max-h-80" />
              <p v-else class="text-center text-muted-foreground py-12">{{ t('reports.noData') }}</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="balance">
          <Card>
            <CardHeader class="pb-2">
              <CardTitle class="text-sm">{{ t('reports.chart.balanceHistory') }}</CardTitle>
            </CardHeader>
            <CardContent>
              <Line v-if="balanceData?.length" :data="balanceChartData" :options="lineOptions" class="max-h-80" />
              <p v-else class="text-center text-muted-foreground py-12">
                {{ accountId ? t('reports.noData') : t('reports.selectAccount') }}
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sollist">
          <Card>
            <CardHeader class="flex-row items-center justify-between pb-2">
              <CardTitle class="text-sm">{{ t('reports.chart.sollIst') }}</CardTitle>
              <Button variant="outline" size="sm" @click="downloadCsv(sollIstFlat, 'soll-ist.csv')">
                {{ t('reports.export.csv') }}
              </Button>
            </CardHeader>
            <CardContent>
              <Bar v-if="sollIstFlat.length" :data="sollIstChartData" :options="hBarOptions" class="max-h-80" />
              <p v-else class="text-center text-muted-foreground py-12">{{ t('reports.noData') }}</p>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="loans">
          <Card>
            <CardHeader class="pb-2">
              <CardTitle class="text-sm">{{ t('loans.title') }}</CardTitle>
            </CardHeader>
            <CardContent class="space-y-4">
              <Select v-model="selectedLoanId" @update:modelValue="loadLoanAmortization">
                <SelectTrigger class="w-64">
                  <SelectValue :placeholder="t('loans.title')" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="loan in loanList" :key="loan.id" :value="String(loan.id)">
                    {{ loan.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
              <Line v-if="loanAmortization.length" :data="loanBalanceChartData" :options="lineOptions" class="max-h-80" />
              <p v-else class="text-center text-muted-foreground py-8">{{ selectedLoanId ? t('reports.noData') : t('loans.noData') }}</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </main>
  </div>
</template>
