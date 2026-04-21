<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'
import AppNav from '@/components/AppNav.vue'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useRouter } from 'vue-router'

ChartJS.register(ArcElement, Tooltip, Legend)

const CHART_COLORS = ['#6366f1','#10b981','#f59e0b','#3b82f6','#ec4899','#8b5cf6','#14b8a6','#f97316']

const { t, locale } = useI18n()
const router = useRouter()
const api = useApi()

const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const summary = ref({ income: 0, expenses: 0, balance: 0 })
const sollIst = ref([])
const balances = ref([])

const monthLabel = computed(() =>
  new Date(year.value, month.value - 1, 1).toLocaleDateString(
    locale.value === 'de' ? 'de-DE' : 'en-US',
    { month: 'long', year: 'numeric' }
  )
)

const donutData = computed(() => {
  const expenseNodes = []
  function walk(nodes) {
    for (const n of nodes) {
      if (n.category_type !== 'income' && Math.abs(parseFloat(n.ist)) > 0) {
        expenseNodes.push({ name: n.name, value: Math.abs(parseFloat(n.ist)) })
      }
      if (n.children) walk(n.children)
    }
  }
  walk(sollIst.value)
  return expenseNodes
})

const donutChartData = computed(() => ({
  labels: donutData.value.map((d) => d.name),
  datasets: [{
    data: donutData.value.map((d) => d.value),
    backgroundColor: donutData.value.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]),
    borderWidth: 0,
    hoverOffset: 8,
  }],
}))

const donutOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: { position: 'right', labels: { boxWidth: 12, padding: 12, font: { size: 12 } } },
    tooltip: {
      callbacks: {
        label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toFixed(2)} €`,
      },
    },
  },
}

async function load() {
  const [sumRes, siRes, balRes] = await Promise.all([
    api.get(`/transactions/summary?year=${year.value}&month=${month.value}`),
    api.get(`/categories/soll-ist?year=${year.value}&month=${month.value}`),
    api.get('/accounts/balances'),
  ])
  if (!sumRes.ok || !siRes.ok || !balRes.ok) {
    toast.error(t('errors.generic'))
    return
  }
  summary.value = await sumRes.json()
  sollIst.value = await siRes.json()
  balances.value = await balRes.json()
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

function fmt(val) {
  return parseFloat(val).toFixed(2).replace('.', ',') + ' €'
}

onMounted(load)
</script>

<template>
  <div class="min-h-dvh bg-background">
    <AppNav />
    <main class="max-w-screen-xl mx-auto px-4 py-6 space-y-6">

      <!-- Month nav -->
      <div class="flex items-center justify-between flex-wrap gap-3">
        <div class="flex items-center gap-3">
          <Button variant="outline" size="sm" @click="prevMonth">←</Button>
          <span class="text-lg font-semibold min-w-44 text-center">{{ monthLabel }}</span>
          <Button variant="outline" size="sm" @click="nextMonth">→</Button>
        </div>
        <Button @click="router.push('/transactions')">{{ t('dashboard.addTransaction') }}</Button>
      </div>

      <!-- Summary cards -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardHeader class="pb-1">
            <CardTitle class="text-xs uppercase tracking-wider text-muted-foreground font-medium">
              {{ t('dashboard.income') }}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-2xl font-bold text-emerald-500 tabular-nums">{{ fmt(summary.income) }}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader class="pb-1">
            <CardTitle class="text-xs uppercase tracking-wider text-muted-foreground font-medium">
              {{ t('dashboard.expenses') }}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-2xl font-bold text-rose-500 tabular-nums">{{ fmt(summary.expenses) }}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader class="pb-1">
            <CardTitle class="text-xs uppercase tracking-wider text-muted-foreground font-medium">
              {{ t('dashboard.balance') }}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-2xl font-bold tabular-nums"
               :class="parseFloat(summary.balance) >= 0 ? 'text-primary' : 'text-rose-500'">
              {{ fmt(summary.balance) }}
            </p>
          </CardContent>
        </Card>
      </div>

      <!-- Soll/Ist + Donut -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Soll/Ist progress bars -->
        <Card>
          <CardHeader class="pb-2">
            <CardTitle class="text-sm uppercase tracking-wider text-muted-foreground">
              {{ t('dashboard.sollIst') }}
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-0 p-0">
            <template v-if="sollIst.length === 0">
              <p class="text-sm text-muted-foreground text-center py-8">{{ t('dashboard.noData') }}</p>
            </template>
            <template v-else>
              <SollIstRow v-for="node in sollIst" :key="node.id" :node="node" :depth="0" />
            </template>
          </CardContent>
        </Card>

        <!-- Donut chart -->
        <Card>
          <CardHeader class="pb-2">
            <CardTitle class="text-sm uppercase tracking-wider text-muted-foreground">
              {{ t('reports.chart.expensesByCategory') }}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Doughnut
              v-if="donutData.length > 0"
              :data="donutChartData"
              :options="donutOptions"
              class="max-h-64"
            />
            <p v-else class="text-sm text-muted-foreground text-center py-8">
              {{ t('dashboard.noData') }}
            </p>
          </CardContent>
        </Card>
      </div>

      <!-- Account balances -->
      <div>
        <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {{ t('dashboard.accounts') }}
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <Card v-for="acc in balances" :key="acc.id" class="flex-row items-center">
            <CardContent class="flex items-center justify-between p-4 w-full">
              <span class="text-sm text-muted-foreground">{{ acc.name }}</span>
              <span class="text-sm font-semibold tabular-nums"
                    :class="parseFloat(acc.balance) >= 0 ? 'text-emerald-500' : 'text-rose-500'">
                {{ parseFloat(acc.balance) >= 0 ? '+' : '' }}{{ parseFloat(acc.balance).toFixed(2).replace('.', ',') }} €
              </span>
            </CardContent>
          </Card>
        </div>
      </div>

    </main>
  </div>
</template>

<script>
// Recursive sub-component for Soll/Ist rows
const SollIstRow = {
  name: 'SollIstRow',
  props: { node: Object, depth: Number },
  setup(props) {
    const pct = parseFloat(props.node.soll) > 0
      ? Math.min(100, Math.abs(parseFloat(props.node.ist) / parseFloat(props.node.soll) * 100))
      : 0
    const over = pct >= 100
    return { pct, over }
  },
  template: `
    <div>
      <div class="px-4 py-3 border-b border-border last:border-0"
           :style="{ paddingLeft: (depth * 16 + 16) + 'px' }">
        <div class="flex justify-between items-center mb-1">
          <span class="text-sm">{{ node.name }}</span>
          <div class="flex gap-4 text-xs tabular-nums">
            <span :class="over ? 'text-rose-500' : 'text-foreground'">
              {{ parseFloat(node.ist).toFixed(2).replace('.', ',') }} €
            </span>
            <span class="text-muted-foreground">/ {{ parseFloat(node.soll).toFixed(2).replace('.', ',') }} €</span>
          </div>
        </div>
        <div class="h-1 rounded-full bg-muted overflow-hidden">
          <div class="h-full rounded-full transition-all"
               :style="{ width: pct + '%' }"
               :class="over ? 'bg-rose-500' : 'bg-primary'" />
        </div>
      </div>
      <SollIstRow v-for="child in node.children" :key="child.id" :node="child" :depth="depth + 1" />
    </div>
  `,
  components: { SollIstRow: null },
}
SollIstRow.components.SollIstRow = SollIstRow
</script>
