import { useState } from 'react'
import './App.css'
import './styles/animations.css'
import './styles/navbar.css'
import './styles/hero.css'
import './styles/recallradar.css'
import './styles/signals.css'
import './styles/pages.css'
import './styles/about.css'
import './styles/faq.css'
import { searchRecalls, type RecallSearchResponse } from './api/recalls'
import { formatDate, formatTimestamp, riskExplanation } from './utils/recallFormatters'
import AuditPanel from './components/AuditPanel'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import { signals } from './data/signals'
import { faqs } from './data/faqs'

type ActivePage = 'home' | 'about' | 'faq' | 'help' | 'profile' | 'signup'
type ActiveSection = 'home' | 'recallradar'

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
        goToPage={goToPage}
      />

      {activePage === 'home' && (
        <>
          <Hero
            data={data}
            goToRecallRadar={goToRecallRadar}
            goToAbout={() => goToPage('about')}
          />

          <section className="recallradar reveal" id="recallradar">
            <div className="section-heading">
              <p className="eyebrow">RecallRadar live module</p>
              <h2>Search public FDA recall signals.</h2>
              <p>
                Enter a product, drug, brand, or category. MedSignal AI fetches live public
                recall records, scores the signal, and keeps source details visible.
              </p>
            </div>

            <div className="search-panel">
              <div className="search-box">
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                      handleSearch()
                    }
                  }}
                  placeholder="Search recalls: eye drops, insulin, metformin"
                />
                <button onClick={handleSearch} disabled={loading}>
                  {loading ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>

              {error && <p className="error-message">{error}</p>}

              {data && (
                <div className="source-strip">
                  <span>{data.count} records matched</span>
                  <span>{data.source_name}</span>
                  <span>Retrieved {formatTimestamp(data.retrieval_timestamp)}</span>
                </div>
              )}

              {data && <AuditPanel query={query} response={data} />}

              <div className="results-grid">
                {data?.results.map((result) => (
                  <article className="recall-card" key={result.recall_number}>
                    <div className="recall-card-top">
                      <span className={`risk-pill risk-${result.risk_score.label.toLowerCase()}`}>
                        {result.risk_score.label} signal
                      </span>
                      <strong>{result.risk_score.score}</strong>
                    </div>

                    <h3>{result.product_description}</h3>

                    <p className="reason">{result.reason_for_recall}</p>

                    <div className="metadata-grid">
                      <div>
                        <small>FDA class</small>
                        <span>{result.classification || 'Unknown'}</span>
                      </div>
                      <div>
                        <small>Status</small>
                        <span>{result.status || 'Unknown'}</span>
                      </div>
                      <div>
                        <small>Recall date</small>
                        <span>{formatDate(result.recall_initiation_date)}</span>
                      </div>
                      <div>
                        <small>Firm</small>
                        <span>{result.recalling_firm || 'Unknown'}</span>
                      </div>
                    </div>

                    <p className="plain-explanation">{riskExplanation(result)}</p>

                    <details>
                      <summary>Technical audit details</summary>
                      <div className="audit-box">
                        <p>Source: {result.source.name}</p>
                        <p>Retrieved: {formatTimestamp(result.source.retrieval_timestamp)}</p>
                        <p>Score version: {result.risk_score.score_version}</p>
                        <p>
                          Components: class {result.risk_score.components.classification_score},
                          status {result.risk_score.components.status_score}, recency{' '}
                          {result.risk_score.components.recency_score}, scope{' '}
                          {result.risk_score.components.scope_score}
                        </p>
                      </div>
                    </details>
                  </article>
                ))}
              </div>
            </div>
          </section>

          <section className="signals reveal">
            {signals.map((signal) => (
              <article key={signal.title}>
                <span>{signal.number}</span>
                <h2>{signal.title}</h2>
                <p>{signal.text}</p>
              </article>
            ))}
          </section>
        </>
      )}

      {activePage === 'about' && (
        <section className="about-page reveal">
          <div className="about-hero">
            <p className="eyebrow">About MedSignal AI</p>
            <h2>Healthcare safety intelligence from public FDA signals.</h2>
            <p>
              MedSignal AI is a full-stack public safety intelligence platform that turns
              fragmented recall and drug-safety data into clear, source-aware review workflows.
              The current MVP focuses on RecallRadar, a live FDA recall search experience powered
              by public openFDA enforcement data.
            </p>
          </div>

          <div className="about-grid">
            <article>
              <span>01</span>
              <h3>What the app does</h3>
              <p>
                MedSignal AI helps users search public recall records, review FDA classification,
                check recall status, understand recall timing, and inspect audit details from the
                source response.
              </p>
            </article>

            <article>
              <span>02</span>
              <h3>What the app does not do</h3>
              <p>
                It does not diagnose conditions, recommend treatment, replace clinicians, or tell
                users to start, stop, or change medication. It is an information and review tool,
                not a medical decision system.
              </p>
            </article>

            <article>
              <span>03</span>
              <h3>Data source transparency</h3>
              <p>
                The current workflow uses public openFDA recall/enforcement data. Each result keeps
                source details visible, including retrieval timestamp, source name, score version,
                and technical audit context.
              </p>
            </article>

            <article>
              <span>04</span>
              <h3>Recall Review Score</h3>
              <p>
                The score is a review-priority signal. It combines recall class, status, recency,
                scope, and confidence into a simple number so users can identify which public
                records deserve closer review.
              </p>
            </article>
          </div>

          <div className="about-section">
            <div>
              <p className="eyebrow">Product positioning</p>
              <h3>Not another health app. A source-audited safety workflow.</h3>
            </div>
            <p>
              MedSignal AI is designed for users who need to review public safety information
              without manually searching multiple government portals. The long-term vision includes
              DrugSignal for adverse-event patterns, role-based briefings, saved monitors, and
              source-audited safety dashboards.
            </p>
          </div>

          <div className="audience-grid">
            <article>
              <h4>Consumers</h4>
              <p>Search a product or drug and understand whether public recall records exist.</p>
            </article>
            <article>
              <h4>Pharmacies</h4>
              <p>Review recall signals, affected products, source details, and staff checklist items.</p>
            </article>
            <article>
              <h4>Clinics</h4>
              <p>Prepare patient-facing safety communication based on public data, not guesses.</p>
            </article>
            <article>
              <h4>Public-health teams</h4>
              <p>Track what changed, where the data came from, and why a signal matters.</p>
            </article>
          </div>

          <div className="safety-note">
            <strong>Important safety boundary:</strong>
            <span>
              MedSignal AI is not FDA approved, not medical advice, and not a replacement for FDA,
              CDC, clinician, pharmacist, or emergency guidance.
            </span>
          </div>
        </section>
      )}

      {activePage === 'faq' && (
        <section className="faq-page reveal">
          <div className="faq-hero">
            <p className="eyebrow">Frequently Asked Questions</p>
            <h2>Clear answers without crowding the page.</h2>
            <p>
              These questions explain what MedSignal AI is, what it is not, where the data comes
              from, and how to interpret recall search results safely.
            </p>
          </div>

          <div className="faq-list">
            {faqs.map((item) => (
              <details className="faq-item" key={item.question}>
                <summary>
                  <span>{item.question}</span>
                  <strong>⌄</strong>
                </summary>
                <p>{item.answer}</p>
              </details>
            ))}
          </div>
        </section>
      )}

      {activePage === 'help' && (
        <section className="trust reveal">
          <p className="eyebrow">Help</p>
          <h2>Use it as a review tool, not medical advice.</h2>
          <p>
            Search a product, drug, brand, or category. Then review the exact FDA source,
            recall class, status, date, and audit details before taking action.
          </p>
        </section>
      )}

      {activePage === 'profile' && (
        <section className="trust reveal">
          <p className="eyebrow">Profile</p>
          <h2>Saved monitors are coming next.</h2>
          <p>
            Future versions can support saved searches, role-based dashboards, and team safety
            monitors.
          </p>
        </section>
      )}

      {activePage === 'signup' && (
        <section className="trust reveal">
          <p className="eyebrow">Sign Up</p>
          <h2>Early access placeholder.</h2>
          <p>
            This MVP currently focuses on the live RecallRadar workflow. Account creation and
            alerts can be added after the core search and audit flow is stable.
          </p>
        </section>
      )}
    </main>
  )
}

export default App