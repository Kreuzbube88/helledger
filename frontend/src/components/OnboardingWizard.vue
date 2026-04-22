<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { toast } from 'vue-sonner'
import {
  Check, Plus, Trash2, Building2, Wallet, CreditCard,
  ChevronRight, ChevronLeft, Sparkles,
  LayoutDashboard, Receipt, CalendarDays, BarChart3,
  Tag, RefreshCw, Landmark, LineChart, Target, MapPin,
} from 'lucide-vue-next'

const emit = defineEmits(['done'])
const { t, locale } = useI18n()
const api = useApi()
const auth = useAuthStore()

// ── Steps: 0=welcome  1=household  2=accounts  3=categories  4=done  5+=tour ──
const step = ref(0)
const loading = ref(false)

// ── Tour data ─────────────────────────────────────────────────────────
const TOUR = [
  {
    icon: LayoutDashboard,
    color: '#10b981',
    nav: { de: 'Dashboard', en: 'Dashboard' },
    title: { de: 'Dein Finanz-Cockpit', en: 'Your Finance Cockpit' },
    bullets: [
      { de: 'Aktuelle Monatsbilanz: Einnahmen, Ausgaben, Sparquote auf einen Blick', en: 'Current monthly balance: income, expenses, savings rate at a glance' },
      { de: 'KPIs: Sparquote, Schuldenquote, Notgroschen in Monaten', en: 'KPIs: savings rate, debt-to-income, emergency fund in months' },
      { de: 'Sparziele & Warnung bei ablaufenden Fixkosten', en: 'Savings goals & alerts for expiring fixed costs' },
    ],
  },
  {
    icon: Receipt,
    color: '#6366f1',
    nav: { de: 'Transaktionen', en: 'Transactions' },
    title: { de: 'Buchungen erfassen', en: 'Record Transactions' },
    bullets: [
      { de: 'Einnahmen, Ausgaben und Umbuchungen manuell eintragen', en: 'Manually enter income, expenses, and transfers' },
      { de: 'Monatlich blättern, nach Konto oder Kategorie filtern', en: 'Browse by month, filter by account or category' },
      { de: 'CSV/OFX-Import für schnellen Massenimport aus dem Banking', en: 'CSV/OFX import for bulk import from your bank export' },
    ],
  },
  {
    icon: CalendarDays,
    color: '#f59e0b',
    nav: { de: 'Monatsübersicht', en: 'Month Overview' },
    title: { de: 'Monatsübersicht', en: 'Month Overview' },
    bullets: [
      { de: 'Alle Buchungen des Monats gruppiert nach Einnahmen, Fixkosten und variablen Ausgaben', en: 'All bookings of the month grouped by income, fixed costs, and variable expenses' },
      { de: 'Summen je Abschnitt und Gesamtsaldo auf einen Blick', en: 'Totals per section and overall balance at a glance' },
      { de: 'Sparquote wird automatisch aus Einnahmen und Ausgaben berechnet', en: 'Savings rate is calculated automatically from income and expenses' },
    ],
  },
  {
    icon: BarChart3,
    color: '#8b5cf6',
    nav: { de: 'Jahresübersicht', en: 'Year Overview' },
    title: { de: '12-Monate auf einen Blick', en: '12 Months at a Glance' },
    bullets: [
      { de: 'Alle Kategorien als Tabelle über das gesamte Jahr', en: 'All categories as a table across the full year' },
      { de: 'Vergangene Monate = echte Buchungen, Zukunft = Planwerte (kursiv)', en: 'Past months = real bookings, future = planned values (italic)' },
      { de: 'Einnahmen grün, Ausgaben rot — auf einen Blick erkennbar', en: 'Income in green, expenses in red — recognizable at a glance' },
    ],
  },
  {
    icon: Tag,
    color: '#ec4899',
    nav: { de: 'Kategorien', en: 'Categories' },
    title: { de: 'Deine Budgetstruktur', en: 'Your Budget Structure' },
    bullets: [
      { de: 'Drei Typen: Einnahmen, Fixkosten, Variable Ausgaben', en: 'Three types: income, fixed costs, variable expenses' },
      { de: 'Unterkategorien möglich — z.B. "Wohnen → Miete, Strom, Wasser"', en: 'Sub-categories supported — e.g. "Housing → Rent, Electricity, Water"' },
      { de: 'Kategorien archivieren wenn sie nicht mehr benötigt werden', en: 'Archive categories when they are no longer needed' },
    ],
  },
  {
    icon: RefreshCw,
    color: '#14b8a6',
    nav: { de: 'Fixkosten', en: 'Fixed Costs' },
    title: { de: 'Fixposten & Automatikbuchungen', en: 'Fixed Costs & Auto-Bookings' },
    bullets: [
      { de: 'Gehalt, Miete, Versicherungen — alles als Fixposten mit Intervall hinterlegen', en: 'Salary, rent, insurance — set up everything as fixed costs with an interval' },
      { de: 'Beim Dashboard-Aufruf werden fällige Fixposten automatisch gebucht', en: 'Due fixed costs are booked automatically when opening the dashboard' },
      { de: 'Rücklagen-Übersicht: monatlicher Anteil für quartals-/jahresweise Kosten', en: 'Reserve overview: monthly share for quarterly/annual costs' },
    ],
  },
  {
    icon: Landmark,
    color: '#f97316',
    nav: { de: 'Kredite', en: 'Loans' },
    title: { de: 'Kredite & Tilgung', en: 'Loans & Repayment' },
    bullets: [
      { de: 'Kredit anlegen: Betrag, Zinssatz, Rate — eines wird berechnet', en: 'Create a loan: amount, rate, payment — one gets computed automatically' },
      { de: 'Konto wählen → monatliche Rate wird automatisch gebucht', en: 'Choose an account → monthly payment is booked automatically' },
      { de: 'Sondertilgungen eintragen, Tilgungsplan als CSV exportieren', en: 'Add extra payments, export amortization schedule as CSV' },
    ],
  },
  {
    icon: LineChart,
    color: '#3b82f6',
    nav: { de: 'Berichte', en: 'Reports' },
    title: { de: 'Auswertungen & Charts', en: 'Reports & Charts' },
    bullets: [
      { de: 'Ausgaben nach Kategorie (Donut), Trend (Balken), Soll-Ist (Querbalken)', en: 'Expenses by category (donut), trend (bar), budget vs. actual (horizontal bar)' },
      { de: 'Kontostand-Verlauf für ein einzelnes Konto im Zeitraum', en: 'Balance history for a single account over a period' },
      { de: 'Zeitraum frei wählen: Monat, Jahr oder individuell — CSV-Export', en: 'Flexible period: month, year, or custom range — CSV export' },
    ],
  },
  {
    icon: Target,
    color: '#d946ef',
    nav: { de: 'Sparziele', en: 'Goals' },
    title: { de: 'Sparziele tracken', en: 'Track Savings Goals' },
    bullets: [
      { de: 'Ziel anlegen: Name, Zielbetrag, Zieldatum, verknüpftes Konto', en: 'Create a goal: name, target amount, target date, linked account' },
      { de: 'Fortschritt wird live aus dem Kontostand berechnet', en: 'Progress is calculated live from the account balance' },
      { de: 'Alle Ziele im Dashboard als Fortschrittsbalken sichtbar', en: 'All goals visible as progress bars in the dashboard' },
    ],
  },
]

