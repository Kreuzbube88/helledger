<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { toast } from 'vue-sonner'
import {
  Check, Plus, Trash2, Building2, Wallet, CreditCard,
  ChevronRight, ChevronLeft, Sparkles,
} from 'lucide-vue-next'

const emit = defineEmits(['done'])
const { t, locale } = useI18n()
const api = useApi()
const auth = useAuthStore()

// ── Steps: 0=welcome  1=household  2=accounts  3=categories  4=done ──
const step = ref(0)
const loading = ref(false)

// ── Step 1: Household ─────────────────────────────────────────────────
const householdName = ref(`${auth.user?.name || 'Mein'}s Haushalt`)

// ── Step 2: Accounts ──────────────────────────────────────────────────
const accounts = ref([
  { name: '', account_type: 'checking', starting_balance: '', currency: 'EUR' },
])

const ACCOUNT_TYPES = [
  { value: 'checking', labelDe: 'Girokonto',   labelEn: 'Checking',  icon: Building2 },
  { value: 'savings',  labelDe: 'Sparkonto',    labelEn: 'Savings',   icon: Wallet },
  { value: 'credit',   labelDe: 'Kreditkarte',  labelEn: 'Credit',    icon: CreditCard },
]

function accountTypeLabel(v) {
  const t = ACCOUNT_TYPES.find((x) => x.value === v)
  return t ? (locale.value === 'de' ? t.labelDe : t.labelEn) : v
}

function addAccount() {
  accounts.value.push({ name: '', account_type: 'checking', starting_balance: '', currency: 'EUR' })
}

function removeAccount(i) {
  if (accounts.value.length > 1) accounts.value.splice(i, 1)
}

const accountsValid = computed(() =>
  accounts.value.every((a) => a.name.trim() && a.starting_balance !== '')
)

// ── Step 3: Categories ────────────────────────────────────────────────
const DEFAULT_CATS = [
  { de: 'Gehalt',           en: 'Salary',          type: 'income',   color: '#10b981' },
  { de: 'Nebeneinkommen',   en: 'Side Income',      type: 'income',   color: '#34d399' },
  { de: 'Sonstige Einnahmen', en: 'Other Income',   type: 'income',   color: '#6ee7b7' },
  { de: 'Miete',            en: 'Rent',             type: 'fixed',    color: '#8b5cf6' },
  { de: 'Strom & Gas',      en: 'Electricity',      type: 'fixed',    color: '#a78bfa' },
  { de: 'Internet',         en: 'Internet',         type: 'fixed',    color: '#c4b5fd' },
  { de: 'Versicherungen',   en: 'Insurance',        type: 'fixed',    color: '#7c3aed' },
  { de: 'Abonnements',      en: 'Subscriptions',    type: 'fixed',    color: '#6d28d9' },
  { de: 'Lebensmittel',     en: 'Groceries',        type: 'variable', color: '#3b82f6' },
  { de: 'Restaurants',      en: 'Restaurants',      type: 'variable', color: '#60a5fa' },
  { de: 'Freizeit',         en: 'Leisure',          type: 'variable', color: '#f59e0b' },
  { de: 'Kleidung',         en: 'Clothing',         type: 'variable', color: '#f97316' },
  { de: 'Transport',        en: 'Transport',        type: 'variable', color: '#06b6d4' },
  { de: 'Gesundheit',       en: 'Health',           type: 'variable', color: '#ec4899' },
]

const selectedCats = ref(new Set(DEFAULT_CATS.map((_, i) => i)))

function catName(cat) { return locale.value === 'de' ? cat.de : cat.en }
function toggleCat(i) {
  if (selectedCats.value.has(i)) selectedCats.value.delete(i)
  else selectedCats.value.add(i)
}
function selectAllCats() { selectedCats.value = new Set(DEFAULT_CATS.map((_, i) => i)) }
function selectNoneCats() { selectedCats.value = new Set() }

const catsByType = computed(() => {
  const groups = { income: [], fixed: [], variable: [] }
  DEFAULT_CATS.forEach((cat, i) => groups[cat.type]?.push({ cat, i }))
  return groups
})

// ── Summary ───────────────────────────────────────────────────────────
const summary = ref({ accounts: 0, categories: 0 })

// ── Navigation ────────────────────────────────────────────────────────
async function next() {
  if (step.value === 0) { step.value = 1; return }

  if (step.value === 1) {
    if (!householdName.value.trim()) return
    loading.value = true
    try {
      const res = await api.post('/households', { name: householdName.value.trim() })
      if (!res.ok) { toast.error(t('errors.generic')); return }
      const hh = await res.json()
      await api.post(`/households/${hh.id}/activate`, {})
      await auth.fetchUser()
      step.value = 2
    } finally { loading.value = false }
    return
  }

  if (step.value === 2) {
    if (!accountsValid.value) return
    step.value = 3
    return
  }

  if (step.value === 3) {
    await finish()
  }
}

