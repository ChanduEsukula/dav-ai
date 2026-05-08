import { useState } from 'react'
import './App.css'
import './styles/animations.css'
import './styles/navbar.css'
import './styles/hero.css'
import './styles/recallradar.css'
import './styles/drugsignal.css'
import './styles/datasources.css'
import './styles/signals.css'
import './styles/pages.css'
import './styles/about.css'
import './styles/faq.css'
import './styles/briefing.css'
import './styles/audit-history.css'
import { searchRecalls, type RecallSearchResponse } from './api/recalls'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import Signals from './components/Signals'
import RecallRadar from './components/RecallRadar'
import DrugSignal from './components/DrugSignal'
import DataSourcesPage from './components/DataSourcesPage'
import AuditHistoryPage from './components/AuditHistoryPage'
import SystemStatusPage from './components/SystemStatusPage'
import FaqPage from './components/FaqPage'
import AboutPage from './components/AboutPage'
import InfoPage from './components/InfoPage'
import type { ActivePage, ActiveSection } from './types/navigation'
import { infoPages } from './data/infoPages'


function App() {
  const [activePage, setActivePage] = useState<ActivePage>('home')
  const [activeSection, setActiveSection] = useState<ActiveSection>('home')
  const [query, setQuery] = useState('')
  const [data, setData] = useState<RecallSearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSearch() {
    if (!query.trim() || loading) return

    setLoading(true)
    setError('')

    try {
      const result = await searchRecalls(query.trim(), 5)
      setData(result)
    } catch {
      setError('Unable to load recall data. Make sure the FastAPI backend is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  function goHome() {
    setActivePage('home')
    setActiveSection('home')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function goToRecallRadar() {
    setActivePage('home')
    setActiveSection('recallradar')

    setTimeout(() => {
      document.getElementById('recallradar')?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      })
    }, 80)
  }

  function goToDrugSignal() {
    setActivePage('home')
    setActiveSection('drugsignal')

    setTimeout(() => {
      document.getElementById('drugsignal')?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      })
    }, 80)
  }

  function goToPage(page: ActivePage) {
    setActivePage(page)
    setActiveSection('home')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <main className="app">
      <Navbar
        activePage={activePage}
        activeSection={activeSection}
        goHome={goHome}
        goToRecallRadar={goToRecallRadar}
        goToDrugSignal={goToDrugSignal}
        goToPage={goToPage}
      />

      {activePage === 'home' && (
        <>
          <Hero
            data={data}
            goToRecallRadar={goToRecallRadar}
            goToAbout={() => goToPage('about')}
          />

          <RecallRadar
            query={query}
            setQuery={setQuery}
            data={data}
            loading={loading}
            error={error}
            handleSearch={handleSearch}
          />

          <DrugSignal />

          <Signals />
        </>
      )}

      {activePage === 'sources' && <DataSourcesPage />}

      {activePage === 'audit' && <AuditHistoryPage />}

      {activePage === 'system' && <SystemStatusPage />}

      {activePage === 'about' && <AboutPage />}

      {activePage === 'faq' && <FaqPage />}

      {activePage === 'help' && <InfoPage {...infoPages.help} />}

      {activePage === 'profile' && <InfoPage {...infoPages.profile} />}

      {activePage === 'signup' && <InfoPage {...infoPages.signup} />}
    </main>
  )
}

export default App