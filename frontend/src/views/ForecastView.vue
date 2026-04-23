<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend,
} from 'chart.js'
import { useApi } from '@/lib/api'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const { t } = useI18n()
const api = useApi()

const loading = ref(true)
const months = ref([])

async function loadData() {
  loading.value = true
  const res = await api.get('/forecast?months=12')
  if (res.ok) {
    const data = await res.json()
    months.value = data.months ?? []
  }
  loading.value = false
}

function formatMonth(m) {
  return new Date(m.month + '-01').toLocaleDateString('default', { month: 'short', year: 'numeric' })
}

const chartData = computed(() => ({
  labels: months.value.map(formatMonth),
  datasets: [
    {
      label: t('forecast.income'),
      data: months.value.map(m => m.income),
      borderColor: '#10b981',
      backgroundColor: 'rgba(16,185,129,0.1)',
      tension: 0.3,
      pointRadius: 3,
    },
    {
      label: t('forecast.fixedExpenses'),
      data: months.value.map(m => m.fixed_expenses),
      borderColor: '#f43f5e',
      backgroundColor: 'rgba(244,63,94,0.1)',
      tension: 0.3,
      pointRadius: 3,
    },
    {
      label: t('forecast.savings'),
      data: months.value.map(m => m.savings),
      borderColor: '#8b5cf6',
      backgroundColor: 'rgba(139,92,246,0.1)',
      tension: 0.3,
      pointRadius: 3,
    },
    {
      label: t('forecast.savingsTotal'),
      data: months.value.map(m => m.savings_total),
      borderColor: '#6366f1',
      backgroundColor: 'rgba(99,102,241,0.1)',
      borderWidth: 3,
      tension: 0.3,
      pointRadius: 3,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  plugins: { legend: { position: 'top' } },
  scales: { x: { grid: { display: false } }, y: { beginAtZero: false } },
}

onMounted(loadData)
</script>

<template>
  <div class="p-4 space-y-6">
    <div>
      <h1 class="text-xl font-bold">{{ t('forecast.title') }}</h1>
      <p class="text-sm text-muted-foreground">{{ t('forecast.subtitle') }}</p>
    </div>

    <div v-if="loading" class="text-center py-8 text-muted-foreground">...</div>
    <div v-else-if="!months.length" class="text-center py-8 text-muted-foreground">{{ t('forecast.noData') }}</div>
    <template v-else>
      <div class="rounded-xl border border-border bg-card p-4">
        <Line :data="chartData" :options="chartOptions" class="max-h-80" />
      </div>

      <div class="rounded-xl border border-border bg-card overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b text-muted-foreground text-left">
              <th class="px-4 py-3 font-medium">{{ t('reports.period.month') }}</th>
              <th class="px-4 py-3 font-medium text-right">{{ t('forecast.income') }}</th>
              <th class="px-4 py-3 font-medium text-right">{{ t('forecast.fixedExpenses') }}</th>
              <th class="px-4 py-3 font-medium text-right">{{ t('forecast.savings') }}</th>
              <th class="px-4 py-3 font-medium text-right">{{ t('forecast.savingsTotal') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in months" :key="m.month" class="border-b last:border-0 hover:bg-muted/50 transition-colors">
              <td class="px-4 py-3 tabular-nums">{{ formatMonth(m) }}</td>
              <td class="px-4 py-3 tabular-nums text-right text-emerald-500">{{ m.income.toFixed(2) }}</td>
              <td class="px-4 py-3 tabular-nums text-right text-rose-500">{{ m.fixed_expenses.toFixed(2) }}</td>
              <td class="px-4 py-3 tabular-nums text-right text-violet-500">{{ m.savings.toFixed(2) }}</td>
              <td class="px-4 py-3 tabular-nums text-right font-medium text-indigo-500">{{ m.savings_total.toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>
