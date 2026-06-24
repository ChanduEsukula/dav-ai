import {
  getSourceIntegrationMode,
  sourceIntegrationModeLabels,
  type SourceIntegrationMode,
} from '../utils/sourceIntegrationMode'

type SourceDetailsDisclosureProps = {
  sourceId?: string | null
  sourceName?: string | null
  sourceType?: string | null
  sourceKind?: string | null
  sourceUrl?: string | null
  endpoint?: string | null
  recordCount?: number | null
  upstreamStatus?: string | null
  retrievedAt?: string | null
  updateCadence?: string | null
}

const sourceModeNotes: Record<SourceIntegrationMode, string> = {
  curated_official_snapshot: 'Prototype snapshot. Live refresh is not automated yet.',
  live_public_api: 'Queried from a live public API when this search runs.',
  live_public_page: 'Read from an official public page when this search runs.',
  prototype_scaffold: 'Prototype scaffold. Live public-source ingestion is not configured yet.',
}

function formatSourceDetailValue(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === '') return 'Not listed'
  return value
}

function formatSourceTimestamp(value: string | null | undefined) {
  if (!value) return 'Not listed'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function SourceDetailsDisclosure({
  sourceId,
  sourceName,
  sourceType,
  sourceKind,
  sourceUrl,
  endpoint,
  recordCount,
  upstreamStatus,
  retrievedAt,
  updateCadence,
}: SourceDetailsDisclosureProps) {
  const mode = getSourceIntegrationMode({ sourceId, sourceName, sourceType })
  const modeLabel = mode ? sourceIntegrationModeLabels[mode] : 'Source details'
  const modeNote = mode ? sourceModeNotes[mode] : 'Public source metadata shown for auditability.'

  const officialUrl = sourceUrl || endpoint

  return (
    <details className="source-details-disclosure">
      <summary>Source details</summary>

      <div className="source-details-disclosure__body">
        <dl>
          <div>
            <dt>Source</dt>
            <dd>{formatSourceDetailValue(sourceName)}</dd>
          </div>

          <div>
            <dt>Mode</dt>
            <dd>{modeLabel}</dd>
          </div>

          <div>
            <dt>Type</dt>
            <dd>{formatSourceDetailValue(sourceType)}</dd>
          </div>

          {sourceKind && (
            <div>
              <dt>Kind</dt>
              <dd>{sourceKind}</dd>
            </div>
          )}

          {upstreamStatus && (
            <div>
              <dt>Status</dt>
              <dd>{upstreamStatus}</dd>
            </div>
          )}

          {recordCount !== undefined && (
            <div>
              <dt>Records</dt>
              <dd>{formatSourceDetailValue(recordCount)}</dd>
            </div>
          )}

          {retrievedAt && (
            <div>
              <dt>Retrieved</dt>
              <dd>{formatSourceTimestamp(retrievedAt)}</dd>
            </div>
          )}

          {updateCadence && (
            <div>
              <dt>Update cadence</dt>
              <dd>{updateCadence}</dd>
            </div>
          )}
        </dl>

        <p className="source-details-disclosure__note">{modeNote}</p>

        {officialUrl && (
          <a
            className="source-details-disclosure__link"
            href={officialUrl}
            target="_blank"
            rel="noreferrer"
          >
            View official source
          </a>
        )}
      </div>
    </details>
  )
}

export default SourceDetailsDisclosure
