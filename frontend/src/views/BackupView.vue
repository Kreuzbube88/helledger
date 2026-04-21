<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import AppNav from '@/components/AppNav.vue'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const { t } = useI18n()
const api = useApi()

const retentionDays = ref('7')
const backups = ref([])
const triggering = ref(false)

function fmtSize(bytes) {
  const mb = bytes / (1024 * 1024)
  return mb >= 1 ? mb.toFixed(1) + ' MB' : (bytes / 1024).toFixed(0) + ' KB'
}

function fmtDate(iso) {
  return new Date(iso).toLocaleString()
}

async function loadSettings() {
  const res = await api.get('/backup/settings')
  if (res.ok) {
    const data = await res.json()
    retentionDays.value = String(data.backup_retention_days)
  }
}

async function saveSettings() {
  const res = await api.patch('/backup/settings', { backup_retention_days: parseInt(retentionDays.value) })
  if (res.ok) toast.success(t('backup.saved'))
  else toast.error(t('errors.generic'))
}

async function triggerBackup() {
  triggering.value = true
  try {
    const res = await api.post('/backup/trigger', {})
    if (res.status === 201) {
      toast.success(t('backup.triggerSuccess'))
      await loadBackups()
    } else {
      toast.error(t('errors.generic'))
    }
  } finally {
    triggering.value = false
  }
}

async function loadBackups() {
  const res = await api.get('/backup/list')
  if (res.ok) backups.value = await res.json()
}

function downloadBackup(filename) {
  const token = localStorage.getItem('helledger_token')
  const a = document.createElement('a')
  a.href = `/api/backup/${filename}/download`
  a.download = filename
  // Fetch with auth to trigger download
  fetch(a.href, { headers: { Authorization: `Bearer ${token}` } })
    .then((res) => res.blob())
    .then((blob) => {
      const url = URL.createObjectURL(blob)
      a.href = url
      a.click()
      URL.revokeObjectURL(url)
    })
    .catch(() => toast.error(t('errors.generic')))
}

async function deleteBackup(filename) {
  if (!confirm(t('backup.deleteConfirm'))) return
  const res = await api.delete(`/backup/${filename}`)
  if (res.ok) { await loadBackups(); toast.success(t('backup.delete')) }
  else toast.error(t('errors.generic'))
}

onMounted(async () => {
  await Promise.all([loadSettings(), loadBackups()])
})
</script>

<template>
  <div class="min-h-dvh bg-background">
    <AppNav />
    <main class="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <h1 class="text-2xl font-bold">{{ t('backup.title') }}</h1>

      <!-- Settings -->
      <Card>
        <CardHeader><CardTitle>{{ t('backup.settings') }}</CardTitle></CardHeader>
        <CardContent>
          <form @submit.prevent="saveSettings" class="flex gap-2 items-end">
            <div class="flex-1 space-y-1">
              <Label>{{ t('backup.retentionDays') }}</Label>
              <Input v-model="retentionDays" type="number" min="1" max="365" required />
            </div>
            <Button type="submit">{{ t('backup.save') }}</Button>
          </form>
        </CardContent>
      </Card>

      <!-- Trigger -->
      <Card>
        <CardContent class="p-6">
          <Button class="w-full" :disabled="triggering" @click="triggerBackup">
            {{ triggering ? '...' : t('backup.triggerBtn') }}
          </Button>
        </CardContent>
      </Card>

      <!-- Backup list -->
      <Card>
        <CardHeader><CardTitle>{{ t('backup.list') }}</CardTitle></CardHeader>
        <CardContent>
          <div v-if="backups.length === 0" class="text-center text-muted-foreground py-8">
            {{ t('backup.empty') }}
          </div>
          <div v-else class="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{{ t('backup.filename') }}</TableHead>
                  <TableHead>{{ t('backup.size') }}</TableHead>
                  <TableHead>{{ t('backup.createdAt') }}</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="b in backups" :key="b.filename">
                  <TableCell class="font-mono text-sm">{{ b.filename }}</TableCell>
                  <TableCell class="tabular-nums text-sm">{{ fmtSize(b.size_bytes) }}</TableCell>
                  <TableCell class="text-sm text-muted-foreground">{{ fmtDate(b.created_at) }}</TableCell>
                  <TableCell class="text-right space-x-1">
                    <Button variant="ghost" size="sm" @click="downloadBackup(b.filename)">{{ t('backup.download') }}</Button>
                    <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="deleteBackup(b.filename)">
                      {{ t('backup.delete') }}
                    </Button>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </main>
  </div>
</template>
