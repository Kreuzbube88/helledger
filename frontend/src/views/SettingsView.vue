<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { useApi } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'

const { t, locale } = useI18n()
const api = useApi()
const auth = useAuthStore()

const profileName = ref(auth.user?.name || '')
const profileLang = ref(auth.user?.language || 'de')
const currentPassword = ref('')
const newPassword = ref('')

async function saveProfile() {
  const r = await api.patch('/users/me', { name: profileName.value, language: profileLang.value })
  if (r.ok) {
    locale.value = profileLang.value
    localStorage.setItem('helledger-lang', profileLang.value)
    await auth.fetchUser()
    toast.success(t('settings.save'))
  }
}

async function changePassword() {
  if (!currentPassword.value || !newPassword.value) return
  const r = await api.post('/auth/change-password', {
    current_password: currentPassword.value,
    new_password: newPassword.value,
  })
  if (r.ok) {
    currentPassword.value = ''
    newPassword.value = ''
    toast.success(t('settings.passwordChanged'))
  } else {
    toast.error(t('errors.generic'))
  }
}

const household = ref(null)
const members = ref([])
const householdName = ref('')
const memberEmail = ref('')

const activeHhId = computed(() => auth.user?.active_household_id)

async function load() {
  if (!activeHhId.value) return
  const [hhRes, membersRes] = await Promise.all([
    api.get('/households'),
    api.get(`/households/${activeHhId.value}/members`),
  ])
  if (hhRes.ok) {
    const all = await hhRes.json()
    household.value = all.find((h) => h.id === activeHhId.value) || null
    householdName.value = household.value?.name || ''
  }
  if (membersRes.ok) members.value = await membersRes.json()
}

async function saveName() {
  if (!activeHhId.value) return
  const res = await api.patch(`/households/${activeHhId.value}`, { name: householdName.value })
  if (res.ok) {
    await auth.fetchUser()
    toast.success(t('settings.save'))
  } else {
    toast.error(t('errors.generic'))
  }
}

async function addMember() {
  if (!memberEmail.value || !activeHhId.value) return
  const res = await api.post(`/households/${activeHhId.value}/members`, { email: memberEmail.value })
  if (res.ok) {
    memberEmail.value = ''
    await load()
    toast.success(t('settings.add'))
  } else {
    toast.error(t('errors.generic'))
  }
}

async function removeMember(userId) {
  if (!activeHhId.value) return
  if (!confirm(t('settings.remove') + '?')) return
  const res = await api.delete(`/households/${activeHhId.value}/members/${userId}`)
  if (res.ok) { await load(); toast.success(t('settings.remove')) }
  else toast.error(t('errors.generic'))
}

onMounted(load)
</script>

<template>
  <div class="min-h-dvh bg-background">
    <main class="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <h1 class="text-2xl font-bold">{{ t('settings.title') }}</h1>

      <!-- Profile -->
      <Card>
        <CardHeader><CardTitle>{{ $t('settings.profile') }}</CardTitle></CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-1">
            <Label>{{ $t('settings.changeName') }}</Label>
            <Input v-model="profileName" />
          </div>
          <div class="space-y-1">
            <Label>{{ $t('settings.changeLanguage') }}</Label>
            <Select v-model="profileLang">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="de">{{ $t('lang.de') }}</SelectItem>
                <SelectItem value="en">{{ $t('lang.en') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button @click="saveProfile">{{ $t('settings.saveProfile') }}</Button>
        </CardContent>
      </Card>

      <!-- Change password -->
      <Card class="mt-4">
        <CardHeader><CardTitle>{{ $t('settings.changePassword') }}</CardTitle></CardHeader>
        <CardContent class="space-y-4">
          <div class="space-y-1">
            <Label>{{ $t('settings.currentPassword') }}</Label>
            <Input type="password" v-model="currentPassword" />
          </div>
          <div class="space-y-1">
            <Label>{{ $t('settings.newPassword') }}</Label>
            <Input type="password" v-model="newPassword" />
          </div>
          <Button @click="changePassword">{{ $t('settings.changePassword') }}</Button>
        </CardContent>
      </Card>

      <!-- Household name -->
      <Card>
        <CardHeader><CardTitle>{{ t('settings.household') }}</CardTitle></CardHeader>
        <CardContent>
          <form @submit.prevent="saveName" class="flex gap-2">
            <div class="flex-1 space-y-1">
              <Label>{{ t('settings.householdName') }}</Label>
              <Input v-model="householdName" required />
            </div>
            <Button type="submit" class="self-end">{{ t('settings.save') }}</Button>
          </form>
        </CardContent>
      </Card>

      <!-- Members -->
      <Card>
        <CardHeader><CardTitle>{{ t('settings.members') }}</CardTitle></CardHeader>
        <CardContent class="space-y-4">
          <div class="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{{ t('auth.name') }}</TableHead>
                  <TableHead>{{ t('auth.email') }}</TableHead>
                  <TableHead>{{ t('accounts.type') }}</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="m in members" :key="m.id">
                  <TableCell class="font-medium">{{ m.name }}</TableCell>
                  <TableCell class="text-muted-foreground text-sm">{{ m.email }}</TableCell>
                  <TableCell>
                    <Badge :variant="m.role === 'owner' ? 'default' : 'secondary'">
                      {{ t(`settings.roles.${m.role}`) }}
                    </Badge>
                  </TableCell>
                  <TableCell class="text-right">
                    <Button
                      v-if="m.role !== 'owner'"
                      variant="ghost"
                      size="sm"
                      class="text-destructive hover:text-destructive"
                      @click="removeMember(m.id)"
                    >
                      {{ t('settings.remove') }}
                    </Button>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>

          <!-- Add member -->
          <form @submit.prevent="addMember" class="flex gap-2">
            <Input
              v-model="memberEmail"
              type="email"
              :placeholder="t('settings.memberEmail')"
              class="flex-1"
              required
            />
            <Button type="submit">{{ t('settings.add') }}</Button>
          </form>
        </CardContent>
      </Card>
    </main>
  </div>
</template>
