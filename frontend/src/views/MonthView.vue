<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useSwipe } from '@vueuse/core'
import { useI18n } from 'vue-i18n'
import { useApi } from '@/lib/api'
import { usePullToRefresh } from '@/composables/usePullToRefresh'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const { t, tm } = useI18n()
const api = useApi()

const now = new Date()
const year = ref(now.getFullYear())
const month = ref(now.getMonth() + 1)
const data = ref(null)
const balances = ref([])
const projectedBalances = ref([])

const swipeContainer = ref(null)

useSwipe(swipeContainer, {
  onSwipeEnd(e, direction) {
    if (direction === 'left')  nextMonth()
    else if (direction === 'right') prevMonth()
  },
  threshold: 50,
})

function prevMonth() {
  if (month.value === 1) { month.value = 12; year.value-- }
  else month.value--
}
function nextMonth() {
  if (month.value === 12) { month.value = 1; year.value++ }
  else month.value++
}

async function load() {
  const r = await api.get(`/dashboard/month?year=${year.value}&month=${month.value}`)
  if (r.ok) {
    data.value = await r.json()
    projectedBalances.value = data.value.projected_balances || []
  }
  const balRes = await api.get('/accounts/balances')
  if (balRes.ok) balances.value = await balRes.json()
}

const effectiveBalances = computed(() =>
  data.value?.is_planned ? projectedBalances.value : balances.value
)
const fixedCostsBalance = computed(() =>
  effectiveBalances.value.filter(b => b.account_role === 'fixed_costs').reduce((s, b) => s + parseFloat(b.balance || 0), 0)
)
const variableBalance = computed(() =>
  effectiveBalances.value.filter(b => b.account_role === 'variable').reduce((s, b) => s + parseFloat(b.balance || 0), 0)
)

const totalSavings = computed(() =>
  (data.value?.savings_rows || []).reduce((s, r) => s + r.amount, 0)
)

const totalDistribution = computed(() =>
  (data.value?.distribution_rows || []).reduce((s, r) => s + r.amount, 0)
)

const monthLabel = computed(() => {
  const months = tm('monthView.monthsFull')
  if (Array.isArray(months) && months[month.value - 1]) {
    return months[month.value - 1]
  }
  return new Date(year.value, month.value - 1).toLocaleString('default', { month: 'long' })
})

const sectionLabel = computed(() => ({
  income: t('monthView.income'),
  fixed: t('monthView.fixed'),
  variable: t('monthView.variable'),
}))

const incomeSection = computed(() => data.value?.sections.find(s => s.type === 'income'))
const otherSections = computed(() => data.value?.sections.filter(s => s.type !== 'income') || [])

const { isPulling } = usePullToRefresh(load)

watch([year, month], load)
onMounted(load)
</script>

