<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useConfirm } from '@/composables/useConfirm'
import { toast } from 'vue-sonner'
import { useApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const { t } = useI18n()
const { confirm } = useConfirm()
const api = useApi()

const accounts = ref([])
const showDialog = ref(false)
const editingId = ref(null)
const form = ref({ name: '', account_type: 'checking', starting_balance: '0', currency: 'EUR' })

async function load() {
  const res = await api.get('/accounts')
  if (res.ok) accounts.value = await res.json()
}

function openCreate() {
  editingId.value = null
  form.value = { name: '', account_type: 'checking', starting_balance: '0', currency: 'EUR' }
  showDialog.value = true
}

function openEdit(acc) {
  editingId.value = acc.id
  form.value = { name: acc.name, account_type: acc.account_type, starting_balance: String(acc.starting_balance), currency: acc.currency }
  showDialog.value = true
}

async function save() {
  const body = {
    name: form.value.name,
    account_type: form.value.account_type,
    starting_balance: parseFloat(form.value.starting_balance),
    currency: form.value.currency,
  }
  const res = editingId.value
    ? await api.patch(`/accounts/${editingId.value}`, body)
    : await api.post('/accounts', body)
  if (res.ok) {
    showDialog.value = false
    await load()
    toast.success(t('accounts.save'))
  } else {
    toast.error(t('errors.generic'))
  }
}

async function archive(id) {
  if (!await confirm(t('accounts.archive') + '?')) return
  const res = await api.delete(`/accounts/${id}`)
  if (res.ok) { await load(); toast.success(t('accounts.archive')) }
  else toast.error(t('errors.generic'))
}

onMounted(load)
</script>

<template>
  <div class="min-h-dvh bg-background">
    <main class="max-w-5xl mx-auto px-4 py-6">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">{{ t('accounts.title') }}</h1>
        <Button @click="openCreate">{{ t('accounts.add') }}</Button>
      </div>

      <div class="rounded-lg border bg-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{{ t('accounts.name') }}</TableHead>
              <TableHead class="w-28">{{ t('accounts.type') }}</TableHead>
              <TableHead class="text-right w-32">{{ t('accounts.balance') }}</TableHead>
              <TableHead class="w-20">{{ t('accounts.currency') }}</TableHead>
              <TableHead class="w-24">{{ t('accounts.status') }}</TableHead>
              <TableHead class="w-40 text-right">{{ t('common.actions') }}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="acc in accounts" :key="acc.id">
              <TableCell class="font-medium">{{ acc.name }}</TableCell>
              <TableCell>{{ t(`accounts.types.${acc.account_type}`) }}</TableCell>
              <TableCell class="text-right tabular-nums"
                :class="parseFloat(acc.starting_balance) >= 0 ? 'text-emerald-500' : 'text-rose-500'">
                {{ parseFloat(acc.starting_balance).toFixed(2) }}
              </TableCell>
              <TableCell>{{ acc.currency }}</TableCell>
              <TableCell>
                <Badge :variant="!acc.archived ? 'default' : 'secondary'">
                  {{ acc.archived ? t('accounts.archived') : t('accounts.active') }}
                </Badge>
              </TableCell>
              <TableCell class="text-right space-x-1 whitespace-nowrap">
                <Button variant="ghost" size="sm" @click="openEdit(acc)">{{ t('accounts.edit') }}</Button>
                <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="archive(acc.id)">
                  {{ t('accounts.archive') }}
                </Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </main>

    <Dialog v-model:open="showDialog">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ editingId ? t('accounts.edit') : t('accounts.add') }}</DialogTitle>
        </DialogHeader>
        <form @submit.prevent="save" class="space-y-4">
          <div class="space-y-1">
            <Label>{{ t('accounts.name') }}</Label>
            <Input v-model="form.name" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('accounts.type') }}</Label>
            <Select v-model="form.account_type">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="checking">{{ t('accounts.types.checking') }}</SelectItem>
                <SelectItem value="savings">{{ t('accounts.types.savings') }}</SelectItem>
                <SelectItem value="credit_card">{{ t('accounts.types.credit_card') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-1">
            <Label>{{ t('accounts.balance') }}</Label>
            <Input v-model="form.starting_balance" type="number" step="0.01" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('accounts.currency') }}</Label>
            <Input v-model="form.currency" required maxlength="3" />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" @click="showDialog = false">{{ t('accounts.cancel') }}</Button>
            <Button type="submit">{{ t('accounts.save') }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>
