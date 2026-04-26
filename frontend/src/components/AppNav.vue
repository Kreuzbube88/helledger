<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LayoutDashboard, Wallet, Tag, ArrowLeftRight, BarChart3,
  CalendarDays, CalendarRange, TrendingUp, Upload, Settings,
  HardDrive, Shield, LogOut, MoreHorizontal, Sun, Moon, X,
  ChevronDown, Landmark, RefreshCw, Target, Search,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useApi } from '@/lib/api'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import GlobalSearch from '@/components/GlobalSearch.vue'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const theme = useThemeStore()
const api = useApi()

const households = ref([])
const activeHousehold = ref(null)
const moreOpen = ref(false)
const searchOpen = ref(false)

const allNavItems = computed(() => {
  const items = [
    { key: 'dashboard',    path: '/dashboard',    icon: LayoutDashboard },
    { key: 'accounts',     path: '/accounts',     icon: Wallet },
    { key: 'transactions', path: '/transactions', icon: ArrowLeftRight },
    { key: 'fixedCosts',   path: '/fixed-costs',  icon: RefreshCw },
    { key: 'loans',        path: '/loans',        icon: Landmark },
    { key: 'goals',        path: '/goals',        icon: Target },
    { key: 'categories',   path: '/categories',   icon: Tag },
    { key: 'month',        path: '/month',        icon: CalendarRange },
    { key: 'year',         path: '/year',         icon: CalendarDays },
    { key: 'reports',      path: '/reports',      icon: BarChart3 },
    { key: 'forecast',     path: '/forecast',     icon: TrendingUp },
    { key: 'import',       path: '/import',       icon: Upload },
    { key: 'settings',     path: '/settings',     icon: Settings },
  ]
  if (auth.isAdmin) items.push({ key: 'backup', path: '/backup', icon: HardDrive })
  if (auth.isAdmin) items.push({ key: 'admin',  path: '/admin',  icon: Shield })
  return items
})

const PRIMARY_KEYS  = ['dashboard', 'transactions', 'accounts', 'month']
const bottomPrimary = computed(() =>
  PRIMARY_KEYS.map(k => allNavItems.value.find(i => i.key === k)).filter(Boolean)
)
const bottomMore    = computed(() => allNavItems.value.filter(i => !PRIMARY_KEYS.includes(i.key)))

const userInitial = computed(() =>
  auth.user?.name?.charAt(0)?.toUpperCase() || '?'
)

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

async function loadHouseholds() {
  const res = await api.get('/households')
  if (res.ok) {
    households.value = await res.json()
    activeHousehold.value =
      households.value.find((h) => h.id === auth.user?.active_household_id) || null
  }
}

async function switchHousehold(id) {
  await api.post(`/households/${id}/activate`, {})
  await auth.fetchUser()
  activeHousehold.value = households.value.find((h) => h.id === id) || null
  router.go(0)
}

function handleLogout() {
  auth.logout()
  moreOpen.value = false
  router.push('/login')
}

// Reload household list whenever the active household changes (e.g. after wizard)
watch(() => auth.user?.active_household_id, () => loadHouseholds(), { immediate: true })

