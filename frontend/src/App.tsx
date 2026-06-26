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
import './styles/query-typeahead.css'
import './styles/productscan.css'
import './styles/public-safety-search.css'
import './styles/source-integration-badge.css'
import './styles/source-details-disclosure.css'
import type { AssistantChatContext } from './api/assistant'
import Navbar from './components/Navbar'
import UniversalSafetySearch from './components/UniversalSafetySearch'
import PublicSafetySearchPage from './components/PublicSafetySearchPage'
import PharmacySafetyPage from './components/PharmacySafetyPage'
import FoodSafetyPage from './components/FoodSafetyPage'
import CosmeticSafetyPage from './components/CosmeticSafetyPage'
import ProductScanPage from './components/ProductScanPage'
import ProductScanTeaser from './components/ProductScanTeaser'
import Hero from './components/Hero'
import SafetyWorkspace from './components/SafetyWorkspace'
import DataSourcesPage from './components/DataSourcesPage'
import AuditHistoryPage from './components/AuditHistoryPage'
import SystemStatusPage from './components/SystemStatusPage'
import SavedMonitorsPage from './components/SavedMonitorsPage'
import FaqPage from './components/FaqPage'
import AboutPage from './components/AboutPage'
import InfoPage from './components/InfoPage'
import AskDavAIChat from './components/AskDavAIChat'
import { PAGE_IDS, isUrlPage, type ActivePage } from './types/navigation'
import { infoPages } from './data/infoPages'
import {
  getSearchComparisonKey,
  normalizeSearchTerm,
} from './utils/safetyRouteClassifier'
import { readSafetyQueryFromUrl } from './utils/safetyQueryUrl'

function getInitialPage(): ActivePage {
  const params = new URLSearchParams(window.location.search)
  const page = params.get('page')

  if (isUrlPage(page)) {
    return page
  }

  if (params.has('audit_id')) {
    return PAGE_IDS.AUDIT
  }

  return PAGE_IDS.HOME
}

function getInitialSafetyQuery() {
  return readSafetyQueryFromUrl()
}

function updatePageInUrl(page: ActivePage, safetyQuery?: string, rawSafetyQuery?: string) {
  const url = new URL(window.location.href)
  url.searchParams.delete('audit_id')

  if (page === PAGE_IDS.HOME) {
    url.searchParams.delete('page')
    url.searchParams.delete('q')
    url.searchParams.delete('raw_q')
  } else {
    url.searchParams.set('page', page)

    const normalizedQuery = normalizeSearchTerm(safetyQuery ?? '')
    const normalizedRawQuery = normalizeSearchTerm(rawSafetyQuery ?? normalizedQuery)

    if (normalizedQuery) {
      url.searchParams.set('q', normalizedQuery)
    } else {
      url.searchParams.delete('q')
    }

    if (
      normalizedRawQuery &&
      getSearchComparisonKey(normalizedRawQuery) !==
        getSearchComparisonKey(normalizedQuery)
    ) {
      url.searchParams.set('raw_q', normalizedRawQuery)
    } else {
      url.searchParams.delete('raw_q')
    }
  }

  if (url.toString() !== window.location.href) {
    window.history.pushState(null, '', url.toString())
  }
}

