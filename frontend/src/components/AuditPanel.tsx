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
  const retrieved = response.retrieval_timestamp
  const recordCount = response.count ?? response.results?.length ?? 0
  const scoreVersion = response.score_version ?? 'Not available'
  const dataSource = response.source_name ?? 'Not available'
  const endpoint = response.endpoint ?? 'Not available'
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

        <div>
          <small>Audit ID</small>
          <span>{response.audit.audit_id}</span>
        </div>

        <div>
          <small>Source ID</small>
          <span>{response.audit.source_id}</span>
        </div>

        <div>
          <small>Module</small>
          <span>{response.audit.module}</span>
        </div>

        <div>
          <small>Upstream Status</small>
          <span>{response.audit.upstream_status}</span>
        </div>

        <div>
          <small>Transform Version</small>
          <span>{response.audit.transform_version}</span>
        </div>
      </div>

      <p className="disclaimer">{disclaimer}</p>
    </div>
  )
}