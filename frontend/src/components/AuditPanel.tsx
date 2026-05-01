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

function getScoreVersion(response: RecallSearchResponse) {
  const firstResult = response.results?.[0]

  return firstResult?.risk_score.score_version ?? 'Not available'
}

function getEndpoint(response: RecallSearchResponse) {
  const firstResult = response.results?.[0]

  return firstResult?.source.endpoint ?? 'Not available'
}

export default function AuditPanel({ query, response }: Props) {
  const retrieved = response.retrieval_timestamp
  const recordCount = response.count ?? response.results?.length ?? 0
  const scoreVersion = getScoreVersion(response)
  const dataSource = response.source_name ?? 'Not available'
  const endpoint = getEndpoint(response)
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
          <span>{response.query || query}</span>
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