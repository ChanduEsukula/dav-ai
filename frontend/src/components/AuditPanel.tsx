import type { RecallSearchResponse } from '../api/recalls'

type Props = {
  query: string
  response: RecallSearchResponse
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

export default function AuditPanel({ query, response }: Props) {
  const retrieved = response.retrieval_timestamp ?? new Date().toISOString()
  const recordCount = response.count ?? response.results?.length ?? 0
  const scoreVersion = 'recall-risk-v0.1'
  const dataSource = 'openFDA Drug Enforcement API'
  const endpoint = '/drug/enforcement.json'
  const disclaimer =
    response.medical_disclaimer ?? 'Public-data safety intelligence only. Not medical advice.'

  return (
    <div className="audit-panel">
      <div className="metadata-grid">
        <div>
          <small>Data Source</small>
          <span>{dataSource}</span>
        </div>

        <div>
          <small>Endpoint</small>
          <span>{endpoint}</span>
        </div>

        <div>
          <small>Search Query</small>
          <span>{query}</span>
        </div>

        <div>
          <small>Retrieved At</small>
          <span>{formatTimestamp(retrieved)}</span>
        </div>

        <div>
          <small>Record Count</small>
          <span>{recordCount}</span>
        </div>

        <div>
          <small>Score Version</small>
          <span>{scoreVersion}</span>
        </div>
      </div>

      <p className="disclaimer">{disclaimer}</p>
    </div>
  )
}