const tourIdx = computed(() => Math.max(0, step.value - 5))
const tourStep = computed(() => TOUR[tourIdx.value])
const isTour = computed(() => step.value >= 5)

// ── Step 1: Household ─────────────────────────────────────────────────
const householdName = ref(`${auth.user?.name || 'Mein'}s Haushalt`)

// ── Step 2: Accounts ──────────────────────────────────────────────────
const accounts = ref([
  { name: '', account_type: 'checking', starting_balance: '', currency: 'EUR' },
])

const ACCOUNT_TYPES = [
  { value: 'checking', labelDe: 'Girokonto',   labelEn: 'Checking',  icon: Building2 },
  { value: 'savings',  labelDe: 'Sparkonto',    labelEn: 'Savings',   icon: Wallet },
  { value: 'credit_card', labelDe: 'Kreditkarte', labelEn: 'Credit Card', icon: CreditCard },
]

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
  // Income
  { de: 'Gehalt',              en: 'Salary',              type: 'income',   color: '#10b981' },
  { de: 'Nebeneinkommen',      en: 'Side Income',         type: 'income',   color: '#34d399' },
  { de: 'Sonstige Einnahmen',  en: 'Other Income',        type: 'income',   color: '#6ee7b7' },
  // Fixed
  { de: 'Miete',               en: 'Rent',                type: 'fixed',    color: '#8b5cf6' },
  { de: 'Strom',               en: 'Electricity',         type: 'fixed',    color: '#7c3aed' },
  { de: 'Gas & Heizung',       en: 'Gas & Heating',       type: 'fixed',    color: '#6d28d9' },
  { de: 'Wasser',              en: 'Water',               type: 'fixed',    color: '#4f46e5' },
  { de: 'Internet',            en: 'Internet',            type: 'fixed',    color: '#a78bfa' },
  { de: 'Telefon & Handy',     en: 'Phone & Mobile',      type: 'fixed',    color: '#c4b5fd' },
  { de: 'Rundfunk (GEZ)',      en: 'Broadcasting Fee',    type: 'fixed',    color: '#818cf8' },
  { de: 'Versicherungen',      en: 'Insurance',           type: 'fixed',    color: '#9333ea' },
  { de: 'Abonnements',         en: 'Subscriptions',       type: 'fixed',    color: '#7e22ce' },
  { de: 'Kreditrate',          en: 'Loan Payment',        type: 'fixed',    color: '#5b21b6' },
  { de: 'Kita & Schule',       en: 'Childcare & School',  type: 'fixed',    color: '#6366f1' },
  { de: 'Sparen & Vorsorge',   en: 'Savings & Pension',   type: 'fixed',    color: '#4338ca' },
  // Variable
  { de: 'Lebensmittel',        en: 'Groceries',           type: 'variable', color: '#3b82f6' },
  { de: 'Drogerie & Haushalt', en: 'Drugstore & Home',    type: 'variable', color: '#60a5fa' },
  { de: 'Restaurants',         en: 'Restaurants',         type: 'variable', color: '#2563eb' },
  { de: 'Kaffee & Snacks',     en: 'Coffee & Snacks',     type: 'variable', color: '#93c5fd' },
  { de: 'Kleidung',            en: 'Clothing',            type: 'variable', color: '#f97316' },
  { de: 'Transport & ÖPNV',    en: 'Transport & Transit', type: 'variable', color: '#fb923c' },
  { de: 'Auto & Kraftstoff',   en: 'Car & Fuel',          type: 'variable', color: '#ea580c' },
  { de: 'Gesundheit & Arzt',   en: 'Health & Doctor',     type: 'variable', color: '#ec4899' },
  { de: 'Apotheke',            en: 'Pharmacy',            type: 'variable', color: '#f472b6' },
  { de: 'Freizeit & Kultur',   en: 'Leisure & Culture',   type: 'variable', color: '#f59e0b' },
  { de: 'Sport & Fitness',     en: 'Sports & Fitness',    type: 'variable', color: '#14b8a6' },
  { de: 'Hobbys',              en: 'Hobbies',             type: 'variable', color: '#fbbf24' },
  { de: 'Urlaub & Reisen',     en: 'Travel & Vacation',   type: 'variable', color: '#d97706' },
  { de: 'Elektronik',          en: 'Electronics',         type: 'variable', color: '#06b6d4' },
  { de: 'Bildung',             en: 'Education',           type: 'variable', color: '#0ea5e9' },
  { de: 'Kinder',              en: 'Children',            type: 'variable', color: '#0284c7' },
  { de: 'Haustiere',           en: 'Pets',                type: 'variable', color: '#16a34a' },
  { de: 'Geschenke & Spenden', en: 'Gifts & Donations',   type: 'variable', color: '#d946ef' },
  { de: 'Sonstiges',           en: 'Miscellaneous',       type: 'variable', color: '#94a3b8' },
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
  if (isTour.value) {
    if (tourIdx.value === 0) { step.value = 4 } else { step.value-- }
  } else if (step.value > 0) {
    step.value--
  }
}

