<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'

const { t, locale } = useI18n()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const activeTab = ref(route.path === '/register' ? 'register' : 'login')
const loading = ref(false)
const oidcEnabled = ref(false)
const needsSetup = ref(false)

onMounted(async () => {
  try {
    const [oidcRes, setupRes] = await Promise.all([
      fetch('/api/auth/oidc/enabled'),
      fetch('/api/auth/setup-status'),
    ])
    if (oidcRes.ok) oidcEnabled.value = (await oidcRes.json()).enabled
    if (setupRes.ok) needsSetup.value = (await setupRes.json()).needs_setup
  } catch {}
})

function loginWithOidc() {
  window.location.href = '/api/auth/oidc/login'
}

const loginForm = ref({ email: '', password: '', rememberMe: true })
const registerForm = ref({ name: '', email: '', password: '', confirmPassword: '', language: locale.value || 'de' })

watch(() => registerForm.value.language, (lang) => {
  locale.value = lang
  localStorage.setItem('helledger-lang', lang)
})

function validateRegister() {
  if (registerForm.value.password.length < 8) {
    toast.error(t('auth.passwordTooShort'))
    return false
  }
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    toast.error(t('auth.passwordMismatch'))
    return false
  }
  return true
}

async function handleLogin() {
  loading.value = true
  try {
    await auth.login(loginForm.value.email, loginForm.value.password, loginForm.value.rememberMe)
    router.push('/dashboard')
  } catch (err) {
    const detail = err?.detail || ''
    const key = detail === 'invalid_credentials' ? 'errors.invalid_credentials'
      : detail === 'registration_disabled' ? 'errors.registration_disabled'
      : 'errors.generic'
    toast.error(t(key))
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!validateRegister()) return
  loading.value = true
  try {
    await auth.register(registerForm.value.name, registerForm.value.email, registerForm.value.password, registerForm.value.language)
    locale.value = registerForm.value.language
    localStorage.setItem('helledger-lang', registerForm.value.language)
    router.push('/dashboard')
  } catch (err) {
    const detail = err?.detail || ''
    const key = detail === 'email_taken' ? 'errors.email_taken'
      : detail === 'registration_disabled' ? 'errors.registration_disabled'
      : 'errors.generic'
    toast.error(t(key))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-dvh flex items-center justify-center bg-background px-4 relative overflow-hidden">
    <div class="w-full max-w-sm relative z-10">
      <!-- Brand -->
      <div class="text-center mb-8 anim-fade-up">
        <div class="flex items-center justify-center mb-4">
          <div class="w-14 h-14 rounded-2xl overflow-hidden logo-ring shadow-xl shadow-emerald-500/25">
            <img src="/favicon.png" class="w-full h-full object-cover" alt="HELLEDGER" />
          </div>
        </div>
        <h1 class="text-xl font-bold tracking-widest uppercase bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
          HELLEDGER
        </h1>
        <p class="text-xs text-muted-foreground mt-1.5 tracking-wide">{{ t('app.tagline') }}</p>
      </div>

      <!-- First-time setup: no users exist yet -->
      <Card v-if="needsSetup">
        <CardHeader>
          <CardTitle>{{ t('auth.setupTitle') }}</CardTitle>
          <CardDescription>{{ t('auth.setupDescription') }}</CardDescription>
        </CardHeader>
        <CardContent>
          <form @submit.prevent="handleRegister" class="space-y-4">
            <div class="space-y-1">
              <Label>{{ t('auth.name') }}</Label>
              <Input v-model="registerForm.name" type="text" required autocomplete="name" />
            </div>
            <div class="space-y-1">
              <Label>{{ t('auth.email') }}</Label>
              <Input v-model="registerForm.email" type="email" required autocomplete="email" />
            </div>
            <div class="space-y-1">
              <Label>{{ t('auth.password') }}</Label>
              <Input
                v-model="registerForm.password"
                type="password"
                required
                autocomplete="new-password"
                :placeholder="t('auth.passwordHint')"
              />
            </div>
            <div class="space-y-1">
              <Label>{{ t('auth.confirmPassword') }}</Label>
              <Input
                v-model="registerForm.confirmPassword"
                type="password"
                required
                autocomplete="new-password"
              />
            </div>
            <div class="space-y-1">
              <Label>{{ t('settings.changeLanguage') }}</Label>
              <Select v-model="registerForm.language">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="de">{{ t('lang.de') }}</SelectItem>
                  <SelectItem value="en">{{ t('lang.en') }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button type="submit" class="w-full" :disabled="loading">
              {{ t('auth.setupCreate') }}
            </Button>
          </form>
        </CardContent>
      </Card>

      <!-- Normal login / register tabs -->
      <Tabs v-else v-model="activeTab">
        <TabsList class="w-full">
          <TabsTrigger value="login" class="flex-1">{{ t('auth.login') }}</TabsTrigger>
          <TabsTrigger value="register" class="flex-1">{{ t('auth.register') }}</TabsTrigger>
        </TabsList>

        <TabsContent value="login">
          <Card>
            <CardHeader>
              <CardTitle>{{ t('auth.loginTitle') }}</CardTitle>
            </CardHeader>
            <CardContent>
              <form @submit.prevent="handleLogin" class="space-y-4">
                <div class="space-y-1">
                  <Label>{{ t('auth.email') }}</Label>
                  <Input v-model="loginForm.email" type="email" required autocomplete="email" />
                </div>
                <div class="space-y-1">
                  <Label>{{ t('auth.password') }}</Label>
                  <Input
                    v-model="loginForm.password"
                    type="password"
                    required
                    autocomplete="current-password"
                  />
                </div>
                <div class="flex items-center gap-2">
                  <input
                    id="rememberMe"
                    type="checkbox"
                    v-model="loginForm.rememberMe"
                    class="h-4 w-4 rounded border-input accent-primary cursor-pointer"
                  />
                  <label for="rememberMe" class="text-sm cursor-pointer select-none">
                    {{ t('auth.rememberMe') }}
                  </label>
                </div>
                <Button type="submit" class="w-full" :disabled="loading">
                  {{ t('auth.login') }}
                </Button>
              </form>
              <template v-if="oidcEnabled">
                <Separator class="my-4" />
                <p class="text-center text-sm text-muted-foreground mb-3">{{ t('auth.orContinueWith') }}</p>
                <Button variant="outline" class="w-full" @click="loginWithOidc">
                  {{ t('auth.ssoLogin') }}
                </Button>
              </template>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="register">
          <Card>
            <CardHeader>
              <CardTitle>{{ t('auth.registerTitle') }}</CardTitle>
            </CardHeader>
            <CardContent>
              <form @submit.prevent="handleRegister" class="space-y-4">
                <div class="space-y-1">
                  <Label>{{ t('auth.name') }}</Label>
                  <Input v-model="registerForm.name" type="text" required autocomplete="name" />
                </div>
                <div class="space-y-1">
                  <Label>{{ t('auth.email') }}</Label>
                  <Input v-model="registerForm.email" type="email" required autocomplete="email" />
                </div>
                <div class="space-y-1">
                  <Label>{{ t('auth.password') }}</Label>
                  <Input
                    v-model="registerForm.password"
                    type="password"
                    required
                    autocomplete="new-password"
                    :placeholder="t('auth.passwordHint')"
                  />
                </div>
                <div class="space-y-1">
                  <Label>{{ t('auth.confirmPassword') }}</Label>
                  <Input
                    v-model="registerForm.confirmPassword"
                    type="password"
                    required
                    autocomplete="new-password"
                  />
                </div>
                <Button type="submit" class="w-full" :disabled="loading">
                  {{ t('auth.register') }}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  </div>
</template>
