<script setup>
import { ref, onMounted } from 'vue'
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

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const activeTab = ref(route.path === '/register' ? 'register' : 'login')
const loading = ref(false)
const oidcEnabled = ref(false)

onMounted(async () => {
  try {
    const r = await fetch('/api/auth/oidc/enabled')
    const data = await r.json()
    oidcEnabled.value = data.enabled
  } catch {}
})

function loginWithOidc() {
  window.location.href = '/api/auth/oidc/login'
}

const loginForm = ref({ email: '', password: '' })
const registerForm = ref({ name: '', email: '', password: '' })

async function handleLogin() {
  loading.value = true
  try {
    await auth.login(loginForm.value.email, loginForm.value.password)
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
  loading.value = true
  try {
    await auth.register(registerForm.value.name, registerForm.value.email, registerForm.value.password)
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
  <div class="min-h-dvh flex items-center justify-center bg-background px-4">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-primary">HELLEDGER</h1>
        <p class="text-sm text-muted-foreground mt-1">{{ t('app.tagline') }}</p>
      </div>

      <Tabs v-model="activeTab">
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
                  <Input
                    v-model="loginForm.email"
                    type="email"
                    required
                    autocomplete="email"
                  />
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
                  <Input
                    v-model="registerForm.name"
                    type="text"
                    required
                    autocomplete="name"
                  />
                </div>
                <div class="space-y-1">
                  <Label>{{ t('auth.email') }}</Label>
                  <Input
                    v-model="registerForm.email"
                    type="email"
                    required
                    autocomplete="email"
                  />
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
