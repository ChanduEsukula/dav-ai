import {
  getSourceIntegrationMode,
  sourceIntegrationModeLabels,
} from '../utils/sourceIntegrationMode'

type SourceIntegrationBadgeProps = {
  sourceId?: string | null
  sourceName?: string | null
  sourceType?: string | null
}

function SourceIntegrationBadge({
  sourceId,
  sourceName,
  sourceType,
}: SourceIntegrationBadgeProps) {
  const mode = getSourceIntegrationMode({ sourceId, sourceName, sourceType })

  if (!mode) return null

  const label = sourceIntegrationModeLabels[mode]

  return (
    <span
      className={`source-integration-badge source-integration-badge--${mode}`}
      title={`Integration mode: ${label}`}
    >
      {label}
    </span>
  )
}

export default SourceIntegrationBadge

