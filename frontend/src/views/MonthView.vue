<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { useApi } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const { t } = useI18n()
const api = useApi()

const now = new Date()
const year = ref(now.getFullYear())
const month = ref(now.getMonth() + 1)
const data = ref(null)

// Inline Soll editing: map of category_id → { editing: bool, value: string }
const editingSoll = ref({})

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
  editingSoll.value = {}
}

watch([year, month], load)
onMounted(load)

function pctColor(pct, type) {
  if (type === 'income') return pct >= 100 ? 'text-emerald-500' : 'text-rose-500'
  if (pct <= 80) return 'text-emerald-500'
  if (pct <= 100) return 'text-yellow-500'
  return 'text-rose-500'
}

function startEditSoll(row) {
  editingSoll.value[row.category_id] = { editing: true, value: String(row.soll) }
  nextTick(() => {
    document.querySelector(`input[data-cat="${row.category_id}"]`)?.focus()
  })
}

async function saveSoll(row) {
  const state = editingSoll.value[row.category_id]
  if (!state) return
  const amount = parseFloat(state.value)
  if (isNaN(amount) || amount < 0) { state.editing = false; return }
  const firstOfMonth = `${year.value}-${String(month.value).padStart(2, '0')}-01`
  const res = await api.post('/expected-values', {
    category_id: row.category_id,
    amount,
    valid_from: firstOfMonth,
  })
  if (res.ok) {
    toast.success(t('monthView.saveSoll'))
    await load()
  } else {
    toast.error(t('errors.generic'))
  }
  state.editing = false
}

function cancelEditSoll(catId) {
  if (editingSoll.value[catId]) editingSoll.value[catId].editing = false
}
</script>

<template>
  <div class="container mx-auto py-6 space-y-4">
    <div class="flex items-center gap-4">
      <Button variant="ghost" size="icon" @click="prevMonth">&#8249;</Button>
      <h1 class="text-2xl font-bold">{{ $tm('monthView.monthsFull')[month - 1] }} {{ year }}</h1>
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
                <th class="text-right py-1 w-28">{{ $t('monthView.soll') }}</th>
                <th class="text-right py-1 w-24">{{ $t('monthView.ist') }}</th>
                <th class="text-right py-1 w-24">{{ $t('monthView.diff') }}</th>
                <th class="text-right py-1 w-16">{{ $t('monthView.pct') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in section.rows" :key="row.category_id" class="border-b hover:bg-muted/50">
                <td class="py-1">{{ row.name }}</td>
                <td class="text-right tabular-nums">
                  <template v-if="editingSoll[row.category_id]?.editing">
                    <input
                      :data-cat="row.category_id"
                      v-model="editingSoll[row.category_id].value"
                      type="number" step="0.01" min="0"
                      class="w-20 text-right bg-transparent border-b border-primary outline-none tabular-nums"
                      @blur="saveSoll(row)"
                      @keydown.enter.prevent="saveSoll(row)"
                      @keydown.escape="cancelEditSoll(row.category_id)"
                    />
                  </template>
                  <template v-else>
                    <span
                      class="cursor-pointer hover:underline hover:text-primary"
                      :title="$t('monthView.editSoll')"
                      @click="startEditSoll(row)"
                    >{{ row.soll.toFixed(2) }}</span>
                  </template>
                </td>
                <td class="text-right tabular-nums">{{ row.ist.toFixed(2) }}</td>
                <td class="text-right tabular-nums" :class="row.diff >= 0 ? 'text-emerald-500' : 'text-rose-500'">
                  {{ row.diff.toFixed(2) }}
                </td>
                <td class="text-right">
                  <span :class="pctColor(row.pct, section.type)">{{ row.pct.toFixed(0) }}%</span>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="font-semibold">
                <td class="pt-2">{{ $t('monthView.gesamt') }}</td>
                <td class="text-right pt-2 tabular-nums">{{ section.total_soll.toFixed(2) }}</td>
                <td class="text-right pt-2 tabular-nums">{{ section.total_ist.toFixed(2) }}</td>
                <td></td><td></td>
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
              <p class="text-xl font-bold text-emerald-500">{{ data.summary.total_income.toFixed(2) }}</p>
            </div>
            <div class="flex-1 text-center px-4 space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('dashboard.expenses') }}</p>
              <p class="text-xl font-bold text-rose-500">{{ data.summary.total_expense.toFixed(2) }}</p>
            </div>
            <div class="flex-1 text-center px-4 space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('monthView.balance') }}</p>
              <p class="text-xl font-bold" :class="data.summary.balance >= 0 ? 'text-emerald-500' : 'text-rose-500'">
                {{ data.summary.balance.toFixed(2) }}
              </p>
            </div>
            <div class="flex-1 text-center px-4 space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('monthView.savingsRate') }}</p>
              <p class="text-xl font-bold text-indigo-500">{{ data.summary.savings_rate.toFixed(1) }}%</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </template>
  </div>
</template>