function back() {
  if (step.value > 0) step.value--
}

async function finish() {
  loading.value = true
  try {
    // Create accounts
    let accountCount = 0
    for (const acc of accounts.value) {
      const res = await api.post('/accounts', {
        name: acc.name.trim(),
        account_type: acc.account_type,
        starting_balance: parseFloat(acc.starting_balance) || 0,
        currency: acc.currency,
      })
      if (res.ok) accountCount++
    }

    // Create categories
    let catCount = 0
    for (const i of selectedCats.value) {
      const cat = DEFAULT_CATS[i]
      const res = await api.post('/categories', {
        name: catName(cat),
        category_type: cat.type,
        color: cat.color,
      })
      if (res.ok) catCount++
    }

    summary.value = { accounts: accountCount, categories: catCount }
    step.value = 4
  } finally { loading.value = false }
}

function skipCategories() {
  summary.value = { accounts: accounts.value.length, categories: 0 }
  selectedCats.value = new Set()
  finish()
}

const GROUP_LABELS = {
  income:   { de: 'Einnahmen',  en: 'Income' },
  fixed:    { de: 'Fixkosten',  en: 'Fixed' },
  variable: { de: 'Variable',   en: 'Variable' },
}
function groupLabel(type) {
  const g = GROUP_LABELS[type]
  return g ? (locale.value === 'de' ? g.de : g.en) : type
}
</script>