function App() {
  const [activePage, setActivePage] = useState<ActivePage>(() => getInitialPage())
  const [safetyQuery, setSafetyQuery] = useState(() => getInitialSafetyQuery().query)
  const [rawSafetyQuery, setRawSafetyQuery] = useState(
    () => getInitialSafetyQuery().rawQuery,
  )
  const [assistantContext, setAssistantContext] =
    useState<AssistantChatContext | null>(null)

  useEffect(() => {
    function handlePopState() {
      setActivePage(getInitialPage())
      const nextQuery = getInitialSafetyQuery()
      setSafetyQuery(nextQuery.query)
      setRawSafetyQuery(nextQuery.rawQuery)
      setAssistantContext(null)
    }

    window.addEventListener('popstate', handlePopState)

    return () => {
      window.removeEventListener('popstate', handlePopState)
    }
  }, [])

  function goHome() {
    setActivePage(PAGE_IDS.HOME)
    setSafetyQuery('')
    setRawSafetyQuery('')
    setAssistantContext(null)
    updatePageInUrl(PAGE_IDS.HOME)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function goToPharmacySafety() {
    setActivePage(PAGE_IDS.PHARMACY_SAFETY)
    setSafetyQuery('')
    setRawSafetyQuery('')
    setAssistantContext(null)
    updatePageInUrl(PAGE_IDS.PHARMACY_SAFETY)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function goToFoodSafety() {
    setActivePage(PAGE_IDS.FOOD_SAFETY)
    setSafetyQuery('')
    setRawSafetyQuery('')
    setAssistantContext(null)
    updatePageInUrl(PAGE_IDS.FOOD_SAFETY)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function goToCosmeticSafety() {
    setActivePage(PAGE_IDS.COSMETIC_SAFETY)
    setSafetyQuery('')
    setRawSafetyQuery('')
    setAssistantContext(null)
    updatePageInUrl(PAGE_IDS.COSMETIC_SAFETY)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function goToPage(page: ActivePage, safetyQuery?: string, rawQuery?: string) {
    const normalizedQuery = normalizeSearchTerm(safetyQuery ?? '')
    const normalizedRawQuery = normalizeSearchTerm(rawQuery ?? normalizedQuery)
    setActivePage(page)
    setSafetyQuery(normalizedQuery)
    setRawSafetyQuery(normalizedRawQuery)
    setAssistantContext(null)
    updatePageInUrl(page, normalizedQuery, normalizedRawQuery)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <main className="app">
      <Navbar
        activePage={activePage}
        goHome={goHome}
        goToPage={goToPage}
      />

      {activePage === PAGE_IDS.HOME && (
        <>
          <Hero
            data={null}
            goToPharmacySafety={goToPharmacySafety}
            goToFoodSafety={goToFoodSafety}
            goToCosmeticSafety={goToCosmeticSafety}
            goToAbout={() => goToPage(PAGE_IDS.ABOUT)}
          />

          <UniversalSafetySearch goToPage={goToPage} />

          <SafetyWorkspace
            goToPharmacySafety={goToPharmacySafety}
            goToFoodSafety={goToFoodSafety}
            goToCosmeticSafety={goToCosmeticSafety}
          />

          <ProductScanTeaser openProductScan={() => goToPage(PAGE_IDS.PRODUCT_SCAN)} />

        </>
      )}

      {activePage === PAGE_IDS.PUBLIC_SAFETY && (
        <PublicSafetySearchPage
          initialQuery={safetyQuery}
          initialRawQuery={rawSafetyQuery}
          setAssistantContext={setAssistantContext}
        />
      )}

      {activePage === PAGE_IDS.PHARMACY_SAFETY && (
        <PharmacySafetyPage
          initialQuery={safetyQuery}
          initialRawQuery={rawSafetyQuery}
          goToPage={goToPage}
          setAssistantContext={setAssistantContext}
        />
      )}

      {activePage === PAGE_IDS.FOOD_SAFETY && (
        <FoodSafetyPage
          initialQuery={safetyQuery}
          initialRawQuery={rawSafetyQuery}
          goToPage={goToPage}
          setAssistantContext={setAssistantContext}
        />
      )}

      {activePage === PAGE_IDS.COSMETIC_SAFETY && (
        <CosmeticSafetyPage
          initialQuery={safetyQuery}
          initialRawQuery={rawSafetyQuery}
          goToPage={goToPage}
          setAssistantContext={setAssistantContext}
        />
      )}

      {activePage === PAGE_IDS.PRODUCT_SCAN && <ProductScanPage goToPage={goToPage} />}

      {activePage === PAGE_IDS.SOURCES && <DataSourcesPage />}

      {activePage === PAGE_IDS.AUDIT && <AuditHistoryPage />}

      {activePage === PAGE_IDS.SYSTEM && <SystemStatusPage />}

      {activePage === PAGE_IDS.SAVED_MONITORS && <SavedMonitorsPage />}


      {activePage === PAGE_IDS.ABOUT && <AboutPage />}

      {activePage === PAGE_IDS.FAQ && <FaqPage />}

      {activePage === PAGE_IDS.HELP && (
        <InfoPage {...infoPages.help} showHelpDocsSearch />
      )}

      {assistantContext && <AskDavAIChat context={assistantContext} />}
    </main>
  )
}

export default App
