import { useEffect, useMemo, useState } from 'react'

import { getSources, type SourceRecord, type SourceRegistryResponse } from '../api/sources'
import {
  getDataQuality,
  getSystemStatus,
  type DataQualityResponse,
  type SystemStatusResponse,
} from '../api/systemStatus'

function formatBoolean(value: boolean) {
  return value ? 'Yes' : 'No'
}

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

function getFreshnessClass(status: SourceRecord['freshness_status']) {
  if (status === 'fresh') {
    return 'freshness-badge freshness-badge--fresh'
  }

  if (status === 'delayed') {
    return 'freshness-badge freshness-badge--delayed'
  }

  if (status === 'error') {
    return 'freshness-badge freshness-badge--error'
  }

  return 'freshness-badge freshness-badge--unknown'
}

function SystemStatusPage() {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null)
  const [dataQuality, setDataQuality] = useState<DataQualityResponse | null>(null)
  const [sources, setSources] = useState<SourceRegistryResponse | null>(null)
  const [lastChecked, setLastChecked] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const freshnessCounts = useMemo(() => {
    const counts = {
      fresh: 0,
      delayed: 0,
      error: 0,
      unknown: 0,
    }

    for (const source of sources?.sources ?? []) {
      counts[source.freshness_status] += 1
    }

    return counts
  }, [sources])

  async function loadStatus() {
    setLoading(true)
    setError('')

    try {
      const [systemResult, dataQualityResult, sourcesResult] = await Promise.all([
        getSystemStatus(),
        getDataQuality(),
        getSources(),
      ])

      setStatus(systemResult)
      setDataQuality(dataQualityResult)
      setSources(sourcesResult)
      setLastChecked(new Date().toLocaleString())
    } catch {
      setError('Unable to load system status. Please check the backend deployment.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadStatus()
  }, [])

  return (
    <section className="system-status-page">
      <div className="page-hero">
        <p className="eyebrow">Operations</p>
        <h1>System Status</h1>
        <p>
          A quick operational snapshot of the MedTrek AI backend, audit persistence,
          registered public-data sources, source freshness, and recent audit data quality.
        </p>
      </div>

      <div className="source-status-card">
        {loading && <p>Checking system status...</p>}

        {error && <p className="status-error">{error}</p>}

        {!loading && !error && status && (
          <>
            <div className="source-summary">
              <span>API: {status.status}</span>
              <span>Database configured: {formatBoolean(status.database.configured)}</span>
              <span>Audit readable: {formatBoolean(status.database.audit_readable)}</span>
              <span>Sources: {status.sources.registered_count}</span>
            </div>

            {sources && (
              <div className="source-summary">
                <span>Fresh sources: {freshnessCounts.fresh}</span>
                <span>Delayed: {freshnessCounts.delayed}</span>
                <span>Error: {freshnessCounts.error}</span>
                <span>Unknown: {freshnessCounts.unknown}</span>
              </div>
            )}

            <div className="source-card-grid">
              <article className="source-card">
                <div className="source-card-top">
                  <span>{status.app}</span>
                  <small>v{status.version}</small>
                </div>

                <p>
                  This endpoint confirms whether the backend is running, whether audit
                  persistence is readable, and whether the source registry is available.
                </p>

                <div className="source-metadata">
                  <div>
                    <small>Overall status</small>
                    <span>{status.status}</span>
                  </div>

                  <div>
                    <small>Database configured</small>
                    <span>{formatBoolean(status.database.configured)}</span>
                  </div>

                  <div>
                    <small>Audit persistence readable</small>
                    <span>{formatBoolean(status.database.audit_readable)}</span>
                  </div>

                  <div>
                    <small>Source registry available</small>
                    <span>{formatBoolean(status.sources.available)}</span>
                  </div>

                  <div>
                    <small>Modules</small>
                    <span>{status.modules.join(', ')}</span>
                  </div>

                  <div>
                    <small>Last checked</small>
                    <span>{lastChecked}</span>
                  </div>
                </div>
              </article>

              {dataQuality && (
                <article className="source-card">
                  <div className="source-card-top">
                    <span>Data Quality</span>
                    <small>{dataQuality.status}</small>
                  </div>

                  <p>
                    Recent audit history is summarized to show source-call outcomes,
                    persistence readability, and the latest recorded audit event.
                  </p>

                  <div className="source-summary">
                    <span>Recent audits: {dataQuality.recent_audit_count}</span>
                    <span>Success: {dataQuality.upstream_status_counts.success}</span>
                    <span>Empty: {dataQuality.upstream_status_counts.empty}</span>
                    <span>Error: {dataQuality.upstream_status_counts.error}</span>
                  </div>

                  <div className="source-metadata">
                    <div>
                      <small>Database configured</small>
                      <span>{formatBoolean(dataQuality.database_configured)}</span>
                    </div>

                    <div>
                      <small>Audit readable</small>
                      <span>{formatBoolean(dataQuality.audit_readable)}</span>
                    </div>

                    <div>
                      <small>Source registry count</small>
                      <span>{dataQuality.source_registry_count}</span>
                    </div>

                    <div>
                      <small>Latest audit exists</small>
                      <span>{formatBoolean(dataQuality.latest_audit_event.exists)}</span>
                    </div>

                    {dataQuality.latest_audit_event.exists && (
                      <>
                        <div>
                          <small>Latest module</small>
                          <span>{dataQuality.latest_audit_event.module}</span>
                        </div>

                        <div>
                          <small>Latest query</small>
                          <span>{dataQuality.latest_audit_event.query}</span>
                        </div>

                        <div>
                          <small>Latest upstream status</small>
                          <span>{dataQuality.latest_audit_event.upstream_status}</span>
                        </div>

                        <div>
                          <small>Latest record count</small>
                          <span>{dataQuality.latest_audit_event.record_count}</span>
                        </div>

                        <div>
                          <small>Latest audit ID</small>
                          <span>{dataQuality.latest_audit_event.audit_id}</span>
                        </div>

                        <div>
                          <small>Latest created at</small>
                          <span>{dataQuality.latest_audit_event.created_at}</span>
                        </div>
                      </>
                    )}
                  </div>
                </article>
              )}

              {sources?.sources.map((source) => (
                <article className="source-card" key={source.source_id}>
                  <div className="source-card-top">
                    <span>{source.module}</span>
                    <small>{source.source_id}</small>
                  </div>

                  <h3>{source.source_name}</h3>
                  <p>{source.freshness_reason}</p>

                  <div className="source-freshness-panel">
                    <div className="source-freshness-header">
                      <small>Freshness</small>
                      <span className={getFreshnessClass(source.freshness_status)}>
                        {source.freshness_label}
                      </span>
                    </div>

                    <div className="source-freshness-grid">
                      <div>
                        <small>Last successful retrieval</small>
                        <span>{formatTimestamp(source.last_successful_retrieval_at)}</span>
                      </div>

                      <div>
                        <small>Last record count</small>
                        <span>
                          {source.last_record_count === null ? 'N/A' : source.last_record_count}
                        </span>
                      </div>

                      <div>
                        <small>Update cadence</small>
                        <span>{source.update_cadence}</span>
                      </div>

                      {source.last_error_message && (
                        <div>
                          <small>Last error</small>
                          <span>{source.last_error_message}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  )
}

export default SystemStatusPage
