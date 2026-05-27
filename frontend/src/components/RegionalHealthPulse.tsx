import { type FormEvent, useState } from 'react'
import {
  searchRegionalHealth,
  type RegionalHealthSearchResponse,
} from '../api/regionalHealth'

function RegionalHealthPulse() {
  const [region, setRegion] = useState('MN')
  const [category, setCategory] = useState('respiratory')
  const [data, setData] = useState<RegionalHealthSearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSearch(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault()

    if (loading) return

    const safeRegion = region.trim()
    const safeCategory = category.trim()

    if (!safeRegion || !safeCategory) {
      setError('Enter both a region and a public-health category before checking Health Pulse.')
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

  return (
    <section className="page-shell health-pulse-page">
      <div className="health-pulse-hero">
        <p className="eyebrow">Regional Health Pulse</p>
        <h1>Review public-health signal scaffolds.</h1>
        <p className="page-intro">
          Health Pulse extends Dav AI toward public CDC/HHS-style regional health awareness while
          preserving source transparency, audit discipline, and responsible AI safety boundaries.
        </p>
      </div>

      <div className="info-card health-pulse-boundary-card">
        <div>
          <p className="eyebrow">Safety boundary</p>
          <h2>Public-data review only</h2>
        </div>
        <p>
          This v1 page uses the Regional Health Pulse backend scaffold. It is not live CDC/HHS
          surveillance yet, not emergency guidance, not medical advice, and not a personal
          disease-risk predictor.
        </p>
      </div>

      <form className="search-card health-pulse-search-card" onSubmit={handleSearch}>
        <div className="health-pulse-form-grid">
          <div className="health-pulse-field">
            <label htmlFor="health-region">Region</label>
            <input
              id="health-region"
              value={region}
              onChange={(event) => setRegion(event.target.value)}
              placeholder="Example: MN"
              autoComplete="off"
            />
          </div>

          <div className="health-pulse-field">
            <label htmlFor="health-category">Public-health category</label>
            <input
              id="health-category"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              placeholder="Example: respiratory or hospital pressure"
              autoComplete="off"
            />
          </div>

          <button type="submit" disabled={loading}>
            {loading ? 'Checking public signal...' : 'Check Health Pulse'}
          </button>
        </div>

        <p className="health-pulse-helper">
          Try <strong>MN respiratory</strong>, <strong>CA respiratory</strong>, or{' '}
          <strong>MN hospital pressure</strong>. Internal spaces are preserved.
        </p>
      </form>

      {error && (
        <p className="error-text health-pulse-error" role="alert">
          {error}
        </p>
      )}

      {data && (
        <div className="health-pulse-results-stack">
          <article className="result-card health-pulse-meaning-card">
            <div>
              <p className="eyebrow">What this means</p>
              <div className="health-pulse-card-heading">
                <h2>{data.signal.trend_label} public-health signal</h2>
                <span className="health-pulse-badge">{data.signal.review_priority}</span>
              </div>
              <p className="health-pulse-summary-line">
                Dav AI found {data.record_count} scaffold public-data record(s) for{' '}
                <strong>{data.region}</strong> · <strong>{data.category}</strong>. This is a
                regional awareness signal for review, not emergency guidance or medical advice.
              </p>
            </div>

            <div className="health-pulse-snapshot-grid">
              <div>
                <small>Review priority</small>
                <strong>{data.signal.review_priority}</strong>
              </div>
              <div>
                <small>Confidence</small>
                <strong>{data.signal.confidence}</strong>
              </div>
              <div>
                <small>Change</small>
                <strong>
                  {data.signal.change_percent === null
                    ? 'Not available'
                    : `${data.signal.change_percent}%`}
                </strong>
              </div>
              <div>
                <small>Latest period</small>
                <strong>{data.latest_period ?? 'Not available'}</strong>
              </div>
              <div>
                <small>Latest value</small>
                <strong>{data.latest_value ?? 'Not available'}</strong>
              </div>
            </div>
          </article>

          <div className="health-pulse-results-grid">
            <article className="result-card health-pulse-trust-card">
              <p className="eyebrow">Data trust status</p>
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

            <article className="result-card health-pulse-audit-card">
              <p className="eyebrow">Technical provenance</p>
              <div className="health-pulse-card-heading">
                <h2>Audit trail</h2>
                <a
                  className="secondary-button health-pulse-audit-link"
                  href={`/?page=audit&audit_id=${encodeURIComponent(data.audit.audit_id)}`}
                >
                  Open in Audit History
                </a>
              </div>
              <p>
                Use this when you need to prove which source, transform version, and audit event
                produced the displayed signal.
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
                  <dd className="technical-value">{data.audit.source_payload_hash ?? 'Not available'}</dd>
                </div>
              </dl>
            </article>
          </div>

          <article className="result-card full-width-card health-pulse-limitations-card">
            <p className="eyebrow">Safety boundaries</p>
            <h2>Public-data review only</h2>
            <p>{data.disclaimer}</p>
            <ul>
              {data.signal.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </article>
        </div>
      )}
    </section>
  )
}

export default RegionalHealthPulse
