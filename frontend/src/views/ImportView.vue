<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { toast } from 'vue-sonner'
import { useRouter } from 'vue-router'
import { useApi } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const { t } = useI18n()
const router = useRouter()
const api = useApi()
const auth = useAuthStore()

const step = ref(1)
const accounts = ref([])
const flatCategories = ref([])
const selectedAccountId = ref('')
const selectedFile = ref(null)
const dragging = ref(false)
const sessionId = ref(null)
const columns = ref([])
const columnMap = ref({ date: '', amount: '', description: '' })
const categoryId = ref('')
const dateFormat = ref('YYYY-MM-DD')
const decimal = ref('dot')
const previewRows = ref([])
const result = ref(null)
const loading = ref(false)

function flattenCats(list) {
  const out = []
  function walk(items) { for (const c of items) { out.push(c); if (c.children) walk(c.children) } }
  walk(list)
  return out
}

onMounted(async () => {
  const [accRes, catRes] = await Promise.all([api.get('/accounts'), api.get('/categories')])
  if (accRes.ok) accounts.value = await accRes.json()
  if (catRes.ok) flatCategories.value = flattenCats(await catRes.json())
  if (accounts.value.length) selectedAccountId.value = String(accounts.value[0].id)
})

function onDrop(e) {
  dragging.value = false
  const f = e.dataTransfer?.files[0]
  if (f) selectedFile.value = f
}

function onFileInput(e) {
  selectedFile.value = e.target.files[0] || null
}

async function uploadFile() {
  if (!selectedFile.value || !selectedAccountId.value) return
  loading.value = true
  const fd = new FormData()
  fd.append('file', selectedFile.value)
  fd.append('account_id', selectedAccountId.value)
  const res = await api.upload('/import/upload', fd)
  loading.value = false
  if (!res.ok) { toast.error(t('import.error.parseError')); return }
  const data = await res.json()
  sessionId.value = data.session_id
  columns.value = data.columns || []
  if (columns.value.length) {
    columnMap.value.date = columns.value[0]
    columnMap.value.amount = columns.value[1] || columns.value[0]
    columnMap.value.description = columns.value[2] || columns.value[0]
  }
  step.value = 2
}

async function loadPreview() {
  loading.value = true
  const res = await api.post(`/import/${sessionId.value}/preview`, {
    column_map: columnMap.value,
    date_format: dateFormat.value,
    decimal: decimal.value,
    category_id: categoryId.value ? parseInt(categoryId.value) : null,
  })
  loading.value = false
  if (res.ok) previewRows.value = (await res.json()).rows || []
}

async function runImport() {
  loading.value = true
  const res = await api.post(`/import/${sessionId.value}/execute`, {
    column_map: columnMap.value,
    date_format: dateFormat.value,
    decimal: decimal.value,
    category_id: categoryId.value ? parseInt(categoryId.value) : null,
  })
  loading.value = false
  if (!res.ok) { toast.error(t('errors.generic')); return }
  result.value = await res.json()
  step.value = 3
}

function restart() {
  step.value = 1
  selectedFile.value = null
  sessionId.value = null
  columns.value = []
  columnMap.value = { date: '', amount: '', description: '' }
  categoryId.value = ''
  dateFormat.value = 'YYYY-MM-DD'
  decimal.value = 'dot'
  previewRows.value = []
  result.value = null
}
</script>

