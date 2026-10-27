import { useEffect, useRef, useState } from 'react'
import ExperienceSelector from './ExperienceSelector'
import type { ExperienceMode } from './experienceState'

const links = [['/home', 'Home'], ['/', 'Evidence Explorer'], ['/ask', 'Ask Dav AI'],
  ['/overview', 'Operational Overview'], ['/faq', 'FAQ'], ['/about', 'About']]

export default function GlassNavigation({ route, mode, onChange }: {
  route: string; mode: ExperienceMode; onChange: (value: ExperienceMode) => void
}) {
  const [open, setOpen] = useState(false)
  const header = useRef<HTMLElement>(null)
  useEffect(() => {
    if (!header.current) return
    const update = () => {
      const node = header.current
      if (!node) return
      const inset = parseFloat(getComputedStyle(node).top) || 0
      document.documentElement.style.setProperty('--navigation-clearance', `${Math.ceil(node.getBoundingClientRect().height + inset + 20)}px`)
    }
    update()
    const keepFocusVisible = (event: FocusEvent) => {
      const target = event.target
      if (!(target instanceof HTMLElement) || !target.closest('main')) return
      requestAnimationFrame(() => {
        const box = target.getBoundingClientRect()
        const bottom = header.current?.getBoundingClientRect().bottom ?? 0
        if (box.top >= 0 && box.top < bottom + 16) window.scrollBy({ top: box.top - bottom - 20, behavior: 'instant' })
      })
    }
    document.addEventListener('focusin', keepFocusVisible)
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(update)
    observer?.observe(header.current)
    return () => { observer?.disconnect(); document.removeEventListener('focusin', keepFocusVisible); document.documentElement.style.removeProperty('--navigation-clearance') }
  }, [])
  return <header ref={header} className="app-nav-bar workspace-nav" onKeyDown={event => {
    if (event.key === 'Escape' && open) {
      setOpen(false)
      event.currentTarget.querySelector<HTMLButtonElement>('.site-menu-toggle')?.focus()
    }
  }}>
    <div className="app-brand-group"><a className="app-brand-link" href="/home" aria-label="Dav AI home"><span className="brand-emblem" aria-hidden="true"><svg viewBox="0 0 40 40" fill="none"><circle cx="20" cy="20" r="11" /><ellipse cx="20" cy="20" rx="17" ry="7" transform="rotate(-38 20 20)" /><circle className="brand-core" cx="20" cy="20" r="3" /><circle className="brand-satellite" cx="32" cy="10" r="2" /></svg></span><span>Dav AI</span></a></div>
    <ExperienceSelector mode={mode} onChange={onChange} />
    <button type="button" className="site-menu-toggle" aria-expanded={open} aria-controls="site-navigation" onClick={() => setOpen(value => !value)}>Menu <span aria-hidden="true">{open ? '−' : '+'}</span></button>
    <nav id="site-navigation" aria-label="Workspace navigation" className={`app-route-links${open ? ' is-open' : ''}`} onClick={event => {
      if ((event.target as HTMLElement).closest('a')) setOpen(false)
    }}>
      {links.map(([href, title]) => <a href={href} key={href} aria-current={route === href ? 'page' : undefined}>{title}</a>)}
      <a className="creator-nav-action" href="/about#contact-creator">Contact the Creator <span aria-hidden="true">↗</span></a>
    </nav>
  </header>
}
