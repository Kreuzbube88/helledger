import { ref, onMounted, onUnmounted } from 'vue'

export function usePullToRefresh(onRefresh, threshold = 80) {
  const isPulling = ref(false)
  const pullDistance = ref(0)
  let startY = 0
  let active = false

  function onTouchStart(e) {
    if (e.target.closest('[role="dialog"]')) return
    if (window.scrollY !== 0) return
    startY = e.touches[0].clientY
    active = true
  }

  function onTouchMove(e) {
    if (!active) return
    const dy = e.touches[0].clientY - startY
    if (dy > 0) {
      isPulling.value = true
      pullDistance.value = Math.min(dy, threshold * 1.5)
    }
  }

  function onTouchEnd() {
    if (!active) return
    if (pullDistance.value >= threshold) {
      onRefresh()
    }
    isPulling.value = false
    pullDistance.value = 0
    startY = 0
    active = false
  }

  onMounted(() => {
    document.addEventListener('touchstart', onTouchStart, { passive: true })
    document.addEventListener('touchmove', onTouchMove, { passive: true })
    document.addEventListener('touchend', onTouchEnd)
  })
  onUnmounted(() => {
    document.removeEventListener('touchstart', onTouchStart)
    document.removeEventListener('touchmove', onTouchMove)
    document.removeEventListener('touchend', onTouchEnd)
  })

  return { isPulling, pullDistance }
}
