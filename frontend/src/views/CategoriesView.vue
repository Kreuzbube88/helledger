<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
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
const api = useApi()

const categories = ref([])
const showDialog = ref(false)
const editingId = ref(null)
const form = ref({ name: '', category_type: 'variable', color: '#6366f1', parent_id: null })

const TYPE_COLORS = { income: 'default', fixed: 'secondary', variable: 'outline' }

async function load() {
  const res = await api.get('/categories')
  if (res.ok) categories.value = await res.json()
}

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
  if (!confirm(t('categories.archive') + '?')) return
  const res = await api.delete(`/categories/${id}`)
  if (res.ok) { await load(); toast.success(t('categories.archive')) }
  else toast.error(t('errors.generic'))
}

onMounted(load)
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
        <div class="rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{{ t('categories.name') }}</TableHead>
                <TableHead>{{ t('categories.type') }}</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              <template v-for="cat in categories.filter(c => c.category_type === section && !c.parent_id)" :key="cat.id">
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
                  <TableCell class="text-right space-x-1">
                    <Button variant="ghost" size="sm" @click="openCreate(cat.id, cat.category_type)">
                      {{ t('categories.addSub') }}
                    </Button>
                    <Button variant="ghost" size="sm" @click="openEdit(cat)">{{ t('categories.edit') }}</Button>
                    <Button variant="ghost" size="sm" class="text-destructive hover:text-destructive" @click="archive(cat.id)">
                      {{ t('categories.archive') }}
                    </Button>
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
                  <TableCell class="text-right space-x-1">
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
  </div>
</template>
