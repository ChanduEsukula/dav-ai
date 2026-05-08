import { useEffect, useState } from 'react'

import { getSystemStatus, type SystemStatusResponse } from '../api/systemStatus'

function formatBoolean(value: boolean) {
  return value ? 'Yes' : 'No'
}

function SystemStatusPage() {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null)
  const [lastChecked, setLastChecked] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function loadStatus() {
    setLoading(true)
    setError('')

    try {
      const result = await getSystemStatus()
      setStatus(result)
      setLastChecked(new Date().toLocaleString())
    } catch {
      setError('Unable to load system status. Please check the backend deployment.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadStatus()
  }, [])

  return (
    <section className="system-status-page">
      <div className="page-hero">
        <p className="eyebrow">Operations</p>
        <h1>System Status</h1>
        <p>
          A quick operational snapshot of the MedTrek AI backend, audit persistence,
          and registered public-data sources.
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
            </div>
          </>
        )}
      </div>
    </section>
  )
}

export default SystemStatusPage
