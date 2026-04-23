<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const { t } = useI18n()
const api = useApi()

const year = ref(String(new Date().getFullYear()))
const data = ref(null)

async function load() {
  const r = await api.get(`/dashboard/year?year=${year.value}`)
  if (r.ok) data.value = await r.json()
}

const hasSavings = computed(() => {
  const actual = Object.values(data.value?.savings_by_month || {}).some(v => v > 0)
  const planned = Object.values(data.value?.savings_planned_by_month || {}).some(v => v > 0)
  return actual || planned
})

watch(year, load)
onMounted(load)
</script>

<template>
  <div class="container mx-auto py-6 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">{{ $t('yearView.title') }}</h1>
      <Select v-model="year">
        <SelectTrigger class="w-32"><SelectValue /></SelectTrigger>
        <SelectContent>
          <SelectItem v-for="y in [2024,2025,2026,2027]" :key="y" :value="String(y)">{{ y }}</SelectItem>
        </SelectContent>
      </Select>
    </div>

    <Card v-if="data && data.categories.length > 0">
      <CardContent class="pt-4 overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b">
              <th class="text-left py-2 pr-4">{{ $t('yearView.category') }}</th>
              <th
                v-for="(m, i) in $tm('monthView.months')"
                :key="m"
                class="text-right py-2 px-2 min-w-16"
                :class="data.planned_from <= i + 1 ? 'text-muted-foreground italic' : ''"
              >{{ m }}</th>
              <th class="text-right py-2 px-2 min-w-16 font-semibold">{{ $t('monthView.gesamt') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cat in data.categories" :key="cat.id" class="border-b hover:bg-muted/50">
              <td class="py-1 pr-4 font-medium">{{ cat.name }}</td>
              <td
                v-for="(val, i) in cat.months"
                :key="i"
                class="text-right py-1 px-2 tabular-nums"
                :class="[
                  cat.is_planned[i]
                    ? 'text-muted-foreground italic'
                    : val > 0
                      ? (cat.type === 'income' ? 'text-emerald-500' : 'text-rose-500')
                      : 'text-muted-foreground'
                ]"
              >
                {{ val > 0 ? (cat.is_planned[i] ? '~' : '') + val.toFixed(0) : '—' }}
              </td>
              <td class="text-right py-1 px-2 tabular-nums font-semibold">
                {{ cat.months.reduce((s, v) => s + v, 0) > 0 ? cat.months.reduce((s, v) => s + v, 0).toFixed(0) : '—' }}
              </td>
            </tr>
            <tr v-if="hasSavings" class="border-t-2 border-border">
              <td class="py-2 pr-4 font-semibold text-emerald-400">
                {{ t('yearView.savings') }}
              </td>
              <td
                v-for="m in 12"
                :key="m"
                class="px-3 py-2 text-right tabular-nums"
                :class="data.savings_by_month[String(m).padStart(2,'0')] ? 'text-emerald-400' : 'text-emerald-400/60 italic'"
              >
                <template v-if="data.savings_by_month[String(m).padStart(2,'0')]">
                  {{ data.savings_by_month[String(m).padStart(2,'0')].toFixed(0) }}
                </template>
                <template v-else-if="data.savings_planned_by_month && data.savings_planned_by_month[String(m).padStart(2,'0')]">
                  ~{{ data.savings_planned_by_month[String(m).padStart(2,'0')].toFixed(0) }}
                </template>
                <template v-else>—</template>
              </td>
              <td class="px-3 py-2 text-right tabular-nums font-semibold text-emerald-400">
                {{ (
                  Object.values(data.savings_by_month || {}).reduce((s, v) => s + v, 0) +
                  Object.values(data.savings_planned_by_month || {}).reduce((s, v) => s + v, 0)
                ).toFixed(0) }}
              </td>
            </tr>
          </tbody>
        </table>
      </CardContent>
    </Card>

    <p v-else-if="data && data.categories.length === 0" class="text-muted-foreground text-center py-8">
      {{ $t('yearView.noData') }}
    </p>
  </div>
</template>