<template>
  <!-- Backdrop -->
  <div class="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-4">
    <div class="absolute inset-0 bg-black/70 backdrop-blur-md" />

    <!-- Card -->
    <div
      class="relative w-full sm:max-w-md rounded-t-3xl sm:rounded-3xl border overflow-hidden shadow-2xl shadow-black/60"
      style="background: #09101f; border-color: rgba(255,255,255,0.08); max-height: 92dvh;"
    >
      <!-- Top accent line -->
      <div class="h-0.5 w-full bg-gradient-to-r from-transparent via-emerald-500 to-transparent opacity-60" />

      <!-- Step progress dots (steps 1–3) -->
      <div v-if="step >= 1 && step <= 3" class="flex items-center justify-center gap-2 pt-5 pb-1">
        <div
          v-for="n in 3"
          :key="n"
          class="h-1.5 rounded-full transition-all duration-300"
          :class="n <= step
            ? 'bg-emerald-400 w-6'
            : 'bg-white/15 w-3'"
        />
      </div>

      <!-- Scrollable content area -->
      <div class="overflow-y-auto" style="max-height: calc(92dvh - 80px)">
        <Transition name="fade" mode="out-in">

          <!-- ══ Step 0: Welcome ══════════════════════════════════════ -->
          <div v-if="step === 0" key="0" class="px-7 pt-8 pb-6 text-center">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center mx-auto mb-6 shadow-xl shadow-emerald-500/30">
              <span class="text-2xl font-black text-white">HL</span>
            </div>
            <h1 class="text-2xl font-bold mb-3">{{ t('onboarding.welcome') }}</h1>
            <p class="text-sm text-muted-foreground leading-relaxed mb-8">
              {{ t('onboarding.welcomeDesc') }}
            </p>
            <!-- Feature bullets -->
            <div class="space-y-3 text-left mb-8">
              <div v-for="bullet in ['onboarding.f1','onboarding.f2','onboarding.f3']" :key="bullet"
                   class="flex items-center gap-3">
                <div class="w-6 h-6 rounded-lg bg-emerald-500/15 flex items-center justify-center shrink-0">
                  <Check class="h-3.5 w-3.5 text-emerald-400" />
                </div>
                <span class="text-sm text-muted-foreground">{{ t(bullet) }}</span>
              </div>
            </div>
            <button
              @click="next"
              class="w-full h-11 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20"
            >
              {{ t('onboarding.start') }}
              <ChevronRight class="h-4 w-4" />
            </button>
          </div>

          <!-- ══ Step 1: Household ════════════════════════════════════ -->
          <div v-else-if="step === 1" key="1" class="px-7 pt-6 pb-6">
            <h2 class="text-xl font-bold mb-1">{{ t('onboarding.household') }}</h2>
            <p class="text-sm text-muted-foreground mb-6">{{ t('onboarding.householdDesc') }}</p>

            <div class="space-y-1 mb-8">
              <label class="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                {{ t('onboarding.householdName') }}
              </label>
              <input
                v-model="householdName"
                type="text"
                class="w-full px-4 py-3 rounded-xl text-sm outline-none transition-colors"
                style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);"
                :style="householdName.trim() ? 'border-color: rgba(16,185,129,0.4)' : ''"
                @focus="(e) => e.target.style.borderColor = 'rgba(16,185,129,0.5)'"
                @blur="(e) => e.target.style.borderColor = householdName.trim() ? 'rgba(16,185,129,0.4)' : 'rgba(255,255,255,0.08)'"
                :placeholder="t('onboarding.householdName')"
              />
            </div>

            <div class="flex gap-3">
              <button @click="back"
                class="h-11 px-4 rounded-xl text-sm text-muted-foreground transition-colors flex items-center gap-1.5"
                style="background: rgba(255,255,255,0.05)">
                <ChevronLeft class="h-4 w-4" />{{ t('onboarding.back') }}
              </button>
              <button
                @click="next"
                :disabled="!householdName.trim() || loading"
                class="flex-1 h-11 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20"
              >
                <span v-if="loading">{{ t('onboarding.creating') }}</span>
                <template v-else>
                  {{ t('onboarding.next') }}
                  <ChevronRight class="h-4 w-4" />
                </template>
              </button>
            </div>
          </div>

          <!-- ══ Step 2: Accounts ═════════════════════════════════════ -->
          <div v-else-if="step === 2" key="2" class="px-7 pt-6 pb-6">
            <h2 class="text-xl font-bold mb-1">{{ t('onboarding.accounts') }}</h2>
            <p class="text-sm text-muted-foreground mb-5">{{ t('onboarding.accountsDesc') }}</p>

            <div class="space-y-4 mb-4">
              <div
                v-for="(acc, i) in accounts"
                :key="i"
                class="rounded-2xl p-4 space-y-3"
                style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07)"
              >
                <div class="flex items-center justify-between">
                  <span class="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    {{ t('onboarding.account') }} {{ i + 1 }}
                  </span>
                  <button
                    v-if="accounts.length > 1"
                    @click="removeAccount(i)"
                    class="p-1 rounded-lg hover:bg-rose-500/10 hover:text-rose-400 text-muted-foreground transition-colors"
                  >
                    <Trash2 class="h-3.5 w-3.5" />
                  </button>
                </div>

                <!-- Account name -->
                <input
                  v-model="acc.name"
                  type="text"
                  class="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
                  style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08)"
                  :placeholder="t('onboarding.accountName')"
                />

                <!-- Type selector -->
                <div class="grid grid-cols-3 gap-1.5">
                  <button
                    v-for="type in ACCOUNT_TYPES"
                    :key="type.value"
                    @click="acc.account_type = type.value"
                    class="flex flex-col items-center gap-1 py-2.5 px-2 rounded-xl text-[11px] font-medium transition-all"
                    :class="acc.account_type === type.value
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                      : 'text-muted-foreground border border-transparent hover:bg-white/5'"
                  >
                    <component :is="type.icon" class="h-4 w-4" />
                    {{ locale === 'de' ? type.labelDe : type.labelEn }}
                  </button>
                </div>

                <!-- Starting balance -->
                <div class="flex items-center gap-2">
                  <input
                    v-model="acc.starting_balance"
                    type="number"
                    step="0.01"
                    class="flex-1 px-3 py-2.5 rounded-xl text-sm outline-none tabular-nums"
                    style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08)"
                    :placeholder="t('onboarding.startBalance')"
                  />
                  <span class="text-sm font-semibold text-muted-foreground w-10 text-right">EUR</span>
                </div>
              </div>
            </div>

            <!-- Add account -->
            <button
              @click="addAccount"
              class="w-full h-10 rounded-xl text-sm text-muted-foreground hover:text-emerald-400 transition-colors flex items-center justify-center gap-2 mb-6"
              style="border: 1px dashed rgba(255,255,255,0.12)"
            >
              <Plus class="h-4 w-4" />
              {{ t('onboarding.addAccount') }}
            </button>

            <div class="flex gap-3">
              <button @click="back"
                class="h-11 px-4 rounded-xl text-sm text-muted-foreground transition-colors flex items-center gap-1.5"
                style="background: rgba(255,255,255,0.05)">
                <ChevronLeft class="h-4 w-4" />{{ t('onboarding.back') }}
              </button>
              <button
                @click="next"
                :disabled="!accountsValid"
                class="flex-1 h-11 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20"
              >
                {{ t('onboarding.next') }}
                <ChevronRight class="h-4 w-4" />
              </button>
            </div>
          </div>

          <!-- ══ Step 3: Categories ═══════════════════════════════════ -->
          <div v-else-if="step === 3" key="3" class="px-7 pt-6 pb-6">
            <h2 class="text-xl font-bold mb-1">{{ t('onboarding.categories') }}</h2>
            <p class="text-sm text-muted-foreground mb-4">{{ t('onboarding.categoriesDesc') }}</p>

            <!-- Select all / none -->
            <div class="flex gap-2 mb-5">
              <button
                @click="selectAllCats"
                class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
                :class="selectedCats.size === DEFAULT_CATS.length
                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                  : 'text-muted-foreground border border-white/10 hover:border-white/20'"
              >
                {{ t('onboarding.selectAll') }}
              </button>
              <button
                @click="selectNoneCats"
                class="px-3 py-1.5 rounded-lg text-xs font-medium text-muted-foreground border border-white/10 hover:border-white/20 transition-colors"
              >
                {{ t('onboarding.selectNone') }}
              </button>
              <span class="ml-auto text-xs text-muted-foreground self-center">
                {{ selectedCats.size }}/{{ DEFAULT_CATS.length }}
              </span>
            </div>

            <!-- Category groups -->
            <div class="space-y-5 mb-6">
              <div v-for="(type, key) in catsByType" :key="key">
                <p class="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  {{ groupLabel(key) }}
                </p>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="{ cat, i } in type"
                    :key="i"
                    @click="toggleCat(i)"
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all border"
                    :class="selectedCats.has(i)
                      ? 'text-white border-transparent'
                      : 'text-muted-foreground border-white/10 hover:border-white/20'"
                    :style="selectedCats.has(i) ? `background: ${cat.color}25; border-color: ${cat.color}60; color: ${cat.color}` : ''"
                  >
                    <span
                      class="w-2 h-2 rounded-full shrink-0"
                      :style="`background: ${cat.color}`"
                    />
                    {{ catName(cat) }}
                  </button>
                </div>
              </div>
            </div>

            <div class="flex gap-3 flex-col">
              <button
                @click="next"
                :disabled="loading"
                class="w-full h-11 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-40 text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20"
              >
                <span v-if="loading">{{ t('onboarding.creating') }}</span>
                <template v-else>
                  <Sparkles class="h-4 w-4" />
                  {{ t('onboarding.finish') }}
                </template>
              </button>
              <div class="flex gap-3">
                <button @click="back"
                  class="h-10 px-4 rounded-xl text-sm text-muted-foreground transition-colors flex items-center gap-1.5"
                  style="background: rgba(255,255,255,0.05)">
                  <ChevronLeft class="h-4 w-4" />{{ t('onboarding.back') }}
                </button>
                <button
                  @click="skipCategories"
                  :disabled="loading"
                  class="flex-1 h-10 rounded-xl text-sm text-muted-foreground hover:text-foreground transition-colors"
                  style="border: 1px solid rgba(255,255,255,0.08)"
                >
                  {{ t('onboarding.skip') }}
                </button>
              </div>
            </div>
          </div>

          <!-- ══ Step 4: Done ═════════════════════════════════════════ -->
          <div v-else-if="step === 4" key="4" class="px-7 pt-8 pb-8 text-center">
            <div class="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center mx-auto mb-6 shadow-xl shadow-emerald-500/30 animate-pop">
              <Check class="h-8 w-8 text-white stroke-[2.5]" />
            </div>
            <h2 class="text-2xl font-bold mb-2">{{ t('onboarding.done') }}</h2>
            <p class="text-sm text-muted-foreground mb-2">{{ t('onboarding.doneDesc') }}</p>
            <p class="text-xs text-muted-foreground mb-8">
              <span class="text-emerald-400 font-semibold">{{ summary.accounts }}</span>
              {{ t('onboarding.summaryAccounts') }} ·
              <span class="text-emerald-400 font-semibold">{{ summary.categories }}</span>
              {{ t('onboarding.summaryCategories') }}
            </p>
            <button
              @click="emit('done')"
              class="w-full h-11 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-semibold text-sm transition-colors shadow-lg shadow-emerald-500/20"
            >
              {{ t('onboarding.toDashboard') }}
            </button>
          </div>

        </Transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.fade-enter-from { opacity: 0; transform: translateY(6px); }
.fade-leave-to   { opacity: 0; transform: translateY(-6px); }

@keyframes pop {
  0%   { transform: scale(0.6); opacity: 0; }
  70%  { transform: scale(1.12); }
  100% { transform: scale(1); opacity: 1; }
}
.animate-pop { animation: pop 0.45s cubic-bezier(0.34, 1.56, 0.64, 1) forwards; }
</style>
