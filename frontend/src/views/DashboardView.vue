<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { Doughnut } from 'vue-chartjs'
import { TrendingUp, TrendingDown, Plus, ArrowRight, Target } from 'lucide-vue-next'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { useApi } from '@/lib/api'
import { useRouter } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { useAuthStore } from '@/stores/auth'

ChartJS.register(ArcElement, Tooltip, Legend)

const CHART_COLORS = [
  '#10b981','#8b5cf6','#3b82f6','#f59e0b',
  '#ec4899','#14b8a6','#f97316','#06b6d4',
]

const { t, locale } = useI18n()
const router = useRouter()
const theme = useThemeStore()
const api = useApi()
const auth = useAuthStore()

const year  = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)
const summary  = ref({ income: 0, expenses: 0, balance: 0 })
const sollIst  = ref([])
const balances = ref([])
const loaded   = ref(false)
const expiringCats = ref([])
const monthlyReserve = ref(null)
const reserveOpen = ref(false)
const topGoals = ref([])

// ── Animated display values ────────────────────────────────────────
const display = reactive({ income: 0, expenses: 0, balance: 0 })

function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3) }

function animateTo(key, target, duration = 950) {
  const from  = display[key]
  const diff  = target - from
  if (Math.abs(diff) < 0.005) { display[key] = target; return }
  const start = performance.now()
  function frame(now) {
    const t = Math.min((now - start) / duration, 1)
    display[key] = from + diff * easeOutCubic(t)
    if (t < 1) requestAnimationFrame(frame)
    else display[key] = target
  }
  requestAnimationFrame(frame)
}

watch(summary, (val) => {
  animateTo('income',   parseFloat(val.income)   || 0)
  animateTo('expenses', parseFloat(val.expenses) || 0)
  animateTo('balance',  parseFloat(val.balance)  || 0)
}, { deep: true })

// ── Month label ────────────────────────────────────────────────────
const monthLabel = computed(() =>
  new Date(year.value, month.value - 1, 1).toLocaleDateString(
    locale.value === 'de' ? 'de-DE' : 'en-US',
    { month: 'long', year: 'numeric' },
  )
)

// ── Donut chart ────────────────────────────────────────────────────
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
    hoverOffset: 12,
  }],
}))

const donutOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: true,
  cutout: '74%',
  plugins: {
    legend: {
      position: 'right',
      labels: {
        boxWidth: 8, borderRadius: 4, padding: 10,
        font: { size: 11, family: 'Inter Variable, Inter, sans-serif' },
        color: theme.isDark ? '#6B7FA3' : '#64748b',
      },
    },
    tooltip: {
      backgroundColor: theme.isDark ? 'rgba(9,16,31,0.95)' : 'rgba(255,255,255,0.95)',
      borderColor: theme.isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
      borderWidth: 1,
      titleColor: theme.isDark ? '#e2e8f0' : '#1e293b',
      bodyColor:  theme.isDark ? '#94a3b8' : '#64748b',
      padding: 10,
      callbacks: { label: (ctx) => ` ${ctx.label}: ${ctx.parsed.toFixed(2)} €` },
    },
  },
}))

// ── Data loading ───────────────────────────────────────────────────
async function loadExpiring() {
  const res = await api.get('/categories/expiring-soon?days=30')
  if (res.ok) expiringCats.value = await res.json()
}

async function loadMonthlyReserve() {
  const res = await api.get('/recurring/monthly-reserve')
  if (res.ok) monthlyReserve.value = await res.json()
}

async function loadGoals() {
  const res = await api.get('/goals')
  if (res.ok) {
    const all = await res.json()
    topGoals.value = all
      .filter((g) => !g.is_achieved)
      .sort((a, b) => b.progress_pct - a.progress_pct)
      .slice(0, 3)
  }
}

async function load() {
  loaded.value = false
  const [sumRes, siRes, balRes] = await Promise.all([
    api.get(`/transactions/summary?year=${year.value}&month=${month.value}`),
    api.get(`/categories/soll-ist?year=${year.value}&month=${month.value}`),
    api.get('/accounts/balances'),
  ])
  if (!sumRes.ok || !siRes.ok || !balRes.ok) { toast.error(t('errors.generic')); return }
  summary.value  = await sumRes.json()
  sollIst.value  = await siRes.json()
  balances.value = await balRes.json()
  loaded.value   = true
}

function prevMonth() {
  month.value--; if (month.value < 1)  { month.value = 12; year.value-- }; load()
}
function nextMonth() {
  month.value++; if (month.value > 12) { month.value = 1;  year.value++ }; load()
}

