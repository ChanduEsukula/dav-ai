import { useState } from 'react'
import './App.css'
import { searchRecalls, type RecallResult, type RecallSearchResponse } from './api/recalls'

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

  return `${level} signal based on ${classification}, ${status.toLowerCase()} status, ${scope}, and recall timing. Review the exact product, lot details, and FDA source before taking action.`
}

function App() {
  const [query, setQuery] = useState('eye drops')
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

  const topResult = data?.results?.[0]

  return (
    <main className="app">
      <nav className="nav">
        <a className="brand" href="#">
          <span className="brand-mark">✚</span>
          <span>MedSignal AI</span>
        </a>

        <div className="nav-links">
          <a href="#demo">Demo</a>
          <a href="#recallradar">RecallRadar</a>
          <a href="#signals">Signals</a>
          <a href="#trust">Trust</a>
        </div>
      </nav>

      <section className="hero" id="demo">
        <div className="hero-copy">
          <p className="eyebrow">Public health intelligence</p>

          <h1>
            Safety signals.
            <br />
            Made simple.
          </h1>

          <p className="subtitle">
            MedSignal AI turns recall, drug-safety, and environmental risk data
            into clear, source-aware briefings.
          </p>

          <div className="actions">
            <button onClick={() => document.getElementById('recallradar')?.scrollIntoView()}>
              Explore live demo
            </button>
            <a href="#signals">View signals</a>
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
                <p>{topResult ? 'Live signal score' : 'Signal score'}</p>
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
              placeholder="Try: eye drops, insulin, metformin"
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

          {data && <p className="disclaimer">{data.medical_disclaimer}</p>}
        </div>
      </section>

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
    </main>
  )
}

export default App