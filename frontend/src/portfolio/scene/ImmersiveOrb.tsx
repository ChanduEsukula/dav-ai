import { Component, lazy, Suspense, useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import { motion } from 'motion/react'
import { EvidenceIcon, type EvidenceKind } from '../EvidenceIcon'
import { StaticOrb } from './StaticOrb'
import type { ExperienceMode } from '../../components/experienceState'
import { useMotionPreference } from '../useMotionPreference'

const OrbScene = lazy(() => import('./OrbScene'))

class SceneBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() { return this.state.failed ? this.props.fallback : this.props.children }
}

function supportsWebGL() {
  const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory
  if ((memory && memory < 4) || (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4)) return false
  if (!window.WebGL2RenderingContext) return false
  try {
    const context = document.createElement('canvas').getContext('webgl2', { failIfMajorPerformanceCaveat: true })
    if (!context) return false
    context.getExtension('WEBGL_lose_context')?.loseContext()
    return true
  } catch { return false }
}

export default function ImmersiveOrb({ mode = 'everyday' }: { mode?: ExperienceMode }) {
  const reduced = useMotionPreference()
  const host = useRef<HTMLDivElement>(null)
  const [enabled, setEnabled] = useState(false)
  const [active, setActive] = useState(false)
  const [ready, setReady] = useState(false)
  const [failed, setFailed] = useState(false)
  const onReady = useCallback(() => setReady(true), [])
  const onFailure = useCallback(() => setFailed(true), [])
  useEffect(() => {
    if (reduced || !host.current || !('IntersectionObserver' in window)) return
    let visible = false
    let checked = false
    const sync = () => setActive(visible && !document.hidden)
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting
      if (visible && !checked) {
        checked = true
        setEnabled(supportsWebGL())
      }
      sync()
    }, { rootMargin: '80px' })
    observer.observe(host.current)
    document.addEventListener('visibilitychange', sync)
    return () => { observer.disconnect(); document.removeEventListener('visibilitychange', sync) }
  }, [reduced])
  const live = enabled && !reduced && !failed
  return <div ref={host} className="immersive-orb" role="img"
    aria-label="Decorative glass orb with a floating capsule and symbols for labels, recalls and FAERS reporting. Not live results.">
    <div className="orb-aura" aria-hidden="true" />
    <div className={`orb-render${live && ready ? ' is-ready' : ''}`} aria-hidden="true">
      {(!live || !ready) && <StaticOrb />}
      {live && <SceneBoundary fallback={<StaticOrb />}><Suspense fallback={null}>
        <OrbScene mode={mode} active={active} onReady={onReady} onFailure={onFailure} />
      </Suspense></SceneBoundary>}
    </div>
    {(['labels', 'recalls', 'faers'] as EvidenceKind[]).map((kind, index) => <motion.div
      key={kind} className={`orb-symbol orb-symbol-${kind}`} aria-hidden="true"
      animate={live && active && !reduced ? { y: [0, -7 - index, -14 - index * 2, -7 - index, 0], x: [0, 7, 0, -7, 0], rotate: [0, 2, 0, -2, 0] } : { x: 0, y: 0, rotate: 0 }}
      transition={live && active && !reduced ? { duration: 9 + index * 2, repeat: Infinity, ease: 'easeInOut', delay: index * .7 } : { duration: 0 }}>
      <EvidenceIcon kind={kind} />
    </motion.div>)}
    <span className="orb-caption" aria-hidden="true">ONE PRODUCT. THREE EVIDENCE LENSES.</span>
  </div>
}
