import { useEffect, useState } from 'react'
import { getSources, type SourceRecord, type SourceRegistryResponse } from '../api/sources'
import SourceIntegrationBadge from './SourceIntegrationBadge'
import SourceDetailsDisclosure from './SourceDetailsDisclosure'

function formatTimestamp(value: string | null) {
  if (!value) {
    return 'No audit record yet'
  }

  const parsed = new Date(value)

  if (Number.isNaN(parsed.getTime())) {
    return value
  }

  return parsed.toLocaleString()
}

function formatFreshnessAge(daysSinceLastSuccess: number | null) {
  if (daysSinceLastSuccess === null) {
    return 'Unknown'
  }

  return `${daysSinceLastSuccess} day(s)`
}

function getFreshnessClass(status: SourceRecord['freshness_status']) {
  if (status === 'fresh') {
    return 'freshness-badge freshness-badge--fresh'
  }

  if (status === 'aging' || status === 'stale') {
    return 'freshness-badge freshness-badge--delayed'
  }

  if (status === 'source_error') {
    return 'freshness-badge freshness-badge--error'
  }

  return 'freshness-badge freshness-badge--unknown'
}

function DataSourcesPage() {
  const [data, setData] = useState<SourceRegistryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadSources() {
      try {
        const response = await getSources()
        setData(response)
      } catch {
        setError('Unable to load source registry. Make sure the FastAPI backend is running.')
      } finally {
        setLoading(false)
      }
    }

    loadSources()
  }, [])

  return (
    <section className="data-sources-page reveal">
      <div className="section-heading">
        <p className="eyebrow">Source transparency</p>
        <h2>Registered public data sources.</h2>
        <p>
          Dav AI keeps source metadata visible so every recall or drug-event signal can be
          traced back to a public endpoint, audit history, and current freshness status.
        </p>
      </div>

      {loading && <div className="source-status-card">Loading source registry...</div>}

      {error && <p className="error-message">{error}</p>}

      {data && (
        <div className="source-summary">
          <span>{data.count} registered sources</span>
          <span>Public-data only</span>
          <span>Audit-backed freshness</span>
        </div>
      )}

      <div className="source-card-grid">
        {data?.sources.map((source) => (
          <article className="source-card" key={source.source_id}>
            <div className="source-card-top">
              <span>{source.module}</span>
              <small>{source.source_id}</small>
            </div>

            <h3>{source.source_name}</h3>
            <SourceIntegrationBadge
              sourceId={source.source_id}
              sourceName={source.source_name}
            />
            <p>{source.description}</p>

            <div className="source-freshness-panel">
              <div className="source-freshness-header">
                <small>Freshness</small>
                <span className={getFreshnessClass(source.freshness_status)}>
                  {source.freshness_label}
                </span>
              </div>

              <p>{source.freshness_reason}</p>
              <p className="source-freshness-safety-note">
                {source.freshness_safety_note}
              </p>

              <div className="source-freshness-grid">
                <div>
                  <small>Last successful retrieval</small>
                  <span>{formatTimestamp(source.last_successful_retrieval_at)}</span>
                </div>

                <div>
                  <small>Freshness age</small>
                  <span>{formatFreshnessAge(source.freshness_days_since_last_success)}</span>
                </div>

                <div>
                  <small>Last record count</small>
                  <span>
                    {source.last_record_count === null ? 'N/A' : source.last_record_count}
                  </span>
                </div>

                {source.last_error_message && (
                  <div>
                    <small>Last error</small>
                    <span>{source.last_error_message}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="source-metadata">
              <div>
                <small>Endpoint</small>
                <span>{source.endpoint}</span>
              </div>

              <div>
                <small>Update cadence</small>
                <span>{source.update_cadence}</span>
              </div>
            </div>

            <SourceDetailsDisclosure
              sourceId={source.source_id}
              sourceName={source.source_name}
              endpoint={source.endpoint}
              updateCadence={source.update_cadence}
              recordCount={source.last_record_count}
              retrievedAt={source.last_successful_retrieval_at}
            />
          </article>
        ))}
      </div>
    </section>
  )
}

export default DataSourcesPage