function fmt(val) {
  return val.toFixed(2).replace('.', ',') + ' €'
}
const balancePositive = computed(() => display.balance >= 0)

// Load once a household is active; also re-runs after wizard sets active_household_id
watch(() => auth.user?.active_household_id, (id) => { if (id) { load(); loadExpiring(); loadMonthlyReserve(); loadGoals() } }, { immediate: true })

onMounted(() => {
  // fire-and-forget auto-book
  api.post('/recurring/auto-book', {}).catch(() => {})
})
</script>

<template>
  <main class="max-w-screen-lg mx-auto px-4 py-6 space-y-5">

    <!-- ── Expiring fixed costs banner ────────────────────────── -->
    <div
      v-if="expiringCats.length > 0"
      class="rounded-xl border border-amber-400/40 bg-amber-50 dark:bg-amber-500/10 px-4 py-3 flex items-start gap-3"
    >
      <span class="text-amber-500 mt-0.5 shrink-0">⚠</span>
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium text-amber-800 dark:text-amber-300">
          {{ t('categories.expiringWarning', { n: expiringCats.length }) }}
        </p>
        <p class="text-xs text-amber-700 dark:text-amber-400 mt-0.5 truncate">
          <span v-for="(cat, i) in expiringCats" :key="cat.id">
            <span v-if="i > 0"> · </span>{{ cat.name }} ({{ t('dashboard.diff') }}: {{ cat.days_remaining }}d)
          </span>
        </p>
      </div>
      <button
        @click="router.push('/categories')"
        class="text-xs font-semibold text-amber-700 dark:text-amber-300 hover:underline shrink-0 mt-0.5"
      >
        {{ t('categories.goToCategories') }}
      </button>
    </div>

    <!-- ── Hero header ─────────────────────────────────────────── -->
    <div class="anim-fade-up flex items-start justify-between pt-2 pb-1">
      <div>
        <p class="text-[11px] text-muted-foreground uppercase tracking-widest mb-2 font-medium">
          {{ monthLabel }}
        </p>
        <!-- Animated balance number -->
        <h1
          class="text-4xl font-black tracking-tight tabular-nums leading-none"
          :class="balancePositive
            ? 'bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent number-glow-emerald'
            : 'bg-gradient-to-r from-rose-400 via-pink-300 to-rose-400 bg-clip-text text-transparent number-glow-rose'"
        >
          {{ fmt(display.balance) }}
        </h1>
        <p class="text-xs text-muted-foreground mt-2">{{ t('dashboard.balance') }}</p>
      </div>
      <div class="flex items-center gap-2 mt-1">
        <button
          @click="prevMonth"
          class="h-8 w-8 rounded-xl flex items-center justify-center text-muted-foreground transition-all hover:scale-105"
          :class="theme.isDark ? 'bg-white/[0.05] hover:bg-white/[0.09]' : 'bg-gray-100 hover:bg-gray-200'"
        >‹</button>
        <button
          @click="nextMonth"
          class="h-8 w-8 rounded-xl flex items-center justify-center text-muted-foreground transition-all hover:scale-105"
          :class="theme.isDark ? 'bg-white/[0.05] hover:bg-white/[0.09]' : 'bg-gray-100 hover:bg-gray-200'"
        >›</button>
        <button
          @click="router.push('/transactions')"
          class="h-8 px-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white text-xs font-semibold flex items-center gap-1.5 transition-all hover:scale-105 hover:shadow-lg hover:shadow-emerald-500/25"
          style="box-shadow: 0 4px 14px rgba(16,185,129,0.18)"
        >
          <Plus class="h-3.5 w-3.5" />
          {{ t('dashboard.addTransaction') }}
        </button>
      </div>
    </div>

    <!-- ── Income / Expenses cards ──────────────────────────────── -->
    <div class="grid grid-cols-2 gap-3">
      <!-- Income -->
      <div
        class="anim-fade-up delay-100 rounded-2xl p-5 border relative overflow-hidden group transition-all duration-300 hover:scale-[1.02] cursor-default"
        :class="theme.isDark
          ? 'bg-emerald-500/[0.07] border-emerald-500/[0.15] hover:border-emerald-500/30'
          : 'bg-emerald-50 border-emerald-100 hover:border-emerald-200'"
        style="box-shadow: 0 0 0 0 rgba(16,185,129,0); transition: box-shadow 0.3s, transform 0.2s, border-color 0.2s;"
        @mouseenter="(e) => e.currentTarget.style.boxShadow = '0 0 30px rgba(16,185,129,0.12)'"
        @mouseleave="(e) => e.currentTarget.style.boxShadow = '0 0 0 0 rgba(16,185,129,0)'"
      >
        <div class="absolute -top-8 -right-8 w-28 h-28 rounded-full bg-emerald-400/[0.12] blur-2xl group-hover:scale-125 transition-transform duration-500" />
        <TrendingUp class="h-4 w-4 text-emerald-400 mb-3 relative" />
        <p class="text-[11px] text-muted-foreground mb-1.5 uppercase tracking-wider font-medium relative">
          {{ t('dashboard.income') }}
        </p>
        <p class="text-2xl font-bold text-emerald-400 tabular-nums relative">{{ fmt(display.income) }}</p>
      </div>

      <!-- Expenses -->
      <div
        class="anim-fade-up delay-150 rounded-2xl p-5 border relative overflow-hidden group transition-all duration-300 hover:scale-[1.02] cursor-default"
        :class="theme.isDark
          ? 'bg-rose-500/[0.07] border-rose-500/[0.15] hover:border-rose-500/30'
          : 'bg-rose-50 border-rose-100 hover:border-rose-200'"
        style="box-shadow: 0 0 0 0 rgba(244,63,94,0); transition: box-shadow 0.3s, transform 0.2s, border-color 0.2s;"
        @mouseenter="(e) => e.currentTarget.style.boxShadow = '0 0 30px rgba(244,63,94,0.12)'"
        @mouseleave="(e) => e.currentTarget.style.boxShadow = '0 0 0 0 rgba(244,63,94,0)'"
      >
        <div class="absolute -top-8 -right-8 w-28 h-28 rounded-full bg-rose-400/[0.12] blur-2xl group-hover:scale-125 transition-transform duration-500" />
        <TrendingDown class="h-4 w-4 text-rose-400 mb-3 relative" />
        <p class="text-[11px] text-muted-foreground mb-1.5 uppercase tracking-wider font-medium relative">
          {{ t('dashboard.expenses') }}
        </p>
        <p class="text-2xl font-bold text-rose-400 tabular-nums relative">{{ fmt(display.expenses) }}</p>
      </div>
    </div>

    <!-- ── Budget vs. Actual + Donut ────────────────────────────── -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Soll/Ist -->
      <div
        class="anim-fade-up delay-200 rounded-2xl border overflow-hidden"
        :class="theme.isDark
          ? 'bg-card/70 backdrop-blur-lg border-white/[0.06]'
          : 'bg-white border-gray-100 shadow-sm'"
      >
        <div class="px-5 py-4 border-b flex items-center justify-between"
             :class="theme.isDark ? 'border-white/[0.05]' : 'border-gray-50'">
          <h2 class="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
            {{ t('dashboard.sollIst') }}
          </h2>
          <div class="w-1.5 h-1.5 rounded-full bg-emerald-400 nav-dot" style="box-shadow: 0 0 6px rgba(16,185,129,0.8)" />
        </div>
        <div v-if="sollIst.length === 0" class="px-5 py-12 text-sm text-muted-foreground text-center">
          {{ t('dashboard.noData') }}
        </div>
        <div v-else>
          <SollIstRow v-for="node in sollIst" :key="node.id" :node="node" :depth="0" />
        </div>
      </div>

      <!-- Donut -->
      <div
        class="anim-fade-up delay-250 rounded-2xl border p-5"
        :class="theme.isDark
          ? 'bg-card/70 backdrop-blur-lg border-white/[0.06]'
          : 'bg-white border-gray-100 shadow-sm'"
      >
        <h2 class="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground mb-5">
          {{ t('reports.chart.expensesByCategory') }}
        </h2>
        <Doughnut
          v-if="donutData.length > 0"
          :data="donutChartData"
          :options="donutOptions"
          class="max-h-52"
        />
        <p v-else class="text-sm text-muted-foreground text-center py-12">
          {{ t('dashboard.noData') }}
        </p>
      </div>
    </div>

    <!-- ── Monthly reserve ─────────────────────────────────────────── -->
    <div v-if="monthlyReserve && monthlyReserve.total > 0" class="anim-fade-up delay-300">
      <div
        class="rounded-2xl border overflow-hidden"
        :class="theme.isDark
          ? 'bg-card/70 backdrop-blur-lg border-white/[0.06]'
          : 'bg-white border-gray-100 shadow-sm'"
      >
        <button
          class="w-full px-5 py-4 flex items-center justify-between text-left"
          @click="reserveOpen = !reserveOpen"
        >
          <span class="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
            {{ t('recurring.reserve') }}
          </span>
          <div class="flex items-center gap-3">
            <span class="text-sm font-bold tabular-nums">
              {{ monthlyReserve.total.toFixed(2).replace('.', ',') }} € / {{ t('month.label', 'Monat') }}
            </span>
            <span class="text-muted-foreground text-xs">{{ reserveOpen ? '▲' : '▼' }}</span>
          </div>
        </button>
        <div v-if="reserveOpen" class="border-t" :class="theme.isDark ? 'border-white/[0.05]' : 'border-gray-50'">
          <div
            v-for="item in monthlyReserve.items"
            :key="item.name"
            class="px-5 py-2.5 flex items-center justify-between text-sm border-b last:border-0"
            :class="theme.isDark ? 'border-white/[0.03]' : 'border-gray-50'"
          >
            <span>{{ item.name }}</span>
            <div class="flex gap-4 text-xs tabular-nums text-muted-foreground">
              <span>{{ item.amount.toFixed(2).replace('.', ',') }} € / {{ t(`recurring.intervals.${item.interval}`) }}</span>
              <span class="font-semibold text-foreground">= {{ item.monthly_equiv.toFixed(2).replace('.', ',') }} € / Mon.</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Account balances ──────────────────────────────────────── -->
    <div v-if="balances.length > 0" class="anim-fade-up delay-300">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
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
          v-for="(acc, i) in balances"
          :key="acc.id"
          class="rounded-2xl border px-4 py-3.5 flex items-center justify-between transition-all duration-200 hover:scale-[1.01] cursor-default"
          :class="[
            theme.isDark
              ? 'bg-card/50 border-white/[0.05] hover:border-white/10'
              : 'bg-white border-gray-100 shadow-sm hover:shadow',
            `anim-fade-up delay-${Math.min(300 + i * 50, 500)}`
          ]"
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

    <!-- ── Savings goals widget ─────────────────────────────────── -->
    <div v-if="topGoals.length > 0" class="anim-fade-up delay-350">
      <div
        class="rounded-2xl border overflow-hidden"
        :class="theme.isDark
          ? 'bg-card/70 backdrop-blur-lg border-white/[0.06]'
          : 'bg-white border-gray-100 shadow-sm'"
      >
        <div class="px-5 py-4 border-b flex items-center justify-between"
             :class="theme.isDark ? 'border-white/[0.05]' : 'border-gray-50'">
          <div class="flex items-center gap-2">
            <Target class="h-4 w-4 text-emerald-400" />
            <h2 class="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
              {{ t('goals.title') }}
            </h2>
          </div>
          <button
            @click="router.push('/goals')"
            class="text-xs text-muted-foreground hover:text-emerald-400 transition-colors"
          >
            {{ t('goals.allGoals') }}
          </button>
        </div>
        <div class="divide-y" :class="theme.isDark ? 'divide-white/[0.04]' : 'divide-gray-50'">
          <div
            v-for="goal in topGoals"
            :key="goal.id"
            class="px-5 py-3 flex items-center gap-4"
          >
            <span class="text-sm flex-1 min-w-0 truncate">{{ goal.name }}</span>
            <div class="w-28 h-1.5 rounded-full bg-muted overflow-hidden shrink-0">
              <div
                class="h-full rounded-full"
                :style="{
                  width: goal.progress_pct + '%',
                  background: goal.color || '#10b981',
                  transition: 'width 0.8s ease',
                }"
              />
            </div>
            <span class="text-xs tabular-nums text-muted-foreground shrink-0 w-28 text-right">
              {{ fmt(goal.current_amount) }} / {{ fmt(goal.target_amount) }}
            </span>
          </div>
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
    const pct  = parseFloat(props.node.soll) > 0
      ? Math.min(100, Math.abs(parseFloat(props.node.ist) / parseFloat(props.node.soll) * 100))
      : 0
    return { pct, over: pct >= 100 }
  },
  template: `
    <div>
      <div class="px-5 py-2.5 border-b border-white/[0.04] last:border-0"
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
        <div class="h-1 rounded-full overflow-hidden" style="background: rgba(255,255,255,0.05)">
          <div class="h-full rounded-full"
               :style="{ width: pct + '%', transition: 'width 1.2s cubic-bezier(0.16,1,0.3,1)' }"
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