<template>
  <div ref="swipeContainer" class="container mx-auto py-6 space-y-4">
    <Transition name="fade">
      <div v-if="isPulling" class="flex justify-center py-3 md:hidden">
        <div class="ptr-spinner" />
      </div>
    </Transition>

    <!-- Navigation -->
    <div class="flex items-center gap-4">
      <Button variant="ghost" size="icon" @click="prevMonth">&#8249;</Button>
      <h1 class="text-2xl font-bold">{{ monthLabel }} {{ year }}</h1>
      <Button variant="ghost" size="icon" @click="nextMonth">&#8250;</Button>
    </div>

    <!-- Prognose-Banner -->
    <div
      v-if="data?.is_planned"
      class="rounded-xl border border-blue-400/40 bg-blue-50 dark:bg-blue-500/10 px-4 py-3 flex items-center gap-3"
    >
      <span class="text-blue-500 shrink-0">📅</span>
      <p class="text-sm text-blue-800 dark:text-blue-300">{{ t('monthView.plannedBanner') }}</p>
    </div>

    <template v-if="data">
      <!-- KPI Bar -->
      <Card>
        <CardContent class="pt-4 pb-4">
          <div class="grid grid-cols-2 md:grid-cols-4">
            <!-- Einnahmen -->
            <div class="text-center px-4 py-2 space-y-1 border-r border-b md:border-b-0">
              <p class="text-xs text-muted-foreground uppercase tracking-wide">{{ t('dashboard.income') }}</p>
              <p class="text-xl font-bold text-emerald-500 tabular-nums">{{ (data.summary?.total_income ?? 0).toFixed(2) }}</p>
            </div>
            <!-- Ausgaben -->
            <div class="text-center px-4 py-2 space-y-1 border-b md:border-b-0 md:border-r">
              <p class="text-xs text-muted-foreground uppercase tracking-wide">{{ t('dashboard.expenses') }}</p>
              <p class="text-xl font-bold text-rose-500 tabular-nums">{{ (data.summary?.total_expense ?? 0).toFixed(2) }}</p>
            </div>
            <!-- Sparen -->
            <div class="text-center px-4 py-2 space-y-1 border-r">
              <p class="text-xs text-muted-foreground uppercase tracking-wide">{{ t('monthView.savings') }}</p>
              <p class="text-xl font-bold text-violet-500 tabular-nums">{{ (data.summary?.savings_amount ?? 0).toFixed(2) }}</p>
              <p class="text-xs text-muted-foreground">{{ (data.summary?.savings_rate ?? 0).toFixed(1) }}%</p>
            </div>
            <!-- Variabel verfügbar -->
            <div class="px-4 py-2 space-y-1 text-center">
              <p class="text-xs text-muted-foreground uppercase tracking-wide">{{ t('monthView.availableKpi') }}</p>
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
          </div>
        </CardContent>
      </Card>

      <!-- Einnahmen-Sektion -->
      <Card v-if="incomeSection">
        <CardHeader>
          <CardTitle>{{ sectionLabel['income'] }}</CardTitle>
        </CardHeader>
        <CardContent>
          <table class="w-full text-sm table-fixed">
            <thead>
              <tr class="border-b text-muted-foreground">
                <th class="text-left py-1">{{ $t('yearView.category') }}</th>
                <th class="text-right py-1 w-32">{{ $t('monthView.ist') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in incomeSection.rows" :key="row.category_id" class="border-b hover:bg-muted/50">
                <td class="py-1" :class="row.parent_id ? 'pl-4 text-muted-foreground' : ''">
                  {{ row.parent_id ? '— ' : '' }}{{ row.name }}
                </td>
                <td class="text-right tabular-nums">{{ (typeof row.ist === 'number' ? row.ist : parseFloat(row.ist)).toFixed(2) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="font-semibold">
                <td class="pt-2">{{ $t('monthView.gesamt') }}</td>
                <td class="text-right pt-2 tabular-nums">{{ incomeSection.total_ist.toFixed(2) }}</td>
              </tr>
            </tfoot>
          </table>
        </CardContent>
      </Card>

      <!-- Sparüberweisungen-Sektion (zwischen income und fixed) -->
      <Card v-if="data?.savings_rows?.length">
        <CardHeader>
          <CardTitle>{{ t('monthView.savingsSection') }}</CardTitle>
        </CardHeader>
        <CardContent>
          <table class="w-full text-sm table-fixed">
            <thead>
              <tr class="border-b text-muted-foreground">
                <th class="text-left py-1">{{ t('monthView.savings') }}</th>
                <th class="text-right py-1 w-32">{{ $t('monthView.ist') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in data.savings_rows" :key="idx" class="border-b hover:bg-muted/50">
                <td class="py-1">{{ row.description }}</td>
                <td class="text-right tabular-nums text-violet-500">{{ row.amount.toFixed(2) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="font-semibold">
                <td class="pt-2">{{ $t('monthView.gesamt') }}</td>
                <td class="text-right pt-2 tabular-nums text-violet-500">{{ totalSavings.toFixed(2) }}</td>
              </tr>
            </tfoot>
          </table>
        </CardContent>
      </Card>

      <!-- Fixkosten und Variable Sektionen -->
      <Card v-for="section in otherSections" :key="section.type">
        <CardHeader>
          <CardTitle>{{ sectionLabel[section.type] || section.type }}</CardTitle>
        </CardHeader>
        <CardContent>
          <table class="w-full text-sm table-fixed">
            <thead>
              <tr class="border-b text-muted-foreground">
                <th class="text-left py-1">{{ $t('yearView.category') }}</th>
                <th class="text-right py-1 w-32">{{ $t('monthView.ist') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in section.rows" :key="row.category_id" class="border-b hover:bg-muted/50">
                <td class="py-1" :class="row.parent_id ? 'pl-4 text-muted-foreground' : ''">
                  {{ row.parent_id ? '— ' : '' }}{{ row.name }}
                </td>
                <td class="text-right tabular-nums">{{ (typeof row.ist === 'number' ? row.ist : parseFloat(row.ist)).toFixed(2) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="font-semibold">
                <td class="pt-2">{{ $t('monthView.gesamt') }}</td>
                <td class="text-right pt-2 tabular-nums">{{ section.total_ist.toFixed(2) }}</td>
              </tr>
            </tfoot>
          </table>
        </CardContent>
      </Card>

      <!-- Kontoverteilung-Sektion (unverändert, bleibt am Ende) -->
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
    </template>
  </div>
</template>
