<!-- frontend/src/views/AdminView.vue -->
<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { useApi } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Switch } from '@/components/ui/switch'

const { t } = useI18n()
const api = useApi()

const users = ref([])
const status = ref(null)
const adminSettings = ref(null)

async function loadUsers() {
  const r = await api.get('/users')
  if (r.ok) users.value = await r.json()
}

async function loadStatus() {
  const r = await api.get('/admin/status')
  if (r.ok) status.value = await r.json()
}

async function loadSettings() {
  const r = await api.get('/admin/settings')
  if (r.ok) adminSettings.value = await r.json()
}

onMounted(() => Promise.all([loadUsers(), loadStatus(), loadSettings()]))

async function toggleUser(user) {
  await api.patch(`/users/${user.id}`, { is_active: !user.is_active })
  await loadUsers()
}

async function deleteUser(user) {
  if (!confirm(t('admin.confirmDelete'))) return
  await api.delete(`/users/${user.id}`)
  await loadUsers()
}

async function saveSettings() {
  const r = await api.patch('/admin/settings', {
    allow_registration: adminSettings.value.allow_registration,
    default_language: adminSettings.value.default_language,
    oidc_enabled: adminSettings.value.oidc_enabled,
    oidc_client_id: adminSettings.value.oidc_client_id,
    oidc_discovery_url: adminSettings.value.oidc_discovery_url,
    smtp_host: adminSettings.value.smtp_host,
    smtp_port: adminSettings.value.smtp_port,
    smtp_user: adminSettings.value.smtp_user,
    smtp_from: adminSettings.value.smtp_from,
  })
  if (r.ok) toast.success(t('admin.save'))
}

function formatBytes(b) {
  if (b < 1024) return `${b} B`
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`
  return `${(b / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <div class="container mx-auto py-6 space-y-4">
    <h1 class="text-2xl font-bold">{{ $t('admin.title') }}</h1>

    <Tabs default-value="users">
      <TabsList>
        <TabsTrigger value="users">{{ $t('admin.users') }}</TabsTrigger>
        <TabsTrigger value="status">{{ $t('admin.status') }}</TabsTrigger>
        <TabsTrigger value="settings">{{ $t('admin.settings') }}</TabsTrigger>
      </TabsList>

      <TabsContent value="users" class="mt-4">
        <Card>
          <CardContent class="pt-4">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>{{ $t('settings.changeName') }}</TableHead>
                  <TableHead>{{ $t('admin.role') }}</TableHead>
                  <TableHead>{{ $t('admin.statusLabel') }}</TableHead>
                  <TableHead>{{ $t('admin.actions') }}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="u in users" :key="u.id">
                  <TableCell>{{ u.id }}</TableCell>
                  <TableCell>{{ u.email }}</TableCell>
                  <TableCell>{{ u.name }}</TableCell>
                  <TableCell><Badge>{{ u.role }}</Badge></TableCell>
                  <TableCell>
                    <Badge :variant="u.is_active ? 'default' : 'destructive'">
                      {{ u.is_active ? $t('admin.active') : $t('admin.inactive') }}
                    </Badge>
                  </TableCell>
                  <TableCell class="space-x-2">
                    <Button size="sm" variant="outline" @click="toggleUser(u)">
                      {{ u.is_active ? $t('admin.banUser') : $t('admin.unbanUser') }}
                    </Button>
                    <Button size="sm" variant="destructive" @click="deleteUser(u)">
                      {{ $t('admin.deleteUser') }}
                    </Button>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="status" class="mt-4">
        <Card v-if="status">
          <CardContent class="pt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('admin.userCount') }}</p>
              <p class="text-2xl font-bold">{{ status.user_count }}</p>
            </div>
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('admin.householdCount') }}</p>
              <p class="text-2xl font-bold">{{ status.household_count }}</p>
            </div>
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('admin.transactionCount') }}</p>
              <p class="text-2xl font-bold">{{ status.transaction_count }}</p>
            </div>
            <div class="space-y-1">
              <p class="text-sm text-muted-foreground">{{ $t('admin.dbSize') }}</p>
              <p class="text-2xl font-bold">{{ formatBytes(status.db_size_bytes) }}</p>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="settings" class="mt-4">
        <Card v-if="adminSettings">
          <CardContent class="pt-4 space-y-4">
            <div class="flex items-center gap-3">
              <Switch v-model:checked="adminSettings.allow_registration" />
              <Label>{{ $t('admin.allowRegistration') }}</Label>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-1">
                <Label>{{ $t('admin.smtpHost') }}</Label>
                <Input v-model="adminSettings.smtp_host" placeholder="smtp.example.com" />
              </div>
              <div class="space-y-1">
                <Label>{{ $t('admin.smtpPort') }}</Label>
                <Input v-model="adminSettings.smtp_port" type="number" />
              </div>
              <div class="space-y-1">
                <Label>{{ $t('admin.smtpUser') }}</Label>
                <Input v-model="adminSettings.smtp_user" />
              </div>
              <div class="space-y-1">
                <Label>{{ $t('admin.smtpFrom') }}</Label>
                <Input v-model="adminSettings.smtp_from" placeholder="helledger@example.com" />
              </div>
            </div>
            <div class="flex items-center gap-3">
              <Switch v-model:checked="adminSettings.oidc_enabled" />
              <Label>{{ $t('admin.oidcEnabled') }}</Label>
            </div>
            <div v-if="adminSettings.oidc_enabled" class="space-y-2">
              <div class="space-y-1">
                <Label>{{ $t('admin.oidcClientId') }}</Label>
                <Input v-model="adminSettings.oidc_client_id" />
              </div>
              <div class="space-y-1">
                <Label>{{ $t('admin.oidcDiscoveryUrl') }}</Label>
                <Input v-model="adminSettings.oidc_discovery_url" placeholder="https://idp.example.com/.well-known/openid-configuration" />
              </div>
            </div>
            <Button @click="saveSettings">{{ $t('admin.save') }}</Button>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
</template>
