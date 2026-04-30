import { useState } from 'react'
import './App.css'
import { searchRecalls, type RecallResult, type RecallSearchResponse } from './api/recalls'
import AuditPanel from './components/AuditPanel'

type ActivePage = 'home' | 'recallradar' | 'about' | 'help' | 'profile' | 'signup'

const signals = [
  {
    number: '01',
    title: 'Recall intelligence',
    text: 'Clean summaries from public food, drug, and device recall data.',
  },
  {
    number: '02',
    title: 'Drug safety patterns',
    text: 'Adverse-event trends explained without diagnosis or treatment claims.',
  },
  {
    number: '03',
    title: 'Weather risk context',
    text: 'AQI, heat, cold, and exposure context for sensitive populations.',
  },
]

function formatDate(value: string | null) {
  if (!value) return 'Unknown'

  if (/^\d{8}$/.test(value)) {
    const year = value.slice(0, 4)
    const month = value.slice(4, 6)
    const day = value.slice(6, 8)
    return `${month}/${day}/${year}`
  }

  return value
}

function formatTimestamp(value: string) {
  try {
    return new Intl.DateTimeFormat('en-US', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

function riskExplanation(result: RecallResult) {
  const level = result.risk_score.label
  const classification = result.classification || 'an FDA recall classification'
  const status = result.status || 'unknown status'
  const scope = result.distribution_pattern?.toLowerCase().includes('nationwide')
    ? 'nationwide distribution'
    : 'documented distribution details'

  return `${level} review priority based on ${classification}, ${status.toLowerCase()} status, ${scope}, and recall timing. Review the exact product, lot details, and FDA source before taking action.`
}

function shortenProductTitle(description: string) {
  const cleanDescription = description.trim()

  if (cleanDescription.length <= 82) {
    return cleanDescription
  }

  const commaCut = cleanDescription.slice(0, 82).lastIndexOf(',')
  const cutPoint = commaCut > 35 ? commaCut : 82

  return `${cleanDescription.slice(0, cutPoint).trim()}…`
}

function App() {
  const [query, setQuery] = useState('eye drops')
  const [data, setData] = useState<RecallSearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activePage, setActivePage] = useState<ActivePage>('home')

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

  function goToRecallRadar() {
    setActivePage('recallradar')
    setTimeout(() => document.getElementById('recallradar')?.scrollIntoView({ behavior: 'smooth' }), 80)
  }

  const topResult = data?.results?.[0]

  return (
    <main className="app">
      <nav className="nav">
        <a
          className="brand"
          href="#"
          onClick={(event) => {
            event.preventDefault()
            setActivePage('home')
            window.scrollTo({ top: 0, behavior: 'smooth' })
          }}
        >
          <span className="brand-mark">✚</span>
          <span>MedSignal AI</span>
        </a>

        <div className="nav-links">
          <button
            type="button"
            className={activePage === 'home' ? 'active' : ''}
            onClick={() => {
              setActivePage('home')
              window.scrollTo({ top: 0, behavior: 'smooth' })
            }}
          >
            Home
          </button>

          <button
            type="button"
            className={activePage === 'recallradar' ? 'active' : ''}
            onClick={goToRecallRadar}
          >
            RecallRadar
          </button>

          <button
            type="button"
            className={activePage === 'about' ? 'active' : ''}
            onClick={() => {
              setActivePage('about')
              window.scrollTo({ top: 0, behavior: 'smooth' })
            }}
          >
            About
          </button>

          <button
            type="button"
            className={activePage === 'help' ? 'active' : ''}
            onClick={() => {
              setActivePage('help')
              window.scrollTo({ top: 0, behavior: 'smooth' })
            }}
          >
            Help
          </button>

          <button
            type="button"
            className={activePage === 'profile' ? 'active' : ''}
            onClick={() => {
              setActivePage('profile')
              window.scrollTo({ top: 0, behavior: 'smooth' })
            }}
          >
            Profile
          </button>

          <button
            type="button"
            className={`signup-link ${activePage === 'signup' ? 'active' : ''}`}
            onClick={() => {
              setActivePage('signup')
              window.scrollTo({ top: 0, behavior: 'smooth' })
            }}
          >
            Sign Up
          </button>
        </div>
      </nav>

      {(activePage === 'home' || activePage === 'recallradar') && (
        <>
          {activePage === 'home' && (
            <section className="hero" id="home">
              <div className="hero-copy">
                <p className="eyebrow">Public health intelligence</p>

                <h1>
                  Public safety data.
                  <br />
                  Made clear.
                </h1>

                <p className="subtitle">
                  MedSignal AI turns public recall and drug-safety data into clear,
                  source-aware intelligence.
                </p>

                <div className="actions">
                  <button type="button" onClick={goToRecallRadar}>
                    Search RecallRadar
                  </button>

                  <button type="button" onClick={() => setActivePage('help')}>
                    How it works
                  </button>
                </div>
              </div>

              <div className="hero-visual" aria-label="Animated product preview">
                <div className="gradient-orb orb-a"></div>
                <div className="gradient-orb orb-b"></div>

                <div className="dashboard-card main-card">
                  <div className="card-header">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>

                  <div className="signal-score">
                    <div>
                      <p>{topResult ? 'Live Recall Review Score' : 'Recall Review Score'}</p>
                      <h2>{topResult ? topResult.risk_score.score : 82}</h2>
                    </div>
                    <div className="score-ring"></div>
                  </div>

                  <div className="mini-chart">
                    <i></i>
                    <i></i>
                    <i></i>
                    <i></i>
                    <i></i>
                    <i></i>
                  </div>
                </div>

                <div className="floating-card card-one">
                  <small>Recall</small>
                  <strong>{topResult ? topResult.risk_score.label : 'Pattern detected'}</strong>
                </div>

                <div className="floating-card card-two">
                  <small>Source</small>
                  <strong>{data ? `${data.count} FDA records` : 'openFDA ready'}</strong>
                </div>

                <div className="floating-card card-three">
                  <small>Audit</small>
                  <strong>{data ? 'Timestamp verified' : 'Traceable results'}</strong>
                </div>
              </div>
            </section>
          )}

          <section className="recallradar reveal" id="recallradar">
            <div className="section-heading">
              <p className="eyebrow">RecallRadar live module</p>
              <h2>Search public FDA recall records.</h2>
              <p>
                Enter a product, drug, brand, or category. MedSignal AI fetches live
                public recall records, computes a review-priority score, and keeps
                source details visible.
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
                  placeholder="Try: eye drops, insulin, metformin"
                />

                <button type="button" onClick={handleSearch} disabled={loading}>
                  {loading ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>

              {error && <p className="error-message">{error}</p>}

              {data && (
                <div className="source-strip">
                  <span>{`${data.count} FDA recall records matched "${query}"`}</span>
                  <span>{data.source_name}</span>
                  <span>Retrieved {formatTimestamp(data.retrieval_timestamp)}</span>
                </div>
              )}

              {data && <AuditPanel query={query} response={data} />}

              {data && (
                <div className="user-summary">
                  <p>{`${data.count} FDA recall records matched "${query}"`}</p>

                  {topResult && (
                    <p className="summary-score">
                      Highest Recall Review Score: {topResult.risk_score.score} / 100
                    </p>
                  )}

                  <p className="safety-note">
                    These records may refer to specific lots, packages, manufacturers, or
                    historical recalls. A matched record does not mean the entire product
                    category is currently recalled.
                  </p>
                </div>
              )}

              <div className="results-grid">
                {data?.results.map((result) => {
                  const shortTitle = shortenProductTitle(result.product_description)

                  return (
                    <article className="recall-card" key={result.recall_number}>
                      <div className="recall-card-top">
                        <span className={`risk-pill risk-${result.risk_score.label.toLowerCase()}`}>
                          {result.risk_score.label} review priority
                        </span>

                        <strong>{result.risk_score.score} / 100</strong>
                      </div>

                      <h3>{shortTitle}</h3>

                      <p className="reason">
                        <strong>Reason:</strong> {result.reason_for_recall || 'No recall reason provided.'}
                      </p>

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
                        <summary>View full FDA product description</summary>
                        <div className="audit-box">
                          <p>{result.product_description}</p>
                        </div>
                      </details>

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
                  )
                })}
              </div>
            </div>
          </section>

          {activePage === 'home' && (
            <>
              <section className="signals reveal" id="signals">
                {signals.map((signal) => (
                  <article key={signal.title}>
                    <span>{signal.number}</span>
                    <h2>{signal.title}</h2>
                    <p>{signal.text}</p>
                  </article>
                ))}
              </section>

              <section className="trust reveal" id="trust">
                <p className="eyebrow">Responsible by design</p>
                <h2>Information, not diagnosis.</h2>
                <p>
                  MedSignal AI explains public safety data. It does not tell users to
                  start, stop, or change medication.
                </p>
              </section>
            </>
          )}
        </>
      )}

      {activePage === 'about' && (
        <section className="what-does reveal" id="what-does">
          <div className="section-heading">
            <p className="eyebrow">Product</p>
            <h2>What MedSignal AI Does</h2>
            <p className="subtitle">
              MedSignal AI turns public healthcare safety data into source-backed recall
              intelligence, review-priority scores, and plain-English explanations.
            </p>
          </div>

          <div className="what-grid">
            <div className="what-card">
              <h4>Search public safety records</h4>
              <p>
                Search by product, drug, brand, or category. MedSignal AI retrieves
                matching public FDA recall/enforcement records and organizes them into
                readable results.
              </p>
            </div>

            <div className="what-card">
              <h4>Explain the recall context</h4>
              <p>
                See FDA classification, recall status, recall reason, recall date, firm
                information, matched record count, and review-priority level.
              </p>
            </div>

            <div className="what-card">
              <h4>Keep the source visible</h4>
              <p>
                Every result includes source and audit details such as the API endpoint,
                search query, retrieval timestamp, record count, and score version.
              </p>
            </div>
          </div>

          <div className="key-terms">
            <h3>Key Terms</h3>

            <div className="term-grid">
              <div className="term-card">
                <h5>FDA Recall Record</h5>
                <p>
                  A public FDA enforcement record tied to a specific product, lot, firm,
                  package, or recall event.
                </p>
              </div>

              <div className="term-card">
                <h5>Matched Records</h5>
                <p>
                  The number of FDA recall records matched this search. This does not mean
                  the entire product category is currently recalled.
                </p>
              </div>

              <div className="term-card">
                <h5>FDA Classification</h5>
                <p>
                  FDA recall seriousness category. Class I is most serious, Class II is
                  moderate, and Class III is lower risk.
                </p>
              </div>

              <div className="term-card">
                <h5>Recall Status</h5>
                <p>
                  Shows whether a recall is ongoing, completed, terminated, or otherwise
                  updated in FDA records.
                </p>
              </div>

              <div className="term-card">
                <h5>Recall Review Score</h5>
                <p>
                  MedSignal AI’s 0–100 review-priority score based on classification,
                  status, recency, distribution scope, and product sensitivity. It is not a
                  personal medical risk score.
                </p>
              </div>

              <div className="term-card">
                <h5>Source + Audit Details</h5>
                <p>
                  Technical transparency showing where the data came from, when it was
                  retrieved, what endpoint was used, and how many records were returned.
                </p>
              </div>
            </div>
          </div>

          <div className="safety-card">
            <h4>What this website does not do</h4>
            <ul>
              <li>Does not diagnose medical conditions</li>
              <li>Does not tell users to start, stop, or change medication</li>
              <li>Does not replace a doctor, pharmacist, FDA notice, or emergency guidance</li>
              <li>Does not claim that every matched product is currently unsafe or recalled</li>
            </ul>
            <p className="final-line">
              MedSignal AI provides public-data safety intelligence only. It is not medical
              advice, diagnosis, or treatment.
            </p>
          </div>
        </section>
      )}

      {activePage === 'help' && (
        <section className="help reveal" id="help">
          <div className="section-heading">
            <p className="eyebrow">Help</p>
            <h2>How to interpret recall records</h2>
            <p className="subtitle">
              Guidance for reading matched FDA recall records safely and effectively.
            </p>
          </div>

          <div className="what-grid">
            <div className="what-card">
              <h4>Read the matched records</h4>
              <p>
                Matched FDA recall records may refer to specific lots, packages,
                manufacturers, or historical enforcement events. A matched record does not
                necessarily mean the entire product category is recalled.
              </p>
            </div>

            <div className="what-card">
              <h4>Check classification and status</h4>
              <p>
                FDA Classification and recall status give context on seriousness and whether
                a recall is active, completed, or terminated.
              </p>
            </div>

            <div className="what-card">
              <h4>Verify source details</h4>
              <p>
                Use Source + Audit Details to confirm the API endpoint, retrieval timestamp,
                and record count before taking action.
              </p>
            </div>
          </div>

          <div className="key-terms">
            <h3>Safe steps</h3>

            <div className="term-grid">
              <div className="term-card">
                <h5>Confirm lot details</h5>
                <p>
                  If a match looks relevant, verify lot, package, and firm details against
                  the FDA notice or manufacturer advisory.
                </p>
              </div>

              <div className="term-card">
                <h5>Consult professionals</h5>
                <p>
                  For clinical questions, consult a clinician or pharmacist. This site does
                  not provide medical advice.
                </p>
              </div>

              <div className="term-card">
                <h5>Follow official notices</h5>
                <p>
                  Check the FDA or manufacturer websites for official recall notices and
                  guidance.
                </p>
              </div>
            </div>
          </div>
        </section>
      )}

      {activePage === 'profile' && (
        <section className="profile reveal">
          <div className="section-heading">
            <p className="eyebrow">Account</p>
            <h2>Profile</h2>
            <p className="subtitle">
              Saved monitors, role preferences, and alert settings will appear here in a
              future version.
            </p>
          </div>

          <div className="what-grid">
            <div className="what-card">
              <h4>Saved monitors</h4>
              <p>Saved monitoring queries will appear here for quick access.</p>
            </div>

            <div className="what-card">
              <h4>Role preferences</h4>
              <p>
                Set your role to tailor the interface and alerts for clinicians,
                pharmacists, researchers, or healthcare operations teams.
              </p>
            </div>

            <div className="what-card">
              <h4>Alert settings</h4>
              <p>Configure notifications, thresholds, and delivery preferences.</p>
            </div>
          </div>
        </section>
      )}

      {activePage === 'signup' && (
        <section className="signup reveal">
          <div className="section-heading">
            <p className="eyebrow">Get started</p>
            <h2>Join the MedSignal AI waitlist</h2>
            <p className="subtitle">
              Create an account in a future version to save recall monitors, export
              briefings, and manage alerts.
            </p>
          </div>

          <div className="what-grid">
            <div className="what-card">
              <h4>Coming soon</h4>
              <p>
                Account creation, saved recall monitors, exportable briefings, and alert
                preferences will be added in a future version.
              </p>
            </div>
          </div>
        </section>
      )}
    </main>
  )
}

export default App