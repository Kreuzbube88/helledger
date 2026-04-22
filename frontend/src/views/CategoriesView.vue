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

const { t, locale } = useI18n()
const { confirm } = useConfirm()
const api = useApi()

const categories = ref([])
const accounts = ref([])
const showDialog = ref(false)
const editingId = ref(null)
const form = ref({ name: '', category_type: 'variable', color: '#6366f1', parent_id: null })

// EV history accordion state: map of category id → { open, entries }
const evState = ref({})

// Adjust-amount dialog
const showAdjustDialog = ref(false)
const adjustCatId = ref(null)
const adjustForm = ref({ amount: '', valid_from: '' })

// Set-expiry dialog
const showExpiryDialog = ref(false)
const expiryCatId = ref(null)
const expiryEvId = ref(null)
const expiryForm = ref({ valid_until: '' })

const TYPE_COLORS = { income: 'default', fixed: 'secondary', variable: 'outline' }

async function load() {
  const res = await api.get('/categories')
  if (res.ok) categories.value = await res.json()
}

async function loadAccounts() {
  const res = await api.get('/accounts')
  if (res.ok) accounts.value = await res.json()
}

// ── EV History ──────────────────────────────────────────────────────
async function toggleEvHistory(catId) {
  if (!evState.value[catId]) evState.value[catId] = { open: false, entries: [] }
  const state = evState.value[catId]
  state.open = !state.open
  if (state.open && state.entries.length === 0) {
    const res = await api.get(`/expected-values?category_id=${catId}`)
    if (res.ok) state.entries = await res.json()
  }
}

async function deleteEv(catId, evId) {
  const res = await api.delete(`/expected-values/${evId}`)
  if (res.ok) {
    evState.value[catId].entries = evState.value[catId].entries.filter(e => e.id !== evId)
    toast.success(t('transactions.delete'))
  } else {
    toast.error(t('errors.generic'))
  }
}

function fmtDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString(locale.value === 'de' ? 'de-DE' : 'en-US', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

function fmtAmount(val) {
  return parseFloat(val).toFixed(2).replace('.', ',') + ' €'
}

// ── Adjust Amount Dialog ─────────────────────────────────────────────
function openAdjustDialog(catId) {
  adjustCatId.value = catId
  adjustForm.value = { amount: '', valid_from: '' }
  showAdjustDialog.value = true
}

async function saveAdjust() {
  const res = await api.post('/expected-values', {
    category_id: adjustCatId.value,
    amount: parseFloat(adjustForm.value.amount),
    valid_from: adjustForm.value.valid_from,
  })
  if (res.ok) {
    showAdjustDialog.value = false
    // refresh EV history if open
    const state = evState.value[adjustCatId.value]
    if (state) {
      const r = await api.get(`/expected-values?category_id=${adjustCatId.value}`)
      if (r.ok) state.entries = await r.json()
    }
    toast.success(t('categories.save'))
  } else {
    toast.error(t('errors.generic'))
  }
}

// ── Set Expiry Dialog ────────────────────────────────────────────────
function openExpiryDialog(cat) {
  const state = evState.value[cat.id]
  const activeEv = state?.entries.find(e => e.valid_until === null)
  if (!activeEv) { toast.error(t('errors.generic')); return }
  expiryCatId.value = cat.id
  expiryEvId.value = activeEv.id
  expiryForm.value = { valid_until: '' }
  showExpiryDialog.value = true
}

async function saveExpiry() {
  const res = await api.patch(`/expected-values/${expiryEvId.value}`, {
    valid_until: expiryForm.value.valid_until,
  })
  if (res.ok) {
    showExpiryDialog.value = false
    const state = evState.value[expiryCatId.value]
    if (state) {
      const r = await api.get(`/expected-values?category_id=${expiryCatId.value}`)
      if (r.ok) state.entries = await r.json()
    }
    toast.success(t('categories.save'))
  } else {
    toast.error(t('errors.generic'))
  }
}

// ── Default Account ─────────────────────────────────────────────────
async function saveDefaultAccount(catId, value) {
  const account_id = value === '__none__' ? null : parseInt(value)
  const res = await api.patch(`/categories/${catId}`, { default_account_id: account_id })
  if (!res.ok) toast.error(t('errors.generic'))
}

// ── Category CRUD ────────────────────────────────────────────────────
function openCreate(parentId = null, defaultType = 'variable') {
  editingId.value = null
  form.value = { name: '', category_type: defaultType, color: '#6366f1', parent_id: parentId }
  showDialog.value = true
}

function openEdit(cat) {
  editingId.value = cat.id
  form.value = { name: cat.name, category_type: cat.category_type, color: cat.color || '#6366f1', parent_id: cat.parent_id }
  showDialog.value = true
}

async function save() {
  const body = { name: form.value.name, category_type: form.value.category_type, color: form.value.color }
  if (form.value.parent_id) body.parent_id = form.value.parent_id
  const res = editingId.value
    ? await api.patch(`/categories/${editingId.value}`, body)
    : await api.post('/categories', body)
  if (res.ok) {
    showDialog.value = false
    await load()
    toast.success(t('categories.save'))
  } else {
    toast.error(t('errors.generic'))
  }
}

async function archive(id) {
  if (!await confirm(t('categories.archive') + '?')) return
  const res = await api.delete(`/categories/${id}`)
  if (res.ok) { await load(); toast.success(t('categories.archive')) }
  else toast.error(t('errors.generic'))
}

onMounted(() => { load(); loadAccounts() })
</script>

<template>
  <div class="min-h-dvh bg-background">
    <main class="max-w-4xl mx-auto px-4 py-6">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold">{{ t('categories.title') }}</h1>
        <Button @click="openCreate(null, 'variable')">{{ t('categories.add') }}</Button>
      </div>

      <div v-for="section in ['income', 'fixed', 'variable']" :key="section" class="mb-8">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          {{ t(`categories.sections.${section}`) }}
        </h2>
        <div class="rounded-lg border bg-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{{ t('categories.name') }}</TableHead>
                <TableHead class="w-28">{{ t('categories.type') }}</TableHead>
                <TableHead class="w-48 text-right">{{ t('common.actions') }}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <template v-for="cat in categories.filter(c => c.category_type === section && !c.parent_id)" :key="cat.id">
                <!-- Parent row -->
                <TableRow>
                  <TableCell class="font-medium">
                    <div class="flex items-center gap-2">
                      <span
                        class="w-3 h-3 rounded-full shrink-0"
                        :style="{ background: cat.color || '#6366f1' }"
                      />
                      {{ cat.name }}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge :variant="TYPE_COLORS[cat.category_type]">{{ t(`categories.types.${cat.category_type}`) }}</Badge>
                  </TableCell>
                  <TableCell class="text-right space-x-1 whitespace-nowrap">
                    <Button variant="ghost" size="sm" @click="openCreate(cat.id, cat.category_type)">
                      {{ t('categories.addSub') }}
                    </Button>
                    <Button variant="ghost" size="sm" @click="openEdit(cat)">{{ t('categories.edit') }}</Button>
                    <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="archive(cat.id)">
                      {{ t('categories.archive') }}
                    </Button>
                  </TableCell>
                </TableRow>

                <!-- Fixed-only: EV controls row for parent -->
                <TableRow v-if="section === 'fixed'" class="bg-muted/20">
                  <TableCell colspan="3" class="py-2 px-4">
                    <div class="flex flex-wrap items-center gap-2">
                      <Button variant="outline" size="sm" @click="toggleEvHistory(cat.id)">
                        {{ t('categories.evHistory') }}
                      </Button>
                      <Button variant="outline" size="sm" @click="openAdjustDialog(cat.id)">
                        {{ t('categories.adjustAmount') }}
                      </Button>
                      <Button
                        variant="outline" size="sm"
                        :disabled="!evState[cat.id]?.entries?.some(e => e.valid_until === null)"
                        @click="openExpiryDialog(cat)"
                      >
                        {{ t('categories.setExpiry') }}
                      </Button>
                      <div class="flex items-center gap-1.5 ml-auto">
                        <span class="text-xs text-muted-foreground whitespace-nowrap">{{ t('categories.autoBookAccount') }}:</span>
                        <Select
                          :model-value="cat.default_account_id != null ? String(cat.default_account_id) : '__none__'"
                          @update:model-value="saveDefaultAccount(cat.id, $event)"
                        >
                          <SelectTrigger class="h-7 text-xs w-40">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="__none__">{{ t('categories.noAccount') }}</SelectItem>
                            <SelectItem v-for="acc in accounts" :key="acc.id" :value="String(acc.id)">
                              {{ acc.name }}
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <!-- EV History accordion -->
                    <div v-if="evState[cat.id]?.open" class="mt-2 border rounded-md overflow-hidden">
                      <div v-if="evState[cat.id].entries.length === 0" class="px-3 py-2 text-xs text-muted-foreground">
                        {{ t('dashboard.noData') }}
                      </div>
                      <div
                        v-for="ev in evState[cat.id].entries"
                        :key="ev.id"
                        class="flex items-center justify-between px-3 py-1.5 text-xs border-b last:border-0 bg-background"
                      >
                        <span>
                          {{ fmtDate(ev.valid_from) }} –
                          <span v-if="ev.valid_until">{{ fmtDate(ev.valid_until) }}</span>
                          <span v-else class="text-emerald-500">({{ t('categories.active') }})</span>
                          : {{ fmtAmount(ev.amount) }}
                        </span>
                        <Button variant="ghost" size="sm" class="h-5 px-1 text-destructive hover:text-destructive" @click="deleteEv(cat.id, ev.id)">
                          ×
                        </Button>
                      </div>
                    </div>
                  </TableCell>
                </TableRow>

                <!-- Children -->
                <TableRow v-for="child in (cat.children || [])" :key="child.id" class="bg-muted/30">
                  <TableCell class="pl-10">
                    <div class="flex items-center gap-2">
                      <span class="w-3 h-3 rounded-full shrink-0" :style="{ background: child.color || '#6366f1' }" />
                      {{ child.name }}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge :variant="TYPE_COLORS[child.category_type]">{{ t(`categories.types.${child.category_type}`) }}</Badge>
                  </TableCell>
                  <TableCell class="text-right space-x-1 whitespace-nowrap">
                    <Button variant="ghost" size="sm" @click="openEdit(child)">{{ t('categories.edit') }}</Button>
                    <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="archive(child.id)">
                      {{ t('categories.archive') }}
                    </Button>
                  </TableCell>
                </TableRow>
              </template>
            </TableBody>
          </Table>
        </div>
      </div>
    </main>

    <!-- Category create/edit dialog -->
    <Dialog v-model:open="showDialog">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ editingId ? t('categories.edit') : t('categories.add') }}</DialogTitle>
        </DialogHeader>
        <form @submit.prevent="save" class="space-y-4">
          <div class="space-y-1">
            <Label>{{ t('categories.name') }}</Label>
            <Input v-model="form.name" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('categories.type') }}</Label>
            <Select v-model="form.category_type" :disabled="!!form.parent_id">
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="income">{{ t('categories.types.income') }}</SelectItem>
                <SelectItem value="fixed">{{ t('categories.types.fixed') }}</SelectItem>
                <SelectItem value="variable">{{ t('categories.types.variable') }}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-1">
            <Label>{{ t('categories.color') }}</Label>
            <div class="flex gap-2 items-center">
              <input type="color" v-model="form.color" class="h-9 w-12 rounded border bg-card cursor-pointer" />
              <Input v-model="form.color" class="font-mono" />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" @click="showDialog = false">{{ t('categories.cancel') }}</Button>
            <Button type="submit">{{ t('categories.save') }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <!-- Adjust amount dialog -->
    <Dialog v-model:open="showAdjustDialog">
      <DialogContent class="max-w-sm">
        <DialogHeader>
          <DialogTitle>{{ t('categories.adjustAmount') }}</DialogTitle>
        </DialogHeader>
        <form @submit.prevent="saveAdjust" class="space-y-4">
          <div class="space-y-1">
            <Label>{{ t('categories.amount') }}</Label>
            <Input v-model="adjustForm.amount" type="number" step="0.01" min="0" required />
          </div>
          <div class="space-y-1">
            <Label>{{ t('categories.validFrom') }}</Label>
            <Input v-model="adjustForm.valid_from" type="date" required />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" @click="showAdjustDialog = false">{{ t('categories.cancel') }}</Button>
            <Button type="submit">{{ t('categories.save') }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>

    <!-- Set expiry dialog -->
    <Dialog v-model:open="showExpiryDialog">
      <DialogContent class="max-w-sm">
        <DialogHeader>
          <DialogTitle>{{ t('categories.setExpiry') }}</DialogTitle>
        </DialogHeader>
        <form @submit.prevent="saveExpiry" class="space-y-4">
          <div class="space-y-1">
            <Label>{{ t('netWorth.date') }}</Label>
            <Input v-model="expiryForm.valid_until" type="date" required />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" @click="showExpiryDialog = false">{{ t('categories.cancel') }}</Button>
            <Button type="submit">{{ t('categories.save') }}</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  </div>
</template>
