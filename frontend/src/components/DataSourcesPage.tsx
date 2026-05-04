import { useEffect, useState } from 'react'
import { getSources, type SourceRegistryResponse } from '../api/sources'

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
          MedTrek AI keeps source metadata visible so every recall or drug-event signal can be
          traced back to a public endpoint and module.
        </p>
      </div>

      {loading && <div className="source-status-card">Loading source registry...</div>}

      {error && <p className="error-message">{error}</p>}

      {data && (
        <div className="source-summary">
          <span>{data.count} registered sources</span>
          <span>Public-data only</span>
          <span>Audit foundation</span>
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
            <p>{source.description}</p>

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
          </article>
        ))}
      </div>
    </section>
  )
}

export default DataSourcesPage