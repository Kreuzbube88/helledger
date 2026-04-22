<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { Doughnut } from 'vue-chartjs'
import { TrendingUp, TrendingDown, Plus, ArrowRight } from 'lucide-vue-next'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { useApi } from '@/lib/api'
import { useRouter } from 'vue-router'
import { useThemeStore } from '@/stores/theme'

ChartJS.register(ArcElement, Tooltip, Legend)

const CHART_COLORS = [
  '#10b981','#8b5cf6','#3b82f6','#f59e0b',
  '#ec4899','#14b8a6','#f97316','#06b6d4',
]

const { t, locale } = useI18n()
const router = useRouter()
const theme = useThemeStore()
const api = useApi()

const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const summary = ref({ income: 0, expenses: 0, balance: 0 })
const sollIst = ref([])
const balances = ref([])

const monthLabel = computed(() =>
  new Date(year.value, month.value - 1, 1).toLocaleDateString(
    locale.value === 'de' ? 'de-DE' : 'en-US',
    { month: 'long', year: 'numeric' },
  )
)

const donutData = computed(() => {
  const nodes = []
  function walk(list) {
    for (const n of list) {
      if (n.category_type !== 'income' && Math.abs(parseFloat(n.ist)) > 0)
        nodes.push({ name: n.name, value: Math.abs(parseFloat(n.ist)) })
      if (n.children) walk(n.children)
    }
  }
  walk(sollIst.value)
  return nodes
})

const donutChartData = computed(() => ({
  labels: donutData.value.map((d) => d.name),
  datasets: [{
    data: donutData.value.map((d) => d.value),
    backgroundColor: donutData.value.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]),
    borderWidth: 0,
    hoverOffset: 10,
  }],
}))

const donutOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: true,
  cutout: '72%',
  plugins: {
    legend: {
      position: 'right',
      labels: {
        boxWidth: 8,
        borderRadius: 4,
        padding: 10,
        font: { size: 11, family: 'Inter Variable, Inter, sans-serif' },
        color: theme.isDark ? '#6B7FA3' : '#64748b',
      },
    },
    tooltip: {
      callbacks: { label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toFixed(2)} €` },
    },
  },
}))

async function load() {
  const [sumRes, siRes, balRes] = await Promise.all([
    api.get(`/transactions/summary?year=${year.value}&month=${month.value}`),
    api.get(`/categories/soll-ist?year=${year.value}&month=${month.value}`),
    api.get('/accounts/balances'),
  ])
  if (!sumRes.ok || !siRes.ok || !balRes.ok) { toast.error(t('errors.generic')); return }
  summary.value = await sumRes.json()
  sollIst.value = await siRes.json()
  balances.value = await balRes.json()
}

function prevMonth() {
  month.value--; if (month.value < 1) { month.value = 12; year.value-- }; load()
}
function nextMonth() {
  month.value++; if (month.value > 12) { month.value = 1; year.value++ }; load()
}

function fmt(val) {
  return parseFloat(val).toFixed(2).replace('.', ',') + ' €'
}

const balancePositive = computed(() => parseFloat(summary.value.balance) >= 0)

onMounted(load)
</script>

<template>
  <main class="max-w-screen-lg mx-auto px-4 py-6 space-y-5">

    <!-- ── Hero header ─────────────────────────────────────────────── -->
    <div class="flex items-start justify-between pt-2 pb-1">
      <div>
        <p class="text-xs text-muted-foreground uppercase tracking-widest mb-2">{{ monthLabel }}</p>
        <h1
          class="text-4xl font-black tracking-tight tabular-nums"
          :class="balancePositive
            ? 'bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent'
            : 'bg-gradient-to-r from-rose-400 to-pink-300 bg-clip-text text-transparent'"
        >
          {{ fmt(summary.balance) }}
        </h1>
        <p class="text-xs text-muted-foreground mt-1.5">{{ t('dashboard.balance') }}</p>
      </div>
      <div class="flex items-center gap-2 mt-1">
        <button
          @click="prevMonth"
          class="h-8 w-8 rounded-xl flex items-center justify-center text-muted-foreground transition-colors"
          :class="theme.isDark ? 'bg-white/[0.05] hover:bg-white/[0.09]' : 'bg-gray-100 hover:bg-gray-200'"
        >‹</button>
        <button
          @click="nextMonth"
          class="h-8 w-8 rounded-xl flex items-center justify-center text-muted-foreground transition-colors"
          :class="theme.isDark ? 'bg-white/[0.05] hover:bg-white/[0.09]' : 'bg-gray-100 hover:bg-gray-200'"
        >›</button>
        <button
          @click="router.push('/transactions')"
          class="h-8 px-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-lg shadow-emerald-500/20"
        >
          <Plus class="h-3.5 w-3.5" />
          {{ t('dashboard.addTransaction') }}
        </button>
      </div>
    </div>

    <!-- ── Income / Expenses cards ─────────────────────────────────── -->
    <div class="grid grid-cols-2 gap-3">
      <!-- Income -->
      <div
        class="rounded-2xl p-4 border relative overflow-hidden"
        :class="theme.isDark
          ? 'bg-emerald-500/[0.07] border-emerald-500/[0.18]'
          : 'bg-emerald-50 border-emerald-100'"
      >
        <div class="absolute -top-6 -right-6 w-24 h-24 rounded-full bg-emerald-400/15 blur-2xl" />
        <TrendingUp class="h-4 w-4 text-emerald-400 mb-3 relative" />
        <p class="text-[11px] text-muted-foreground mb-1 relative">{{ t('dashboard.income') }}</p>
        <p class="text-xl font-bold text-emerald-400 tabular-nums relative">{{ fmt(summary.income) }}</p>
      </div>
      <!-- Expenses -->
      <div
        class="rounded-2xl p-4 border relative overflow-hidden"
        :class="theme.isDark
          ? 'bg-rose-500/[0.07] border-rose-500/[0.18]'
          : 'bg-rose-50 border-rose-100'"
      >
        <div class="absolute -top-6 -right-6 w-24 h-24 rounded-full bg-rose-400/15 blur-2xl" />
        <TrendingDown class="h-4 w-4 text-rose-400 mb-3 relative" />
        <p class="text-[11px] text-muted-foreground mb-1 relative">{{ t('dashboard.expenses') }}</p>
        <p class="text-xl font-bold text-rose-400 tabular-nums relative">{{ fmt(summary.expenses) }}</p>
      </div>
    </div>

    <!-- ── Budget vs. Actual + Donut ──────────────────────────────── -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Soll/Ist -->
      <div
        class="rounded-2xl border"
        :class="theme.isDark
          ? 'bg-card/60 backdrop-blur-lg border-white/[0.06]'
          : 'bg-white border-gray-100 shadow-sm'"
      >
        <div class="px-5 py-4 border-b"
             :class="theme.isDark ? 'border-white/[0.05]' : 'border-gray-100'">
          <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {{ t('dashboard.sollIst') }}
          </h2>
        </div>
        <div v-if="sollIst.length === 0" class="px-5 py-10 text-sm text-muted-foreground text-center">
          {{ t('dashboard.noData') }}
        </div>
        <div v-else>
          <SollIstRow v-for="node in sollIst" :key="node.id" :node="node" :depth="0" />
        </div>
      </div>

      <!-- Donut -->
      <div
        class="rounded-2xl border p-5"
        :class="theme.isDark
          ? 'bg-card/60 backdrop-blur-lg border-white/[0.06]'
          : 'bg-white border-gray-100 shadow-sm'"
      >
        <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4">
          {{ t('reports.chart.expensesByCategory') }}
        </h2>
        <Doughnut
          v-if="donutData.length > 0"
          :data="donutChartData"
          :options="donutOptions"
          class="max-h-52"
        />
        <p v-else class="text-sm text-muted-foreground text-center py-10">
          {{ t('dashboard.noData') }}
        </p>
      </div>
    </div>

    <!-- ── Account balances ────────────────────────────────────────── -->
    <div v-if="balances.length > 0">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {{ t('dashboard.accounts') }}
        </h2>
        <button
          @click="router.push('/accounts')"
          class="text-xs text-muted-foreground hover:text-emerald-400 transition-colors flex items-center gap-1"
        >
          {{ t('nav.accounts') }}
          <ArrowRight class="h-3 w-3" />
        </button>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div
          v-for="acc in balances"
          :key="acc.id"
          class="rounded-2xl border px-4 py-3 flex items-center justify-between"
          :class="theme.isDark
            ? 'bg-card/40 border-white/[0.05]'
            : 'bg-white border-gray-100 shadow-sm'"
        >
          <span class="text-sm text-muted-foreground">{{ acc.name }}</span>
          <span
            class="text-sm font-bold tabular-nums"
            :class="parseFloat(acc.balance) >= 0 ? 'text-emerald-400' : 'text-rose-400'"
          >
            {{ parseFloat(acc.balance) >= 0 ? '+' : '' }}{{ parseFloat(acc.balance).toFixed(2).replace('.', ',') }} €
          </span>
        </div>
      </div>
    </div>

  </main>
</template>

<script>
const SollIstRow = {
  name: 'SollIstRow',
  props: { node: Object, depth: Number },
  setup(props) {
    const pct = parseFloat(props.node.soll) > 0
      ? Math.min(100, Math.abs(parseFloat(props.node.ist) / parseFloat(props.node.soll) * 100))
      : 0
    return { pct, over: pct >= 100 }
  },
  template: `
    <div>
      <div class="px-5 py-2.5 border-b border-white/[0.04] last:border-0 group"
           :style="{ paddingLeft: (depth * 12 + 20) + 'px' }">
        <div class="flex justify-between items-center mb-1.5">
          <span class="text-sm">{{ node.name }}</span>
          <div class="flex gap-3 text-xs tabular-nums">
            <span :class="over ? 'text-rose-400 font-semibold' : ''">
              {{ parseFloat(node.ist).toFixed(2).replace('.', ',') }} €
            </span>
            <span class="text-muted-foreground">/ {{ parseFloat(node.soll).toFixed(2).replace('.', ',') }} €</span>
          </div>
        </div>
        <div class="h-1 rounded-full overflow-hidden" style="background:rgba(255,255,255,0.06)">
          <div class="h-full rounded-full transition-all duration-700"
               :style="{ width: pct + '%' }"
               :class="over ? 'bg-rose-500' : 'bg-emerald-500'" />
        </div>
      </div>
      <SollIstRow v-for="child in node.children" :key="child.id" :node="child" :depth="depth + 1" />
    </div>
  `,
  components: { SollIstRow: null },
}
SollIstRow.components.SollIstRow = SollIstRow
</script>
