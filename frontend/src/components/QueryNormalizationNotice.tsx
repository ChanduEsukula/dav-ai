import { getSearchComparisonKey } from '../utils/queryNormalization'

type QueryNormalizationNoticeProps = {
  rawQuery: string
  normalizedQuery: string
}

function QueryNormalizationNotice({
  rawQuery,
  normalizedQuery,
}: QueryNormalizationNoticeProps) {
  if (
    !rawQuery ||
    !normalizedQuery ||
    getSearchComparisonKey(rawQuery) === getSearchComparisonKey(normalizedQuery)
  ) {
    return null
  }

  return (
    <p className="query-normalization-notice" role="status" aria-live="polite">
      {`Showing results for '${normalizedQuery}' based on your search '${rawQuery}'.`}
    </p>
  )
}

export default QueryNormalizationNotice
