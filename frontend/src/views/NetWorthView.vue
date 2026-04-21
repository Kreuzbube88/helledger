<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const { t } = useI18n()
const api = useApi()

const snapshots = ref([])
const showDialog = ref(false)
const form = ref({ snapshot_date: '', total_assets: '', total_liabilities: '', notes: '' })

async function load() {
  const r = await api.get('/net-worth')
  if (r.ok) snapshots.value = await r.json()
}

async function save() {
  const r = await api.post('/net-worth', {
    snapshot_date: form.value.snapshot_date,
    total_assets: parseFloat(form.value.total_assets),
    total_liabilities: parseFloat(form.value.total_liabilities),
    notes: form.value.notes || null,
  })
  if (r.ok) {
    showDialog.value = false
    form.value = { snapshot_date: '', total_assets: '', total_liabilities: '', notes: '' }
    await load()
  }
}

async function deleteSnapshot(id) {
  if (!confirm(t('netWorth.confirmDelete'))) return
  await api.delete(`/net-worth/${id}`)
  await load()
}

onMounted(load)
</script>

<template>
  <div class="container mx-auto py-6 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">{{ $t('netWorth.title') }}</h1>
      <Button @click="showDialog = true">{{ $t('netWorth.newSnapshot') }}</Button>
    </div>

    <Card>
      <CardContent class="pt-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{{ $t('netWorth.date') }}</TableHead>
              <TableHead class="text-right">{{ $t('netWorth.totalAssets') }}</TableHead>
              <TableHead class="text-right">{{ $t('netWorth.totalLiabilities') }}</TableHead>
              <TableHead class="text-right">{{ $t('netWorth.netWorth') }}</TableHead>
              <TableHead>{{ $t('netWorth.notes') }}</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="s in snapshots" :key="s.id">
              <TableCell>{{ s.snapshot_date }}</TableCell>
              <TableCell class="text-right tabular-nums text-emerald-500">{{ Number(s.total_assets).toFixed(2) }}</TableCell>
              <TableCell class="text-right tabular-nums text-rose-500">{{ Number(s.total_liabilities).toFixed(2) }}</TableCell>
              <TableCell class="text-right tabular-nums font-bold" :class="Number(s.net_worth) >= 0 ? 'text-emerald-500' : 'text-rose-500'">
                {{ Number(s.net_worth).toFixed(2) }}
              </TableCell>
              <TableCell class="text-muted-foreground">{{ s.notes || '—' }}</TableCell>
              <TableCell>
                <Button size="sm" variant="destructive" @click="deleteSnapshot(s.id)">
                  {{ $t('netWorth.delete') }}
                </Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>

    <Dialog v-model:open="showDialog">
      <DialogContent>
        <DialogHeader><DialogTitle>{{ $t('netWorth.newSnapshot') }}</DialogTitle></DialogHeader>
        <div class="space-y-3 py-2">
          <div class="space-y-1">
            <Label>{{ $t('netWorth.date') }}</Label>
            <Input type="date" v-model="form.snapshot_date" />
          </div>
          <div class="space-y-1">
            <Label>{{ $t('netWorth.totalAssets') }}</Label>
            <Input type="number" v-model="form.total_assets" placeholder="50000" />
          </div>
          <div class="space-y-1">
            <Label>{{ $t('netWorth.totalLiabilities') }}</Label>
            <Input type="number" v-model="form.total_liabilities" placeholder="10000" />
          </div>
          <div class="space-y-1">
            <Label>{{ $t('netWorth.notes') }}</Label>
            <Input v-model="form.notes" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="showDialog = false">{{ $t('netWorth.cancel') }}</Button>
          <Button @click="save">{{ $t('netWorth.save') }}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
