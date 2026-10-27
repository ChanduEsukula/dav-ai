import { useState, useEffect, useRef } from 'react'
import StoredDrugCatalog from './components/StoredDrugCatalog'
import Workspace from './research/Workspace'
import GlassNavigation from './components/GlassNavigation'
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
import './components/site-nav.css'
import './portfolio/immersive.css'
import './unified-glass.css'
import './dual-experience.css'
import './readability.css'

export default function App() {
  const [mode, setMode] = useState<ExperienceMode>(getInitialExperienceMode)
  const [location, setLocation] = useState(() => window.location.pathname + window.location.search)
  const address = new URL(location, window.location.origin)
  const ask = address.pathname === '/ask'
  const legacyPage = address.searchParams.get('page')
  const route = legacyPage === 'operational-overview' ? '/overview'
    : ['home', 'about', 'faq'].includes(legacyPage ?? '') ? `/${legacyPage}` : address.pathname
  const portfolio = ['/home', '/overview', '/about', '/faq'].includes(route)
  const [homeFeedback, setHomeFeedback] = useState(false)
  const feedbackTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  useEffect(() => {
    const pop = () => setLocation(window.location.pathname + window.location.search)
    window.addEventListener('popstate', pop)
    return () => { window.removeEventListener('popstate', pop); clearTimeout(feedbackTimer.current) }
  }, [])

  function navigate(url: URL) {
    window.history.pushState(null, '', url.pathname + url.search + url.hash)
    setLocation(url.pathname + url.search)
    setMode(getInitialExperienceMode())
    window.dispatchEvent(new PopStateEvent('popstate'))
    requestAnimationFrame(() => {
      if (url.hash) document.getElementById(url.hash.slice(1))?.scrollIntoView({ block: 'start' })
      else window.scrollTo({ top: 0, behavior: 'instant' })
    })
  }

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode)
  }, [mode])

  useEffect(() => {
    const titles: Record<string, string> = { '/home': 'Real FDA data. Clearer answers.', '/about': 'About', '/faq': 'FAQ', '/overview': 'Operational Overview', '/ask': 'Ask Dav AI' }
    document.title = `${titles[route] ?? 'Evidence Explorer'} · Dav AI`
  }, [route])

  return (
    <div onClick={event => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
      const anchor = (event.target as HTMLElement).closest<HTMLAnchorElement>('a[href]')
      if (!anchor || anchor.target || anchor.hasAttribute('download')) return
      const url = new URL(anchor.href)
      if (url.origin !== window.location.origin) return
      if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) return
      event.preventDefault()
      if (route === '/home' && url.pathname === '/home') {
        setHomeFeedback(true); clearTimeout(feedbackTimer.current)
        feedbackTimer.current = setTimeout(() => setHomeFeedback(false), 1600)
        return
      }
      if (ask && url.pathname === '/ask') return
      navigate(url)
    }} onSubmit={event => {
      const form = event.target as HTMLFormElement
      if (event.defaultPrevented || form.getAttribute('action') !== '/' || form.method !== 'get') return
      event.preventDefault()
      const url = new URL('/', window.location.origin)
      url.searchParams.set('q', String(new FormData(form).get('q') || '').trim())
      navigate(url)
    }} className={`app-container glass-site${homeFeedback ? ' home-feedback' : ''}${portfolio ? ' portfolio' : ''}${route === '/home' ? ' immersive-home' : ''}`} data-theme={mode}>
      <a className="site-skip-link" href="#main-content">Skip to main content</a>
      <GlassNavigation route={portfolio || ask ? route : '/'} mode={mode} onChange={setMode} />
      {homeFeedback && <span className="home-feedback-note" role="status">You’re on Home</span>}

      {route === '/home' ? <HomePage mode={mode} /> : route === '/about' ? <AboutPage /> : route === '/faq' ? <FaqPage />
        : route === '/overview' ? <main id="main-content" className="portfolio-overview"><div className="portfolio-page-heading page-entrance"><p className="eyebrow">Operational Overview</p><h1>How Dav AI Works</h1><p>From FDA source snapshots to a read-only database, bounded retrieval and cited outputs.</p></div><OperationalOverview mode={mode} /></main>
        : ask ? null : <StoredDrugCatalog mode={mode} />}
      <Workspace mode={mode} active={ask} />
      {portfolio && <footer className="portfolio-footer"><a className="portfolio-footer-brand" href="/home">Dav AI <span>Evidence, with perspective.</span></a><nav aria-label="Supporting pages"><a href="/overview">Operational Overview</a><a href="/about">About</a><a href="/faq">FAQ</a><a href="/">Evidence Explorer</a></nav><p>Frozen FDA/openFDA source data. Not FDA approved. Not medical advice.</p></footer>}
    </div>
  )
}
