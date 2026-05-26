import { useState } from 'react'
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

  async function handleSearch() {
    if (!region.trim() || !category.trim() || loading) return

    setLoading(true)
    setError('')

    try {
      const result = await searchRegionalHealth(region.trim(), category.trim())
      setData(result)
    } catch {
      setError('Unable to load Regional Health Pulse data. Make sure the FastAPI backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="page-shell health-pulse-page">
      <p className="eyebrow">Regional Health Pulse</p>
      <h1>Review public-health signal scaffolds.</h1>
      <p className="page-intro">
        Health Pulse extends Dav AI toward public CDC/HHS-style regional health awareness while
        preserving source transparency, audit discipline, and responsible AI safety boundaries.
      </p>

      <div className="info-card">
        <h2>Public-data safety boundary</h2>
        <p>
          This v1 page uses the Regional Health Pulse backend scaffold. It is not live CDC/HHS
          surveillance yet, not emergency guidance, not medical advice, and not a personal
          disease-risk predictor.
        </p>
      </div>

      <div className="search-card">
        <label htmlFor="health-region">Region</label>
        <input
          id="health-region"
          value={region}
          onChange={(event) => setRegion(event.target.value)}
          placeholder="Example: MN"
        />

        <label htmlFor="health-category">Public-health category</label>
        <input
          id="health-category"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          placeholder="Example: respiratory"
        />

        <button onClick={handleSearch} disabled={loading}>
          {loading ? 'Checking public signal...' : 'Check Health Pulse'}
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}

      {data && (
        <div className="results-grid">
          <article className="result-card">
            <p className="eyebrow">Signal summary</p>
            <h2>{data.signal.trend_label}</h2>
            <p>
              {data.region} · {data.category} · {data.record_count} public-data record(s)
            </p>
            <dl className="detail-list">
              <div>
                <dt>Review priority</dt>
                <dd>{data.signal.review_priority}</dd>
              </div>
              <div>
                <dt>Confidence</dt>
                <dd>{data.signal.confidence}</dd>
              </div>
              <div>
                <dt>Change</dt>
                <dd>{data.signal.change_percent === null ? 'Not available' : `${data.signal.change_percent}%`}</dd>
              </div>
              <div>
                <dt>Latest period</dt>
                <dd>{data.latest_period ?? 'Not available'}</dd>
              </div>
              <div>
                <dt>Latest value</dt>
                <dd>{data.latest_value ?? 'Not available'}</dd>
              </div>
            </dl>
          </article>

          <article className="result-card">
            <p className="eyebrow">Source transparency</p>
            <h2>{data.source_name}</h2>
            <p>{data.endpoint}</p>
            <dl className="detail-list">
              <div>
                <dt>Source ID</dt>
                <dd>{data.source_id}</dd>
              </div>
              <div>
                <dt>Retrieved</dt>
                <dd>{new Date(data.retrieval_timestamp).toLocaleString()}</dd>
              </div>
              <div>
                <dt>Signal version</dt>
                <dd>{data.signal.signal_version}</dd>
              </div>
            </dl>
          </article>

          <article className="result-card">
            <p className="eyebrow">Source freshness</p>
            <h2>{data.source_freshness.freshness_label}</h2>
            <p>{data.source_freshness.freshness_message}</p>
            <dl className="detail-list">
              <div>
                <dt>Freshness status</dt>
                <dd>{data.source_freshness.freshness_status}</dd>
              </div>
              <div>
                <dt>Update cadence</dt>
                <dd>{data.source_freshness.source_update_cadence}</dd>
              </div>
            </dl>
          </article>

          <article className="result-card">
            <p className="eyebrow">Audit trail</p>
            <h2>Health Pulse provenance</h2>
            <a
              className="secondary-button"
              href={`/?page=audit&audit_id=${encodeURIComponent(data.audit.audit_id)}`}
            >
              Open in Audit History
            </a>

            <dl className="detail-list">
              <div>
                <dt>Audit ID</dt>
                <dd>{data.audit.audit_id}</dd>
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
                <dd>{data.audit.transform_version}</dd>
              </div>
              <div>
                <dt>Snapshot status</dt>
                <dd>{data.audit.source_snapshot_status ?? 'Not available'}</dd>
              </div>
              <div>
                <dt>Source pull ID</dt>
                <dd>{data.audit.source_pull_id ?? 'Not available'}</dd>
              </div>
              <div>
                <dt>Payload hash</dt>
                <dd>{data.audit.source_payload_hash ?? 'Not available'}</dd>
              </div>
            </dl>
          </article>

          <article className="result-card full-width-card">
            <p className="eyebrow">Limitations</p>
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