function onKeydown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    searchOpen.value = true
  }
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <!-- ═══════════════════════════════════════════════════════════════
       DESKTOP SIDEBAR (md+)
  ═══════════════════════════════════════════════════════════════ -->
  <aside
    class="hidden md:flex flex-col fixed left-0 top-0 h-full w-64 z-40"
    :class="theme.isDark
      ? 'bg-[#060a14]/75 backdrop-blur-3xl sidebar-glow'
      : 'bg-white/95 backdrop-blur-2xl shadow-sm'"
  >
    <!-- Brand -->
    <div class="flex items-center gap-3 px-5 h-16 shrink-0 border-b relative overflow-hidden"
         :class="theme.isDark ? 'border-emerald-500/[0.08]' : 'border-gray-100'">
      <div v-if="theme.isDark" class="absolute inset-0 bg-gradient-to-r from-emerald-500/[0.06] via-transparent to-transparent pointer-events-none" />
      <div class="w-8 h-8 rounded-xl overflow-hidden shrink-0 logo-ring shadow-lg shadow-emerald-500/20">
        <img src="/favicon.png" class="w-full h-full object-cover" alt="HELLEDGER" />
      </div>
      <span class="font-bold text-sm tracking-widest uppercase text-foreground">Helledger</span>
    </div>

    <!-- Household switcher -->
    <div class="px-4 pt-4 pb-2 shrink-0">
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <button
            class="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs transition-colors text-muted-foreground hover:text-foreground"
            :class="theme.isDark ? 'bg-white/[0.05] hover:bg-white/[0.08]' : 'bg-gray-50 hover:bg-gray-100'"
          >
            <span class="truncate flex-1 text-left">{{ activeHousehold?.name || '—' }}</span>
            <ChevronDown class="h-3 w-3 shrink-0" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" class="w-52">
          <DropdownMenuItem
            v-for="hh in households"
            :key="hh.id"
            @click="switchHousehold(hh.id)"
            :class="hh.id === auth.user?.active_household_id ? 'text-primary' : ''"
          >
            {{ hh.name }}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>

    <!-- Search button -->
    <div class="px-3 pb-2">
      <button @click="searchOpen = true" class="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-muted-foreground transition-colors hover:bg-muted">
        <Search class="h-4 w-4" />
        <span class="text-xs">{{ t('search.placeholder') }}</span>
        <kbd class="ml-auto text-[10px] border rounded px-1">⌘K</kbd>
      </button>
    </div>

    <!-- Nav items -->
    <nav class="flex-1 px-3 py-2 overflow-y-auto space-y-0.5">
      <RouterLink
        v-for="item in allNavItems"
        :key="item.key"
        :to="item.path"
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all duration-150 group relative"
        :class="isActive(item.path)
          ? (theme.isDark
              ? 'bg-emerald-500/[0.12] text-emerald-400 font-medium'
              : 'bg-emerald-50 text-emerald-600 font-medium')
          : (theme.isDark
              ? 'text-muted-foreground hover:bg-white/[0.05] hover:text-foreground'
              : 'text-muted-foreground hover:bg-gray-50 hover:text-foreground')"
      >
        <component
          :is="item.icon"
          class="h-4 w-4 shrink-0 transition-colors"
          :class="isActive(item.path)
            ? (theme.isDark ? 'text-emerald-400' : 'text-emerald-500')
            : 'group-hover:text-foreground'"
        />
        <span>{{ t(`nav.${item.key}`) }}</span>
        <!-- Active dot -->
        <span
          v-if="isActive(item.path)"
          class="absolute right-3 w-1.5 h-1.5 rounded-full bg-emerald-400 nav-dot"
          style="box-shadow: 0 0 6px rgba(16,185,129,0.8)"
        />
      </RouterLink>
    </nav>

    <!-- User footer -->
    <div class="shrink-0 p-4 border-t relative"
         :class="theme.isDark ? 'border-emerald-500/[0.08]' : 'border-gray-100'">
      <div v-if="theme.isDark" class="absolute inset-0 bg-gradient-to-t from-emerald-500/[0.04] to-transparent pointer-events-none" />
      <div class="flex items-center gap-3 mb-3 px-1">
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-violet-400 to-purple-600 flex items-center justify-center text-[11px] font-bold text-white shrink-0 shadow-sm">
          {{ userInitial }}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-xs font-semibold truncate">{{ auth.user?.name }}</p>
          <p class="text-[10px] text-muted-foreground truncate">{{ auth.user?.email }}</p>
        </div>
      </div>
      <div class="flex gap-2">
        <button
          @click="theme.toggle"
          class="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-lg text-xs text-muted-foreground transition-colors"
          :class="theme.isDark ? 'hover:bg-white/[0.06]' : 'hover:bg-gray-100'"
        >
          <Sun v-if="theme.isDark" class="h-3.5 w-3.5" />
          <Moon v-else class="h-3.5 w-3.5" />
          {{ theme.isDark ? t('theme.light') : t('theme.dark') }}
        </button>
        <button
          @click="handleLogout"
          class="flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg text-xs transition-colors text-muted-foreground hover:bg-rose-500/10 hover:text-rose-400"
        >
          <LogOut class="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  </aside>

  <!-- ═══════════════════════════════════════════════════════════════
       MOBILE BOTTOM NAV (< md)
  ═══════════════════════════════════════════════════════════════ -->
  <nav
    class="md:hidden fixed bottom-0 left-0 right-0 z-50 border-t safe-bottom"
    :class="theme.isDark
      ? 'bg-[#05080f]/95 backdrop-blur-2xl border-white/[0.07]'
      : 'bg-white/97 backdrop-blur-2xl border-gray-200'"
  >
    <div class="flex items-center justify-around h-16">
      <RouterLink
        v-for="item in bottomPrimary"
        :key="item.key"
        :to="item.path"
        class="flex flex-col items-center gap-1 px-3 py-2 relative transition-all duration-150"
        :class="isActive(item.path)
          ? (theme.isDark ? 'text-emerald-400' : 'text-emerald-600')
          : 'text-muted-foreground'"
      >
        <!-- Active glow pill -->
        <span
          v-if="isActive(item.path)"
          class="absolute top-1.5 w-8 h-1 rounded-full bg-emerald-400/30 blur-sm"
        />
        <component :is="item.icon" class="h-5 w-5 relative z-10" />
        <span class="text-[9px] font-medium relative z-10">{{ t(`nav.${item.key}`) }}</span>
      </RouterLink>

      <!-- More button -->
      <button
        @click="moreOpen = true"
        class="flex flex-col items-center gap-1 px-3 py-2 text-muted-foreground transition-colors"
        :class="moreOpen ? (theme.isDark ? 'text-emerald-400' : 'text-emerald-600') : ''"
      >
        <MoreHorizontal class="h-5 w-5" />
        <span class="text-[9px] font-medium">{{ t('nav.more') }}</span>
      </button>
    </div>
  </nav>

  <!-- Mobile "More" sheet -->
  <Transition name="sheet">
    <div v-if="moreOpen" class="md:hidden fixed inset-0 z-50">
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/60 backdrop-blur-sm"
        @click="moreOpen = false"
      />
      <!-- Drawer -->
      <div
        class="absolute bottom-0 left-0 right-0 rounded-t-3xl border-t pt-5 pb-8 px-4"
        :class="theme.isDark
          ? 'bg-[#0c1020] border-white/[0.08]'
          : 'bg-white border-gray-100'"
        style="padding-bottom: calc(2rem + env(safe-area-inset-bottom))"
      >
        <!-- Handle bar -->
        <div class="w-10 h-1 rounded-full bg-white/20 mx-auto mb-5" />

        <div class="flex items-center justify-between mb-4">
          <span class="text-sm font-semibold">{{ t('nav.menu') }}</span>
          <button
            @click="moreOpen = false"
            class="p-1.5 rounded-lg transition-colors"
            :class="theme.isDark ? 'hover:bg-white/[0.07]' : 'hover:bg-gray-100'"
          >
            <X class="h-4 w-4 text-muted-foreground" />
          </button>
        </div>

        <!-- Search -->
        <button
          @click="moreOpen = false; searchOpen = true"
          class="w-full flex items-center gap-3 px-4 py-3 rounded-2xl mb-3 transition-all"
          :class="theme.isDark ? 'bg-white/[0.04] text-muted-foreground hover:bg-white/[0.08]' : 'bg-gray-50 text-muted-foreground hover:bg-gray-100'"
        >
          <Search class="h-5 w-5" />
          <span class="text-sm">{{ t('search.placeholder') }}</span>
          <kbd class="ml-auto text-[10px] border rounded px-1">⌘K</kbd>
        </button>

        <!-- Grid of remaining nav items -->
        <div class="grid grid-cols-3 gap-2 mb-5">
          <RouterLink
            v-for="item in bottomMore"
            :key="item.key"
            :to="item.path"
            @click="moreOpen = false"
            class="flex flex-col items-center gap-2 p-3.5 rounded-2xl transition-all"
            :class="isActive(item.path)
              ? (theme.isDark ? 'bg-emerald-500/15 text-emerald-400' : 'bg-emerald-50 text-emerald-600')
              : (theme.isDark ? 'bg-white/[0.04] text-muted-foreground hover:bg-white/[0.08]' : 'bg-gray-50 text-muted-foreground hover:bg-gray-100')"
          >
            <component :is="item.icon" class="h-5 w-5" />
            <span class="text-[11px] font-medium text-center leading-tight">{{ t(`nav.${item.key}`) }}</span>
          </RouterLink>
        </div>

        <!-- User row + actions -->
        <div
          class="flex items-center justify-between pt-4 border-t"
          :class="theme.isDark ? 'border-white/[0.06]' : 'border-gray-100'"
        >
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-full bg-gradient-to-br from-violet-400 to-purple-600 flex items-center justify-center text-xs font-bold text-white shadow-sm">
              {{ userInitial }}
            </div>
            <div>
              <p class="text-sm font-semibold">{{ auth.user?.name }}</p>
              <p class="text-xs text-muted-foreground">{{ auth.user?.email }}</p>
            </div>
          </div>
          <div class="flex gap-2">
            <button
              @click="theme.toggle"
              class="p-2.5 rounded-xl transition-colors"
              :class="theme.isDark ? 'bg-white/[0.06] hover:bg-white/10' : 'bg-gray-100 hover:bg-gray-200'"
            >
              <Sun v-if="theme.isDark" class="h-4 w-4" />
              <Moon v-else class="h-4 w-4" />
            </button>
            <button
              @click="handleLogout"
              class="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-colors"
            >
              <LogOut class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>

  <GlobalSearch :open="searchOpen" @close="searchOpen = false" />
</template>

<style scoped>
.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.25s ease;
}
.sheet-enter-active .absolute.bottom-0,
.sheet-leave-active .absolute.bottom-0 {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}
.sheet-enter-from .absolute.bottom-0,
.sheet-leave-to .absolute.bottom-0 {
  transform: translateY(100%);
}
</style>
