import { useEffect, useState } from 'react'
import './App.css'
import './styles/animations.css'
import './styles/navbar.css'
import './styles/hero.css'
import './styles/recallradar.css'
import './styles/safe-insight-cards.css'
import './styles/drugsignal.css'
import './styles/foodradar.css'
import './styles/cosmeticsignal.css'
import './styles/datasources.css'
import './styles/signals.css'
import './styles/pages.css'
import './styles/about.css'
import './styles/faq.css'
import './styles/briefing.css'
import './styles/audit-history.css'
import './styles/operational-overview.css'
import './styles/safety-workspace.css'
import './styles/universal-safety-search.css'
import './styles/safety-area-pages.css'
import './styles/ask-dav-ai.css'
import './styles/search-glass.css'
import type { AssistantChatContext } from './api/assistant'
import Navbar from './components/Navbar'
import UniversalSafetySearch from './components/UniversalSafetySearch'
import PharmacySafetyPage from './components/PharmacySafetyPage'
import FoodSafetyPage from './components/FoodSafetyPage'
import CosmeticSafetyPage from './components/CosmeticSafetyPage'
import Hero from './components/Hero'
import SafetyWorkspace from './components/SafetyWorkspace'
import OperationalOverview from './components/OperationalOverview'
import Signals from './components/Signals'
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
import { normalizeSearchTerm } from './utils/safetyRouteClassifier'

function getInitialPage(): ActivePage {
  const params = new URLSearchParams(window.location.search)
  const page = params.get('page')

  if (
    page === 'pharmacy-safety' ||
    page === 'food-safety' ||
    page === 'cosmetic-safety' ||
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

function getInitialSafetyQuery() {
  return normalizeSearchTerm(new URLSearchParams(window.location.search).get('q') ?? '')
}

function updatePageInUrl(page: ActivePage, safetyQuery?: string) {
  const url = new URL(window.location.href)

  if (page === 'home') {
    url.searchParams.delete('page')
    url.searchParams.delete('audit_id')
    url.searchParams.delete('q')
  } else {
    url.searchParams.set('page', page)

    const normalizedQuery = normalizeSearchTerm(safetyQuery ?? '')

    if (normalizedQuery) {
      url.searchParams.set('q', normalizedQuery)
    } else {
      url.searchParams.delete('q')
    }
  }

  if (url.toString() !== window.location.href) {
    window.history.pushState(null, '', url.toString())
  }
}

function App() {
  const [activePage, setActivePage] = useState<ActivePage>(() => getInitialPage())
  const [activeSection, setActiveSection] = useState<ActiveSection>('home')
  const [safetyQuery, setSafetyQuery] = useState(() => getInitialSafetyQuery())
  const [assistantContext] = useState<AssistantChatContext | null>(null)

  useEffect(() => {
    function handlePopState() {
      setActivePage(getInitialPage())
      setSafetyQuery(getInitialSafetyQuery())
      setActiveSection('home')
    }

    window.addEventListener('popstate', handlePopState)

    return () => {
      window.removeEventListener('popstate', handlePopState)
    }
  }, [])

  function goHome() {
    setActivePage('home')
    setSafetyQuery('')
    setActiveSection('home')
    updatePageInUrl('home')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function goToRecallRadar() {
    setActivePage('pharmacy-safety')
    setSafetyQuery('')
    setActiveSection('recallradar')
    updatePageInUrl('pharmacy-safety')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function goToDrugSignal() {
    setActivePage('pharmacy-safety')
    setSafetyQuery('')
    setActiveSection('drugsignal')
    updatePageInUrl('pharmacy-safety')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function goToFoodRadar() {
    setActivePage('food-safety')
    setSafetyQuery('')
    setActiveSection('foodradar')
    updatePageInUrl('food-safety')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function goToCosmeticSignal() {
    setActivePage('cosmetic-safety')
    setSafetyQuery('')
    setActiveSection('cosmeticsignal')
    updatePageInUrl('cosmetic-safety')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function goToPage(page: ActivePage, safetyQuery?: string) {
    const normalizedQuery = normalizeSearchTerm(safetyQuery ?? '')
    setActivePage(page)
    setSafetyQuery(normalizedQuery)
    setActiveSection('home')
    updatePageInUrl(page, normalizedQuery)
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
        goToFoodRadar={goToFoodRadar}
        goToCosmeticSignal={goToCosmeticSignal}
        goToPage={goToPage}
      />

      {activePage === 'home' && (
        <>
          <Hero
            data={null}
            goToRecallRadar={goToRecallRadar}
            goToDrugSignal={goToDrugSignal}
            goToFoodRadar={goToFoodRadar}
            goToCosmeticSignal={goToCosmeticSignal}
            goToAbout={() => goToPage('about')}
          />

          <SafetyWorkspace
            goToRecallRadar={goToRecallRadar}
            goToDrugSignal={goToDrugSignal}
            goToFoodRadar={goToFoodRadar}
            goToCosmeticSignal={goToCosmeticSignal}
          />

          <UniversalSafetySearch goToPage={goToPage} />

          <OperationalOverview />

          <Signals />
        </>
      )}

      {activePage === 'pharmacy-safety' && (
        <PharmacySafetyPage initialQuery={safetyQuery} goToPage={goToPage} />
      )}

      {activePage === 'food-safety' && (
        <FoodSafetyPage
          initialQuery={safetyQuery}
          goToFoodRadar={goToFoodRadar}
          goToPage={goToPage}
        />
      )}

      {activePage === 'cosmetic-safety' && (
        <CosmeticSafetyPage
          initialQuery={safetyQuery}
          goToCosmeticSignal={goToCosmeticSignal}
          goToPage={goToPage}
        />
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