<template>
  <div class="min-h-dvh bg-background">
    <main class="max-w-3xl mx-auto px-4 py-6">
      <h1 class="text-2xl font-bold mb-6">{{ t('import.title') }}</h1>

      <!-- No household -->
      <div v-if="!auth.user?.active_household_id" class="text-center text-muted-foreground py-16">
        {{ t('import.noHousehold') }}
      </div>

      <template v-else>
        <!-- Stepper -->
        <div class="flex items-center gap-2 mb-8">
          <div v-for="(label, i) in [t('import.step.upload'), t('import.step.mapping'), t('import.step.result')]"
               :key="i"
               class="flex items-center gap-2">
            <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
                 :class="step >= i + 1 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'">
              {{ i + 1 }}
            </div>
            <span class="text-sm" :class="step === i + 1 ? 'font-medium' : 'text-muted-foreground'">{{ label }}</span>
            <span v-if="i < 2" class="text-muted-foreground">→</span>
          </div>
        </div>

        <!-- Step 1: Upload -->
        <Card v-if="step === 1">
          <CardHeader><CardTitle>{{ t('import.step.upload') }}</CardTitle></CardHeader>
          <CardContent class="space-y-4">
            <div class="space-y-1">
              <Label>{{ t('import.account') }}</Label>
              <Select v-model="selectedAccountId">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="acc in accounts" :key="acc.id" :value="String(acc.id)">{{ acc.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div
              class="border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors"
              :class="dragging ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'"
              @dragover.prevent="dragging = true"
              @dragleave="dragging = false"
              @drop.prevent="onDrop"
              @click="$refs.fileInput.click()"
            >
              <p class="text-sm text-muted-foreground">{{ t('import.dropzone') }}</p>
              <p v-if="selectedFile" class="text-sm font-medium text-primary mt-2">{{ selectedFile.name }}</p>
              <input ref="fileInput" type="file" accept=".csv,.ofx,.qfx" class="hidden" @change="onFileInput" />
            </div>
            <Button class="w-full" :disabled="!selectedFile || !selectedAccountId || loading" @click="uploadFile">
              {{ loading ? '...' : t('import.step.mapping') + ' →' }}
            </Button>
          </CardContent>
        </Card>

        <!-- Step 2: Mapping -->
        <Card v-if="step === 2">
          <CardHeader><CardTitle>{{ t('import.step.mapping') }}</CardTitle></CardHeader>
          <CardContent class="space-y-4">
            <div v-for="field in ['date', 'amount', 'description']" :key="field" class="space-y-1">
              <Label>{{ t(`import.field.${field}`) }}</Label>
              <Select v-model="columnMap[field]">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="col in columns" :key="col" :value="col">{{ col }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-1">
              <Label>{{ t('import.field.dateFormat') }}</Label>
              <Select v-model="dateFormat">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                  <SelectItem value="DD.MM.YYYY">DD.MM.YYYY</SelectItem>
                  <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-1">
              <Label>{{ t('import.field.decimal') }}</Label>
              <Select v-model="decimal">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="dot">{{ t('import.decimal.dot') }}</SelectItem>
                  <SelectItem value="comma">{{ t('import.decimal.comma') }}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-1">
              <Label>{{ t('import.field.category') }}</Label>
              <Select v-model="categoryId">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">—</SelectItem>
                  <SelectItem v-for="cat in flatCategories" :key="cat.id" :value="String(cat.id)">{{ cat.name }}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <!-- Preview -->
            <div v-if="previewRows.length" class="rounded-lg border overflow-hidden max-h-48 overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{{ t('transactions.date') }}</TableHead>
                    <TableHead>{{ t('transactions.description') }}</TableHead>
                    <TableHead class="text-right">{{ t('transactions.amount') }}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow v-for="(row, i) in previewRows.slice(0, 5)" :key="i">
                    <TableCell>{{ row.date }}</TableCell>
                    <TableCell>{{ row.description }}</TableCell>
                    <TableCell class="text-right">{{ row.amount }}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>

            <div class="flex gap-2">
              <Button variant="outline" @click="loadPreview" :disabled="loading">{{ t('import.btn.preview') }}</Button>
              <Button class="flex-1" @click="runImport" :disabled="loading">
                {{ loading ? '...' : t('import.btn.import') }}
              </Button>
            </div>
          </CardContent>
        </Card>

        <!-- Step 3: Result -->
        <Card v-if="step === 3 && result">
          <CardHeader><CardTitle>{{ t('import.step.result') }}</CardTitle></CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-3 gap-4 text-center">
              <div>
                <p class="text-2xl font-bold text-emerald-500">{{ result.imported }}</p>
                <p class="text-xs text-muted-foreground">{{ t('import.result.imported') }}</p>
              </div>
              <div>
                <p class="text-2xl font-bold text-amber-500">{{ result.duplicates }}</p>
                <p class="text-xs text-muted-foreground">{{ t('import.result.duplicates') }}</p>
              </div>
              <div>
                <p class="text-2xl font-bold text-rose-500">{{ result.errors }}</p>
                <p class="text-xs text-muted-foreground">{{ t('import.result.errors') }}</p>
              </div>
            </div>
            <div v-if="result.duplicates > 0" class="text-sm text-amber-600 bg-amber-50 dark:bg-amber-950 rounded-md p-3">
              {{ t('import.warn.duplicates') }}
            </div>
            <div class="flex gap-2">
              <Button variant="outline" @click="restart">{{ t('import.btn.restart') }}</Button>
              <Button @click="router.push('/transactions')">{{ t('import.btn.toTransactions') }}</Button>
            </div>
          </CardContent>
        </Card>
      </template>
    </main>
  </div>
</template>
