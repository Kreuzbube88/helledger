<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Sun, Moon, ChevronDown, LogOut, Menu } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useApi } from '@/lib/api'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { Separator } from '@/components/ui/separator'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const theme = useThemeStore()
const api = useApi()

const households = ref([])
const activeHousehold = ref(null)
const mobileOpen = ref(false)

const navItems = computed(() => {
  const items = [
    { key: 'dashboard', path: '/dashboard' },
    { key: 'accounts', path: '/accounts' },
    { key: 'categories', path: '/categories' },
    { key: 'transactions', path: '/transactions' },
    { key: 'reports', path: '/reports' },
    { key: 'import', path: '/import' },
    { key: 'settings', path: '/settings' },
  ]
  if (auth.isAdmin) items.push({ key: 'backup', path: '/backup' })
  if (auth.isAdmin) items.push({ key: 'admin', path: '/admin' })
  return items
})

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
  router.push('/login')
}

onMounted(loadHouseholds)
</script>

<template>
  <header class="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
    <div class="max-w-screen-xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
      <!-- Brand -->
      <RouterLink to="/dashboard" class="font-bold text-lg text-primary shrink-0">
        HELLEDGER
      </RouterLink>

      <!-- Desktop nav -->
      <nav class="hidden md:flex items-center gap-1 flex-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.key"
          :to="item.path"
          class="px-3 py-1.5 rounded-md text-sm transition-colors whitespace-nowrap"
          :class="
            route.path.startsWith(item.path)
              ? 'bg-primary/10 text-primary font-medium'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted'
          "
        >
          {{ t(`nav.${item.key}`) }}
        </RouterLink>
      </nav>

      <!-- Right section -->
      <div class="flex items-center gap-1 shrink-0">
        <!-- Household switcher -->
        <DropdownMenu v-if="auth.user">
          <DropdownMenuTrigger as-child>
            <Button variant="ghost" size="sm" class="gap-1 max-w-40 hidden sm:flex">
              <span class="truncate text-sm">{{ activeHousehold?.name || '...' }}</span>
              <ChevronDown class="h-3 w-3 shrink-0" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" class="w-52">
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

        <!-- User name -->
        <span v-if="auth.user" class="text-sm text-muted-foreground hidden lg:block px-2">
          {{ auth.user.name }}
        </span>

        <!-- Dark/Light toggle -->
        <div class="flex items-center gap-1 px-1">
          <Sun class="h-4 w-4 text-muted-foreground" />
          <Switch :checked="theme.isDark" @update:checked="theme.toggle" />
          <Moon class="h-4 w-4 text-muted-foreground" />
        </div>

        <!-- Logout -->
        <Button variant="ghost" size="icon" @click="handleLogout" class="hidden sm:flex">
          <LogOut class="h-4 w-4" />
        </Button>

        <!-- Mobile hamburger -->
        <Sheet v-model:open="mobileOpen">
          <SheetTrigger as-child>
            <Button variant="ghost" size="icon" class="md:hidden">
              <Menu class="h-4 w-4" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" class="w-64 pt-10">
            <nav class="flex flex-col gap-1">
              <RouterLink
                v-for="item in navItems"
                :key="item.key"
                :to="item.path"
                class="px-3 py-2 rounded-md text-sm transition-colors"
                :class="
                  route.path.startsWith(item.path)
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                "
                @click="mobileOpen = false"
              >
                {{ t(`nav.${item.key}`) }}
              </RouterLink>
            </nav>
            <Separator class="my-4" />
            <div class="px-3 space-y-2">
              <p class="text-sm text-muted-foreground">{{ auth.user?.name }}</p>
              <Button variant="outline" size="sm" class="w-full" @click="handleLogout">
                {{ t('nav.logout') }}
              </Button>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </div>
  </header>
</template>
