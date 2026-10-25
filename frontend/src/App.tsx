import { useState, useEffect } from 'react'
import StoredDrugCatalog from './components/StoredDrugCatalog'
import Workspace from './research/Workspace'
import ExperienceSelector from './components/ExperienceSelector'
import {
  type ExperienceMode,
  getInitialExperienceMode,
} from './components/experienceState'
import './theme.css'
import './App.css'
import HomePage from './portfolio/HomePage'
import AboutPage from './portfolio/AboutPage'
import FaqPage from './portfolio/FaqPage'
import OperationalOverview from './portfolio/OperationalOverview'
import './portfolio/portfolio.css'
import './polish.css'

export default function App() {
  const [mode, setMode] = useState<ExperienceMode>(getInitialExperienceMode)
  const ask = window.location.pathname === '/ask'
  const legacyPage = new URLSearchParams(window.location.search).get('page')
  const route = legacyPage === 'operational-overview' ? '/overview'
    : ['home', 'about', 'faq'].includes(legacyPage ?? '') ? `/${legacyPage}` : window.location.pathname
  const portfolio = ['/home', '/overview', '/about', '/faq'].includes(route)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode)
  }, [mode])

  useEffect(() => {
    const titles: Record<string, string> = { '/home': 'Pharmaceutical intelligence', '/about': 'About', '/faq': 'FAQ', '/overview': 'Operational Overview', '/ask': 'Ask Dav AI' }
    document.title = `${titles[route] ?? 'Evidence Explorer'} · Dav AI`
  }, [route])

  return (
    <div className={`app-container${portfolio ? ' portfolio' : ''}`} data-theme={portfolio ? 'everyday' : mode}>
      <a className="site-skip-link" href="#main-content">Skip to main content</a>
      <header className="app-nav-bar workspace-nav" onKeyDown={event => {
        if (event.key === 'Escape' && menuOpen) {
          setMenuOpen(false)
          event.currentTarget.querySelector<HTMLButtonElement>('.site-menu-toggle')?.focus()
        }
      }}>
        <div className="app-brand-group">
          <a className="app-brand-link" href="/home" aria-label="Dav AI home">
            Dav AI
            <span className="app-brand-subtitle">
              {portfolio ? 'Pharmaceutical intelligence' : mode === 'everyday' ? 'Medication Guide' : 'Evidence Research Pro'}
            </span>
          </a>

          <button type="button" className="site-menu-toggle" aria-expanded={menuOpen} aria-controls="site-navigation" onClick={() => setMenuOpen(value => !value)}>Menu <span aria-hidden="true">{menuOpen ? '−' : '+'}</span></button>
          <nav id="site-navigation" aria-label="Workspace navigation" className={`app-route-links${menuOpen ? ' is-open' : ''}`}>
            <a href="/home" aria-current={route === '/home' ? 'page' : undefined}>Home</a>
            <a href="/" aria-current={!ask && !portfolio ? 'page' : undefined}>
              Evidence explorer
            </a>
            <a href="/ask" aria-current={ask ? 'page' : undefined}>
              Ask Dav AI
            </a>
            <a href="/about" aria-current={route === '/about' ? 'page' : undefined}>About</a>
            <a href="/faq" aria-current={route === '/faq' ? 'page' : undefined}>FAQ</a>
          </nav>
        </div>

        {!portfolio && <ExperienceSelector mode={mode} onChange={setMode} />}
      </header>

      {route === '/home' ? <HomePage /> : route === '/about' ? <AboutPage /> : route === '/faq' ? <FaqPage />
        : route === '/overview' ? <main id="main-content" className="portfolio-overview"><div className="portfolio-page-heading page-entrance"><p className="eyebrow">Operational Overview</p><h1>Research you can follow.</h1><p>A view of the workflow and its boundaries, from identity to original source.</p></div><OperationalOverview /></main>
        : ask ? <Workspace mode={mode} /> : <StoredDrugCatalog />}
      {portfolio && <footer className="portfolio-footer"><a className="portfolio-footer-brand" href="/home">Dav AI <span>Evidence, with perspective.</span></a><nav aria-label="Supporting pages"><a href="/overview">Operational Overview</a><a href="/about">About</a><a href="/faq">FAQ</a><a href="/">Evidence Explorer</a></nav><p>A graduate AI portfolio project. Frozen source data. Not medical advice.</p></footer>}
    </div>
  )
}
