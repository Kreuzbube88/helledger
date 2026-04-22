<script setup>
import { useI18n } from 'vue-i18n'
import { useConfirm } from '@/composables/useConfirm'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

const { t } = useI18n()
const { open, message, _accept, _cancel } = useConfirm()
</script>

<template>
  <Dialog :open="open" @update:open="(v) => !v && _cancel()">
    <DialogContent class="max-w-sm">
      <DialogHeader>
        <DialogTitle>{{ message }}</DialogTitle>
      </DialogHeader>
      <DialogFooter>
        <Button variant="outline" @click="_cancel">{{ t('common.cancel') }}</Button>
        <Button variant="destructive" @click="_accept">{{ t('common.confirm') }}</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
