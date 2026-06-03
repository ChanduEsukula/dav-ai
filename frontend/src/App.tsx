import { useEffect, useState } from 'react'
import './App.css'
import './styles/animations.css'
import './styles/navbar.css'
import './styles/hero.css'
import './styles/recallradar.css'
import './styles/safe-insight-cards.css'
import './styles/drugsignal.css'
import './styles/foodradar.css'
import './styles/datasources.css'
import './styles/signals.css'
import './styles/pages.css'
import './styles/about.css'
import './styles/faq.css'
import './styles/briefing.css'
import './styles/audit-history.css'
import './styles/operational-overview.css'
import './styles/safety-workspace.css'
import './styles/ask-dav-ai.css'
import {
  buildRecallAssistantContext,
  type AssistantChatContext,
} from './api/assistant'
import { searchRecalls, type RecallSearchResponse } from './api/recalls'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import SafetyWorkspace from './components/SafetyWorkspace'
import OperationalOverview from './components/OperationalOverview'
import Signals from './components/Signals'
import RecallRadar from './components/RecallRadar'
import DrugSignal from './components/DrugSignal'
import FoodRadar from './components/FoodRadar'
import DataSourcesPage from './components/DataSourcesPage'
import AuditHistoryPage from './components/AuditHistoryPage'
import SystemStatusPage from './components/SystemStatusPage'
import SavedMonitorsPage from './components/SavedMonitorsPage'
import RegionalHealthPulse from './components/RegionalHealthPulse'
import FaqPage from './components/FaqPage'
import AboutPage from './components/AboutPage'
import InfoPage from './components/InfoPage'
import AskDavAIChat from './components/AskDavAIChat'
import FloatingSafetyReportIntake from './components/FloatingSafetyReportIntake'
import type { ActivePage, ActiveSection } from './types/navigation'
import { infoPages } from './data/infoPages'

function getInitialPage(): ActivePage {
  const params = new URLSearchParams(window.location.search)
  const page = params.get('page')

  if (
    page === 'sources' ||
    page === 'audit' ||
    page === 'system' ||
    page === 'saved-monitors' ||
    page === 'regional-health' ||
    page === 'about' ||
    page === 'faq' ||
    page === 'help'
  ) {
    return page
  }

  if (params.has('audit_id')) {
    return 'audit'
  }

  return 'home'
}

function updatePageInUrl(page: ActivePage) {
  const url = new URL(window.location.href)

  if (page === 'home') {
    url.searchParams.delete('page')
    url.searchParams.delete('audit_id')
  } else {
    url.searchParams.set('page', page)
  }

  window.history.replaceState(null, '', url.toString())
}

function App() {
  const [activePage, setActivePage] = useState<ActivePage>(() => getInitialPage())
  const [activeSection, setActiveSection] = useState<ActiveSection>('home')
  const [query, setQuery] = useState('')
  const [data, setData] = useState<RecallSearchResponse | null>(null)
  const [assistantContext, setAssistantContext] = useState<AssistantChatContext | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    function handlePopState() {
      setActivePage(getInitialPage())
      setActiveSection('home')
    }

    window.addEventListener('popstate', handlePopState)

    return () => {
      window.removeEventListener('popstate', handlePopState)
    }
  }, [])

  async function handleSearch() {
    if (!query.trim() || loading) return

    setLoading(true)
    setError('')

    try {
      const result = await searchRecalls(query.trim(), 5)
      setData(result)
      setAssistantContext(buildRecallAssistantContext(result))
    } catch {
      setError('Unable to load recall data. Make sure the FastAPI backend is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  function goHome() {
    setActivePage('home')
    setActiveSection('home')
    updatePageInUrl('home')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function goToRecallRadar() {
    setActivePage('home')
    setActiveSection('recallradar')
    updatePageInUrl('home')

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
    updatePageInUrl('home')

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
    updatePageInUrl(page)
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
            goToDrugSignal={goToDrugSignal}
            goToHealthPulse={() => goToPage('regional-health')}
            goToAbout={() => goToPage('about')}
          />

          <SafetyWorkspace
            goToRecallRadar={goToRecallRadar}
            goToDrugSignal={goToDrugSignal}
            goToHealthPulse={() => goToPage('regional-health')}
          />

          <OperationalOverview />

          <RecallRadar
            query={query}
            setQuery={setQuery}
            data={data}
            loading={loading}
            error={error}
            handleSearch={handleSearch}
          />

          <DrugSignal onAssistantContextChange={setAssistantContext} />

          <FoodRadar />

          <Signals />
        </>
      )}

      {activePage === 'sources' && <DataSourcesPage />}

      {activePage === 'audit' && <AuditHistoryPage />}

      {activePage === 'system' && <SystemStatusPage />}

      {activePage === 'saved-monitors' && <SavedMonitorsPage />}

      {activePage === 'regional-health' && <RegionalHealthPulse />}

      {activePage === 'about' && <AboutPage />}

      {activePage === 'faq' && <FaqPage />}

      {activePage === 'help' && <InfoPage {...infoPages.help} />}

      <AskDavAIChat context={assistantContext} />
      <FloatingSafetyReportIntake />
    </main>
  )
}

export default App
