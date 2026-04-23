<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const { t, tm } = useI18n()
const api = useApi()

const now = new Date()
const year = ref(now.getFullYear())
const month = ref(now.getMonth() + 1)
const data = ref(null)
const balances = ref([])

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
  if (r.ok) data.value = await r.json()
  const balRes = await api.get('/accounts/balances')
  if (balRes.ok) balances.value = await balRes.json()
}

const fixedCostsBalance = computed(() =>
  balances.value.filter(b => b.account_role === 'fixed_costs').reduce((s, b) => s + parseFloat(b.balance || 0), 0)
)
const variableBalance = computed(() =>
  balances.value.filter(b => b.account_role === 'variable').reduce((s, b) => s + parseFloat(b.balance || 0), 0)
)
const totalAvailable = computed(() => fixedCostsBalance.value + variableBalance.value)

const monthLabel = computed(() => {
  const months = tm('monthView.monthsFull')
  if (Array.isArray(months) && months[month.value - 1]) {
    return months[month.value - 1]
  }
  return new Date(year.value, month.value - 1).toLocaleString('default', { month: 'long' })
})

watch([year, month], load)
onMounted(load)
</script>

<template>
  <div class="container mx-auto py-6 space-y-4">
    <div class="flex items-center gap-4">
      <Button variant="ghost" size="icon" @click="prevMonth">&#8249;</Button>
      <h1 class="text-2xl font-bold">{{ monthLabel }} {{ year }}</h1>
      <Button variant="ghost" size="icon" @click="nextMonth">&#8250;</Button>
    </div>

    <template v-if="data">
      <Card v-for="section in data.sections" :key="section.type">
        <CardHeader>
          <CardTitle>{{ $t(`monthView.${section.type}`) }}</CardTitle>
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
                <td class="py-1">{{ row.name }}</td>
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

      <Card>
        <CardContent class="pt-4 pb-4">
          <div class="flex divide-x">
            <div class="flex-1 text-center px-4 space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('dashboard.income') }}</p>
              <p class="text-xl font-bold text-emerald-500">{{ (data.summary?.total_income ?? 0).toFixed(2) }}</p>
            </div>
            <div class="flex-1 text-center px-4 space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('dashboard.expenses') }}</p>
              <p class="text-xl font-bold text-rose-500">{{ (data.summary?.total_expense ?? 0).toFixed(2) }}</p>
            </div>
            <div class="flex-1 text-center px-4 space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('monthView.balance') }}</p>
              <p class="text-xl font-bold" :class="(data.summary?.balance ?? 0) >= 0 ? 'text-emerald-500' : 'text-rose-500'">
                {{ (data.summary?.balance ?? 0).toFixed(2) }}
              </p>
            </div>
            <div class="flex-1 text-center px-4 space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('monthView.savingsRate') }}</p>
              <p class="text-xl font-bold text-indigo-500">{{ (data.summary?.real_savings_rate ?? 0).toFixed(1) }}%</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <section v-if="data?.savings_rows?.length" class="mt-4">
        <h3 class="text-sm font-semibold text-muted-foreground mb-2">{{ t('monthView.savings') }}</h3>
        <div
          v-for="row in data.savings_rows"
          :key="row.date + row.description"
          class="flex justify-between items-center py-1 border-b border-border/50"
        >
          <span class="text-sm">{{ row.description }}</span>
          <span class="text-sm text-muted-foreground">{{ row.date }}</span>
          <span class="text-sm font-medium text-emerald-400">{{ row.amount.toFixed(2) }}</span>
        </div>
      </section>

      <div class="grid grid-cols-3 gap-3 mt-4">
        <div class="rounded-xl border border-border bg-card p-4">
          <p class="text-xs text-muted-foreground">{{ t('monthView.availableFixed') }}</p>
          <p class="text-lg font-bold">{{ fixedCostsBalance.toFixed(2) }}</p>
        </div>
        <div class="rounded-xl border border-border bg-card p-4">
          <p class="text-xs text-muted-foreground">{{ t('monthView.availableVariable') }}</p>
          <p class="text-lg font-bold">{{ variableBalance.toFixed(2) }}</p>
        </div>
        <div class="rounded-xl border border-border bg-card p-4">
          <p class="text-xs text-muted-foreground">{{ t('monthView.availableTotal') }}</p>
          <p class="text-lg font-bold">{{ totalAvailable.toFixed(2) }}</p>
        </div>
      </div>
    </template>
  </div>
</template>
