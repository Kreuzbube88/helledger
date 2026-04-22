<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Search, X } from 'lucide-vue-next'
import { useApi } from '@/lib/api'

const props = defineProps({ open: Boolean })
const emit = defineEmits(['close'])
const { t } = useI18n()
const api = useApi()
const router = useRouter()

const query = ref('')
const results = ref([])
const loading = ref(false)
let debounceTimer = null

watch(query, (val) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  if (val.length < 2) { results.value = []; return }
  debounceTimer = setTimeout(async () => {
    loading.value = true
    const res = await api.get(`/search?q=${encodeURIComponent(val)}&limit=20`)
    if (res.ok) results.value = await res.json()
    loading.value = false
  }, 300)
})

watch(() => props.open, (v) => {
  if (!v) { query.value = ''; results.value = [] }
})

onUnmounted(() => { if (debounceTimer) clearTimeout(debounceTimer) })

function navigate(result) {
  const [year, month] = result.date.split('-')
  router.push(`/transactions?year=${year}&month=${parseInt(month)}`)
  emit('close')
}

function fmtAmount(amt, type) {
  const sign = type === 'income' ? '+' : type === 'expense' ? '-' : ''
  return sign + Math.abs(amt).toLocaleString('de-DE', { minimumFractionDigits: 2 }) + ' €'
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-start justify-center pt-[10vh]">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('close')" />
      <!-- Modal -->
      <div class="relative z-10 w-full max-w-lg mx-4 rounded-xl border bg-background shadow-2xl">
        <!-- Search input -->
        <div class="flex items-center gap-3 px-4 py-3 border-b">
          <Search class="h-4 w-4 text-muted-foreground shrink-0" />
          <input
            v-model="query"
            class="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            :placeholder="t('search.placeholder')"
            autofocus
          />
          <button @click="$emit('close')"><X class="h-4 w-4 text-muted-foreground" /></button>
        </div>
        <!-- Results -->
        <div class="max-h-80 overflow-y-auto py-1">
          <div v-if="loading" class="px-4 py-6 text-center text-sm text-muted-foreground">...</div>
          <div v-else-if="results.length === 0 && query.length >= 2" class="px-4 py-6 text-center text-sm text-muted-foreground">{{ t('search.noResults') }}</div>
          <button
            v-for="r in results"
            :key="r.id"
            class="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-muted text-sm text-left transition-colors"
            @click="navigate(r)"
          >
            <div class="flex-1 min-w-0">
              <p class="font-medium truncate">{{ r.description }}</p>
              <p class="text-xs text-muted-foreground">{{ r.date }} · {{ r.category_name || '—' }} · {{ r.account_name }}</p>
            </div>
            <span :class="r.transaction_type === 'income' ? 'text-emerald-500' : r.transaction_type === 'expense' ? 'text-rose-500' : 'text-muted-foreground'" class="tabular-nums text-xs font-medium shrink-0">
              {{ fmtAmount(r.amount, r.transaction_type) }}
            </span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
