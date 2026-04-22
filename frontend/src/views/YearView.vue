<script setup>
import { ref, watch, onMounted } from 'vue'
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
              <th v-for="m in $tm('monthView.months')" :key="m" class="text-right py-2 px-2 min-w-16">{{ m }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cat in data.categories" :key="cat.id" class="border-b hover:bg-muted/50">
              <td class="py-1 pr-4 font-medium">{{ cat.name }}</td>
              <td v-for="(val, i) in cat.months" :key="i" class="text-right py-1 px-2 tabular-nums"
                  :class="val > 0 ? 'text-rose-500' : 'text-muted-foreground'">
                {{ val > 0 ? val.toFixed(0) : '—' }}
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