function startTour() {
  step.value = 5
}

function nextTour() {
  if (tourIdx.value < TOUR.length - 1) {
    step.value++
  } else {
    emit('done')
  }
}

async function finish() {
  loading.value = true
  try {
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

function groupLabel(type) {
  return t(`categories.types.${type}`) || type
}

function loc(obj) {
  return locale.value === 'de' ? obj.de : obj.en
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
      <!-- Top accent line — changes color in tour mode -->
      <div
        class="h-0.5 w-full transition-all duration-500"
        :style="isTour
          ? `background: linear-gradient(to right, transparent, ${tourStep.color}, transparent); opacity: 0.8`
          : 'background: linear-gradient(to right, transparent, #10b981, transparent); opacity: 0.6'"
      />

      <!-- Progress: setup dots (steps 1–3) -->
      <div v-if="step >= 1 && step <= 3" class="flex items-center justify-center gap-2 pt-5 pb-1">
        <div
          v-for="n in 3"
          :key="n"
          class="h-1.5 rounded-full transition-all duration-300"
          :class="n <= step ? 'bg-emerald-400 w-6' : 'bg-white/15 w-3'"
        />
      </div>

      <!-- Progress: tour steps -->
      <div v-if="isTour" class="flex items-center justify-between px-7 pt-5 pb-1">
        <span class="text-xs text-muted-foreground font-medium">
          {{ locale === 'de' ? 'Feature-Tour' : 'Feature Tour' }}
        </span>
        <div class="flex items-center gap-1.5">
          <div
            v-for="(_, i) in TOUR"
            :key="i"
            class="h-1 rounded-full transition-all duration-300"
            :class="i <= tourIdx ? 'w-4' : 'w-1.5 bg-white/15'"
            :style="i <= tourIdx ? `background: ${tourStep.color}; width: 1rem` : ''"
          />
        </div>
        <span class="text-xs text-muted-foreground">{{ tourIdx + 1 }}/{{ TOUR.length }}</span>
      </div>

      <!-- Scrollable content area -->
      <div class="overflow-y-auto" style="max-height: calc(92dvh - 80px)">
        <Transition name="fade" mode="out-in">

          <!-- ══ Step 0: Welcome ══════════════════════════════════════ -->
          <div v-if="step === 0" key="0" class="px-7 pt-8 pb-6 text-center">
            <div class="w-16 h-16 rounded-2xl overflow-hidden mx-auto mb-6 logo-ring shadow-xl shadow-emerald-500/25">
              <img src="/favicon.png" class="w-full h-full object-cover" alt="HELLEDGER" />
            </div>
            <h1 class="text-2xl font-bold mb-3">{{ t('onboarding.welcome') }}</h1>
            <p class="text-sm text-muted-foreground leading-relaxed mb-8">
              {{ t('onboarding.welcomeDesc') }}
            </p>
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

                <input
                  v-model="acc.name"
                  type="text"
                  class="w-full px-3 py-2.5 rounded-xl text-sm outline-none"
                  style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08)"
                  :placeholder="t('onboarding.accountName')"
                />

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
                    <span class="w-2 h-2 rounded-full shrink-0" :style="`background: ${cat.color}`" />
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

            <!-- Tour CTA -->
            <div class="rounded-2xl p-4 mb-5 text-left" style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08)">
              <p class="text-sm font-semibold mb-1">
                {{ locale === 'de' ? '2-Minuten-Tour gefällig?' : '2-minute tour?' }}
              </p>
              <p class="text-xs text-muted-foreground leading-relaxed">
                {{ locale === 'de'
                  ? 'Wir zeigen dir kurz, wo was ist — 9 Funktionen, eine pro Slide.'
                  : 'Let us show you where everything is — 9 features, one slide each.' }}
              </p>
            </div>

            <button
              @click="startTour"
              class="w-full h-11 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/20 mb-3"
            >
              <MapPin class="h-4 w-4" />
              {{ locale === 'de' ? 'Tour starten' : 'Start tour' }}
            </button>
            <button
              @click="emit('done')"
              class="w-full h-10 rounded-xl text-sm text-muted-foreground hover:text-foreground transition-colors"
              style="border: 1px solid rgba(255,255,255,0.08)"
            >
              {{ locale === 'de' ? 'Direkt zum Dashboard' : 'Go to Dashboard' }}
            </button>
          </div>

          <!-- ══ Steps 5–13: Feature Tour ════════════════════════════ -->
          <div v-else-if="isTour" :key="`tour-${tourIdx}`" class="px-7 pt-5 pb-7">

            <!-- Icon -->
            <div
              class="w-14 h-14 rounded-2xl flex items-center justify-center mb-5 mx-auto shadow-lg"
              :style="`background: ${tourStep.color}20; box-shadow: 0 8px 24px ${tourStep.color}25`"
            >
              <component :is="tourStep.icon" class="h-7 w-7" :style="`color: ${tourStep.color}`" />
            </div>

            <!-- Nav badge -->
            <div class="flex justify-center mb-3">
              <span
                class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold uppercase tracking-wide"
                :style="`background: ${tourStep.color}15; color: ${tourStep.color}; border: 1px solid ${tourStep.color}30`"
              >
                <MapPin class="h-3 w-3" />
                {{ loc(tourStep.nav) }}
              </span>
            </div>

            <!-- Title -->
            <h2 class="text-xl font-bold text-center mb-5">{{ loc(tourStep.title) }}</h2>

            <!-- Bullets -->
            <div class="space-y-3 mb-8">
              <div
                v-for="(bullet, bi) in tourStep.bullets"
                :key="bi"
                class="flex items-start gap-3"
              >
                <div
                  class="w-5 h-5 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                  :style="`background: ${tourStep.color}20`"
                >
                  <Check class="h-3 w-3" :style="`color: ${tourStep.color}`" />
                </div>
                <p class="text-sm text-muted-foreground leading-relaxed">{{ loc(bullet) }}</p>
              </div>
            </div>

            <!-- Navigation -->
            <div class="flex gap-3">
              <button
                @click="back"
                class="h-11 px-4 rounded-xl text-sm text-muted-foreground transition-colors flex items-center gap-1.5 shrink-0"
                style="background: rgba(255,255,255,0.05)"
              >
                <ChevronLeft class="h-4 w-4" />
              </button>
              <button
                @click="nextTour"
                class="flex-1 h-11 rounded-xl text-white font-semibold text-sm transition-all flex items-center justify-center gap-2 shadow-lg"
                :style="`background: ${tourStep.color}; box-shadow: 0 4px 16px ${tourStep.color}35`"
              >
                <template v-if="tourIdx < TOUR.length - 1">
                  {{ locale === 'de' ? 'Weiter' : 'Next' }}
                  <ChevronRight class="h-4 w-4" />
                </template>
                <template v-else>
                  <Sparkles class="h-4 w-4" />
                  {{ locale === 'de' ? 'Los geht\'s!' : 'Let\'s go!' }}
                </template>
              </button>
            </div>

            <!-- Skip tour link -->
            <button
              v-if="tourIdx < TOUR.length - 1"
              @click="emit('done')"
              class="w-full mt-3 text-xs text-muted-foreground hover:text-foreground transition-colors text-center"
            >
              {{ locale === 'de' ? 'Tour überspringen' : 'Skip tour' }}
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
