import { type FormEvent, useState } from 'react'
import {
  searchRegionalHealth,
  type RegionalHealthSearchResponse,
} from '../api/regionalHealth'

const healthPulseRegions = [
  { value: '', label: 'Select a region' },
  { value: 'MN', label: 'Minnesota' },
  { value: 'CA', label: 'California' },
]

const healthPulseCategories = [
  { value: '', label: 'Select a category' },
  { value: 'respiratory', label: 'Respiratory' },
  { value: 'hospital pressure', label: 'Hospital pressure' },
]

function RegionalHealthPulse() {
  const [region, setRegion] = useState('MN')
  const [category, setCategory] = useState('respiratory')
  const [data, setData] = useState<RegionalHealthSearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function handleRegionChange(value: string) {
    setRegion(value)
    setData(null)
    setError('')
  }

  function handleCategoryChange(value: string) {
    setCategory(value)
    setData(null)
    setError('')
  }

  async function handleSearch(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault()

    if (loading) return

    const safeRegion = region.trim()
    const safeCategory = category.trim()

    if (!safeRegion || !safeCategory) {
      setError('Choose both a region and a public-health category before reviewing Health Pulse.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const result = await searchRegionalHealth(safeRegion, safeCategory)
      setData(result)
    } catch {
      setError('Unable to load Regional Health Pulse data. Make sure the FastAPI backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const hasNoResult = !data && !loading && !error
  const helperTextId = 'health-pulse-sample-note'
  const scopeTextId = 'health-pulse-scope-note'
  const describedBy = `${helperTextId} ${scopeTextId}`

  return (
    <section className="page-shell health-pulse-page">
      <div className="health-pulse-header">
        <p className="eyebrow">Regional Health Pulse</p>
        <h1>Review sample regional public-data signals.</h1>
        <p className="page-intro">
          Explore deterministic regional signal summaries from Dav AI&apos;s public-data scaffold.
          This view is for portfolio review and source transparency, not live surveillance or
          medical guidance.
        </p>
      </div>

      <div className="health-pulse-shell">
        <div className="health-pulse-scope-banner" id={scopeTextId}>
          <div>
            <p className="eyebrow">Scope of this view</p>
            <h2>Public-data sample review only</h2>
          </div>
          <p>
            Uses sample public regional-health records only. Not live CDC/HHS surveillance, not
            emergency guidance, not medical advice, and not a personal risk predictor.
          </p>
        </div>

        <form className="health-pulse-console" onSubmit={handleSearch}>
          <div className="health-pulse-console-header">
            <div>
              <p className="eyebrow">Signal review</p>
              <h2>Choose a region and category.</h2>
            </div>
            <p>
              Preview how Dav AI can summarize a regional public-data signal while preserving
              source freshness, audit metadata, and limitations.
            </p>
          </div>

          <div className="health-pulse-control-grid">
            <div className="health-pulse-field">
              <label htmlFor="health-region">Region</label>
              <select
                id="health-region"
                value={region}
                aria-describedby={describedBy}
                onChange={(event) => handleRegionChange(event.target.value)}
              >
                {healthPulseRegions.map((option) => (
                  <option key={option.value || 'empty-region'} value={option.value}>
                    {option.value ? `${option.label} (${option.value})` : option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="health-pulse-field">
              <label htmlFor="health-category">Category</label>
              <select
                id="health-category"
                value={category}
                aria-describedby={describedBy}
                onChange={(event) => handleCategoryChange(event.target.value)}
              >
                {healthPulseCategories.map((option) => (
                  <option key={option.value || 'empty-category'} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <button type="submit" disabled={loading}>
              {loading ? 'Reviewing signal...' : 'Review signal'}
            </button>
          </div>

          <p className="health-pulse-sample-note" id={helperTextId}>
            <strong>Supported sample reviews:</strong> MN respiratory, CA respiratory, and MN
            hospital pressure.
          </p>

          {loading && (
            <p className="health-pulse-loading-status" role="status" aria-live="polite">
              Checking the selected public-data sample...
            </p>
          )}
        </form>

        {error && (
          <p className="error-text health-pulse-error" role="alert">
            {error}
          </p>
        )}

        {hasNoResult && (
          <div className="health-pulse-empty-state">
            <p className="eyebrow">Ready to preview</p>
            <h2>Choose a supported sample to preview Health Pulse.</h2>
            <p>
              Results will show a deterministic signal summary, source freshness, audit metadata,
              and limitations for the selected regional public-data sample.
            </p>
          </div>
        )}

        {data && (
          <div className="health-pulse-results-stack" role="status" aria-live="polite">
            <article className="health-pulse-result-summary">
              <div>
                <p className="eyebrow">Signal summary</p>
                <div className="health-pulse-card-heading">
                  <h2>{data.signal.trend_label} regional signal</h2>
                  <span className="health-pulse-badge">{data.signal.review_priority}</span>
                </div>
                <p className="health-pulse-summary-line">
                  Dav AI reviewed {data.record_count} sample public-data record(s) for{' '}
                  <strong>{data.region}</strong> · <strong>{data.category}</strong>. This is a
                  deterministic awareness signal for review only, not live surveillance or medical
                  advice.
                </p>
              </div>

              <div className="health-pulse-metric-grid">
                <div>
                  <small>Review priority</small>
                  <strong>{data.signal.review_priority}</strong>
                </div>
                <div>
                  <small>Confidence</small>
                  <strong>{data.signal.confidence}</strong>
                </div>
                <div>
                  <small>Latest period</small>
                  <strong>{data.latest_period ?? 'Not available'}</strong>
                </div>
                <div>
                  <small>Latest value</small>
                  <strong>{data.latest_value ?? 'Not available'}</strong>
                </div>
                <div>
                  <small>Change</small>
                  <strong>
                    {data.signal.change_percent === null
                      ? 'Not available'
                      : `${data.signal.change_percent}%`}
                  </strong>
                </div>
              </div>
            </article>

            <div className="health-pulse-detail-grid">
              <article className="health-pulse-detail-card">
                <p className="eyebrow">Source freshness</p>
                <h2>{data.source_freshness.freshness_label}</h2>
                <p>
                  The signal comes from <strong>{data.source_name}</strong>.{' '}
                  {data.source_freshness.freshness_message}
                </p>

                <dl className="detail-list health-pulse-detail-list">
                  <div>
                    <dt>Source ID</dt>
                    <dd className="technical-value">{data.source_id}</dd>
                  </div>
                  <div>
                    <dt>Endpoint</dt>
                    <dd className="technical-value">{data.endpoint}</dd>
                  </div>
                  <div>
                    <dt>Retrieved</dt>
                    <dd>{new Date(data.retrieval_timestamp).toLocaleString()}</dd>
                  </div>
                  <div>
                    <dt>Freshness status</dt>
                    <dd>{data.source_freshness.freshness_status}</dd>
                  </div>
                  <div>
                    <dt>Update cadence</dt>
                    <dd>{data.source_freshness.source_update_cadence}</dd>
                  </div>
                  <div>
                    <dt>Signal version</dt>
                    <dd className="technical-value">{data.signal.signal_version}</dd>
                  </div>
                </dl>
              </article>

              <article className="health-pulse-detail-card">
                <p className="eyebrow">Audit trail</p>
                <div className="health-pulse-card-heading">
                  <h2>Provenance</h2>
                  <a
                    className="health-pulse-audit-link"
                    href={`/?page=audit&audit_id=${encodeURIComponent(data.audit.audit_id)}`}
                  >
                    Open in Audit History
                  </a>
                </div>
                <p>
                  Shows the source, transform version, and audit event behind this displayed signal.
                </p>

                <dl className="detail-list health-pulse-detail-list">
                  <div>
                    <dt>Audit ID</dt>
                    <dd className="technical-value">{data.audit.audit_id}</dd>
                  </div>
                  <div>
                    <dt>Module</dt>
                    <dd>{data.audit.module}</dd>
                  </div>
                  <div>
                    <dt>Upstream status</dt>
                    <dd>{data.audit.upstream_status}</dd>
                  </div>
                  <div>
                    <dt>Transform version</dt>
                    <dd className="technical-value">{data.audit.transform_version}</dd>
                  </div>
                  <div>
                    <dt>Snapshot status</dt>
                    <dd>{data.audit.source_snapshot_status ?? 'Not available'}</dd>
                  </div>
                  <div>
                    <dt>Payload hash</dt>
                    <dd className="technical-value">
                      {data.audit.source_payload_hash ?? 'Not available'}
                    </dd>
                  </div>
                </dl>
              </article>
            </div>

            <article className="health-pulse-limitations-card">
              <p className="eyebrow">Limitations</p>
              <h2>Sample public-data review only</h2>
              <p>{data.disclaimer}</p>
              <ul>
                {data.signal.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </article>
          </div>
        )}
      </div>
    </section>
  )
}

export default RegionalHealthPulse