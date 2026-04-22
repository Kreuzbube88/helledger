import { ref, shallowRef } from 'vue'

const open = ref(false)
const message = ref('')
const _resolve = shallowRef(null)

export function useConfirm() {
  function confirm(msg) {
    message.value = msg
    open.value = true
    return new Promise((resolve) => {
      _resolve.value = resolve
    })
  }

  function _accept() {
    open.value = false
    _resolve.value?.(true)
  }

  function _cancel() {
    open.value = false
    _resolve.value?.(false)
  }

  return { open, message, confirm, _accept, _cancel }
}
