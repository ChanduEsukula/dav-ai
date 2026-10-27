import { useSyncExternalStore } from 'react'

const query = '(prefers-reduced-motion: reduce)'
const read = () => window.matchMedia?.(query).matches ?? true
function subscribe(notify: () => void) {
  const media = window.matchMedia?.(query)
  media?.addEventListener('change', notify)
  return () => media?.removeEventListener('change', notify)
}

// Keep runtime changes responsive as well as honoring the initial preference.
export function useMotionPreference() {
  return useSyncExternalStore(subscribe, read, () => true)
}
