<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useConfirm } from '@/composables/useConfirm'
import { CheckCircle, Pencil, Trash2 } from 'lucide-vue-next'
import { useApi } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'

const { t } = useI18n()
const { confirm } = useConfirm()
const api = useApi()

const goals = ref([])
const accounts = ref([])
const showDialog = ref(false)
const editingId = ref(null)

const emptyForm = () => ({
  name: '',
  target_amount: '',
  target_date: '',
  account_id: '',
  color: '#10b981',
  notes: '',
})
const form = ref(emptyForm())

async function load() {
  const [gRes, aRes] = await Promise.all([
    api.get('/goals'),
    api.get('/accounts'),
  ])
  if (gRes.ok) goals.value = await gRes.json()
  if (aRes.ok) accounts.value = (await aRes.json()).filter((a) => !a.archived)
}

function openAdd() {
  editingId.value = null
  form.value = emptyForm()
  showDialog.value = true
}

function openEdit(goal) {
  editingId.value = goal.id
  form.value = {
    name: goal.name,
    target_amount: goal.target_amount,
    target_date: goal.target_date || '',
    account_id: goal.account_id ? String(goal.account_id) : '',
    color: goal.color || '#10b981',
    notes: goal.notes || '',
  }
  showDialog.value = true
}

async function save() {
  const payload = {
    name: form.value.name,
    target_amount: parseFloat(form.value.target_amount),
    target_date: form.value.target_date || null,
    account_id: form.value.account_id ? parseInt(form.value.account_id) : null,
    color: form.value.color || null,
    notes: form.value.notes || null,
  }
  let r
  if (editingId.value) {
    r = await api.patch(`/goals/${editingId.value}`, payload)
  } else {
    r = await api.post('/goals', payload)
  }
  if (r.ok) {
    showDialog.value = false
    await load()
  }
}

async function remove(id) {
  if (!await confirm(t('goals.confirmDelete'))) return
  const r = await api.delete(`/goals/${id}`)
  if (r.ok) await load()
}

function fmt(val) {
  return parseFloat(val).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €'
}

onMounted(load)
</script>

<template>
  <div class="container mx-auto py-6 space-y-5 max-w-screen-lg px-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">{{ t('goals.title') }}</h1>
      <Button @click="openAdd">{{ t('goals.add') }}</Button>
    </div>

    <p v-if="goals.length === 0" class="text-sm text-muted-foreground">
      {{ t('goals.noData') }}
    </p>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card v-for="goal in goals" :key="goal.id" class="relative overflow-hidden">
        <!-- Color accent -->
        <div
          class="absolute top-0 left-0 right-0 h-1 rounded-t-xl"
          :style="{ background: goal.color || '#10b981' }"
        />
        <CardContent class="pt-5 pb-4 space-y-3">
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center gap-2 min-w-0">
              <span class="font-semibold text-sm truncate">{{ goal.name }}</span>
              <CheckCircle
                v-if="goal.is_achieved"
                class="h-4 w-4 text-emerald-500 shrink-0"
              />
            </div>
            <div class="flex gap-1 shrink-0">
              <button
                @click="openEdit(goal)"
                class="p-1 rounded text-muted-foreground hover:text-foreground transition-colors"
              >
                <Pencil class="h-3.5 w-3.5" />
              </button>
              <button
                @click="remove(goal.id)"
                class="p-1 rounded text-muted-foreground hover:text-rose-400 transition-colors"
              >
                <Trash2 class="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          <!-- Progress bar -->
          <div>
            <div class="h-2 rounded-full bg-muted overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-700"
                :style="{
                  width: goal.progress_pct + '%',
                  background: goal.color || '#10b981',
                }"
              />
            </div>
            <div class="flex justify-between items-center mt-1.5 text-xs text-muted-foreground">
              <span class="tabular-nums">{{ fmt(goal.current_amount) }} {{ t('goals.of') }} {{ fmt(goal.target_amount) }}</span>
              <span class="font-semibold" :style="{ color: goal.color || '#10b981' }">
                {{ goal.progress_pct.toFixed(0) }}%
              </span>
            </div>
          </div>

          <div v-if="goal.target_date" class="text-xs text-muted-foreground">
            {{ t('goals.targetDate') }}: {{ new Date(goal.target_date).toLocaleDateString() }}
          </div>
          <div v-if="goal.notes" class="text-xs text-muted-foreground italic truncate">{{ goal.notes }}</div>
        </CardContent>
      </Card>
    </div>

    <!-- Dialog -->
    <Dialog v-model:open="showDialog">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{{ editingId ? t('goals.edit') : t('goals.add') }}</DialogTitle>
        </DialogHeader>

        <div class="space-y-4 py-2">
          <div class="space-y-1">
            <Label>{{ t('goals.name') }}</Label>
            <Input v-model="form.name" />
          </div>

          <div class="space-y-1">
            <Label>{{ t('goals.targetAmount') }}</Label>
            <Input v-model="form.target_amount" type="number" step="0.01" min="0" />
          </div>

          <div class="space-y-1">
            <Label>{{ t('goals.targetDate') }}</Label>
            <Input v-model="form.target_date" type="date" />
          </div>

          <div class="space-y-1">
            <Label>{{ t('goals.account') }}</Label>
            <Select v-model="form.account_id">
              <SelectTrigger>
                <SelectValue :placeholder="t('goals.noAccount')" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">{{ t('goals.noAccount') }}</SelectItem>
                <SelectItem
                  v-for="acc in accounts"
                  :key="acc.id"
                  :value="String(acc.id)"
                >{{ acc.name }}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div class="space-y-1">
            <Label>{{ t('goals.color') }}</Label>
            <Input v-model="form.color" type="color" class="h-9 px-2 py-1 cursor-pointer" />
          </div>

          <div class="space-y-1">
            <Label>{{ t('goals.notes') }}</Label>
            <Input v-model="form.notes" />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" @click="showDialog = false">{{ t('transactions.cancel') }}</Button>
          <Button @click="save" :disabled="!form.name || !form.target_amount">
            {{ t('transactions.save') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
