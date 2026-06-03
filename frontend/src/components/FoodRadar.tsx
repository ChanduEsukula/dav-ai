import { useMemo, useState } from 'react'
import {
  searchEverydaySafety,
  type EverydaySafetyRecord,
  type EverydaySafetySearchResponse,
} from '../api/everydaySafety'
import { formatDate, formatTimestamp, riskExplanation } from '../utils/recallFormatters'

function sourceLabel(sourceType: EverydaySafetyRecord['source_type']) {
  if (sourceType === 'USDA_FSIS_RECALL') {
    return 'USDA FSIS'
  }

  return 'FDA Food'
}

function FoodRadar() {
  const [query, setQuery] = useState('')
  const [data, setData] = useState<EverydaySafetySearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [sortMode, setSortMode] = useState<'score' | 'latest'>('score')

  async function handleSearch() {
    const trimmedQuery = query.trim()

    if (!trimmedQuery) {
      setError('Enter a food, supplement, protein powder, meat, poultry, or packaged product.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await searchEverydaySafety(trimmedQuery, 5)
      setData(response)
    } catch {
      setError(
        'Unable to load FoodRadar data. Make sure the FastAPI backend is running on port 8000.'
      )
    } finally {
      setLoading(false)
    }
  }

  const sortedResults = useMemo(() => {
    if (!data) return []

    return [...data.results].sort((left, right) => {
      if (sortMode === 'latest') {
        return Number(right.recall_initiation_date || 0) - Number(left.recall_initiation_date || 0)
      }

      return right.risk_score.score - left.risk_score.score
    })
  }, [data, sortMode])

  const topResult = sortedResults[0] ?? null
  const hasResults = sortedResults.length > 0
  const hasNoResults = data && sortedResults.length === 0

  return (
    <section className="foodradar" id="foodradar">
      <div className="section-heading">
        <p className="eyebrow">FoodRadar module</p>
        <h2>Check everyday food and supplement recall signals.</h2>
        <p>
          Search foods, supplements, protein powders, packaged groceries, meat, poultry, or egg
          products. DAV AI checks public FDA/openFDA and USDA FSIS sources and shows source-backed
          recall records.
        </p>
      </div>

      <div className="foodradar-panel">
        <div className="search-box">
          <div className="search-field">
            <label className="field-label" htmlFor="foodradar-search">
              Food, supplement, or product
            </label>

            <input
              id="foodradar-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  handleSearch()
                }
              }}
              placeholder="Search: chocolate, peanut butter, chicken, protein powder"
              aria-describedby="foodradar-search-helper"
            />

            <p className="field-helper" id="foodradar-search-helper">
              Public recall records only. Not medical advice, safety guarantee, or official recall
              instruction.
            </p>
          </div>

          <button type="button" onClick={handleSearch} disabled={loading}>
            {loading ? 'Checking public data...' : 'Check FoodRadar'}
          </button>
        </div>

        {loading && (
          <p className="loading-helper" role="status" aria-live="polite">
            Checking FDA Food Enforcement and USDA FSIS public recall sources.
          </p>
        )}

        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}

        {data && (
          <div className="source-strip" role="status" aria-live="polite">
            <span>{data.count} records matched</span>
            <span>Strategy: {data.search_strategy_used}</span>
            <span>Retrieved {formatTimestamp(data.retrieval_timestamp)}</span>
          </div>
        )}

        {data && (
          <div className="foodradar-source-grid" aria-label="FoodRadar sources checked">
            {data.sources_checked.map((source) => (
              <div className="foodradar-source-card" key={source.source_id}>
                <small>{source.source_type}</small>
                <strong>{source.source_name}</strong>
                <span className={`foodradar-source-status status-${source.upstream_status}`}>
                  {source.upstream_status} · {source.record_count} record
                  {source.record_count === 1 ? '' : 's'}
                </span>
              </div>
            ))}
          </div>
        )}

        {topResult && (
          <section className="consumer-summary" aria-label="FoodRadar safety summary">
            <div className="consumer-summary__content">
              <h3>
                DAV AI found {data?.count ?? 0} public food/supplement recall record
                {data?.count === 1 ? '' : 's'} that may match your search.
              </h3>

              <div className="consumer-summary__signal">
                <span>Highest review signal:</span>
                <strong>{topResult.risk_score.label}</strong>
              </div>

              <p>
                Review product names, lot numbers, code information, recalling firm, source, and
                dates. This is public data only and not official recall guidance.
              </p>
            </div>
          </section>
        )}

        {hasNoResults && (
          <div className="empty-state">
            <h3>No public food/supplement recall records matched this search.</h3>
            <p>
              No match does not prove the product is safe or unsafe. Try a brand name, product
              name, ingredient, recall reason, or more specific package wording.
            </p>
          </div>
        )}

        {hasResults && (
          <>
            <div className="recall-results-toolbar">
              <div>
                <span>Sort results</span>
                <p>Choose how public recall records are ordered.</p>
              </div>

              <div className="recall-sort-control" role="group" aria-label="Sort FoodRadar results">
                <button
                  type="button"
                  className={sortMode === 'score' ? 'active' : ''}
                  onClick={() => setSortMode('score')}
                >
                  Highest score
                </button>

                <button
                  type="button"
                  className={sortMode === 'latest' ? 'active' : ''}
                  onClick={() => setSortMode('latest')}
                >
                  Latest recall
                </button>
              </div>
            </div>

            <div className="results-grid" aria-label="FoodRadar search results">
              {sortedResults.map((result, index) => (
                <details
                  className="recall-card recall-card--compact foodradar-card"
                  key={`${result.source_type}-${result.recall_number ?? result.record_id ?? index}`}
                >
                  <summary className="recall-card-summary">
                    <span className={`risk-pill risk-${result.risk_score.label.toLowerCase()}`}>
                      {result.risk_score.label} signal
                    </span>

                    <span className="foodradar-source-pill">{sourceLabel(result.source_type)}</span>

                    <h3 className="recall-card-title">
                      {result.product_description || 'Unnamed recalled product'}
                    </h3>

                    <span className="recall-score-inline">
                      <strong>{result.risk_score.score}</strong>
                      <small>Review score</small>
                    </span>
                  </summary>

                  <div className="recall-card-expanded">
                    <div className="recall-full-name-panel">
                      <small>Full product description</small>
                      <strong>{result.product_description || 'Not provided'}</strong>
                    </div>

                    <div className="recall-firm-panel">
                      <small>Recalling firm / establishment</small>
                      <strong>{result.recalling_firm || 'Unknown'}</strong>
                    </div>

                    <div className="details-grid">
                      <div>
                        <span>Recall number</span>
                        <strong>{result.recall_number || 'Not provided'}</strong>
                      </div>

                      <div>
                        <span>Classification</span>
                        <strong>{result.classification || 'Not provided'}</strong>
                      </div>

                      <div>
                        <span>Status</span>
                        <strong>{result.status || 'Not provided'}</strong>
                      </div>

                      <div>
                        <span>Recall date</span>
                        <strong>{formatDate(result.recall_initiation_date)}</strong>
                      </div>

                      <div>
                        <span>Report date</span>
                        <strong>{formatDate(result.report_date)}</strong>
                      </div>

                      <div>
                        <span>Quantity</span>
                        <strong>{result.product_quantity || 'Not provided'}</strong>
                      </div>
                    </div>

                    <div className="recall-reason">
                      <small>Reason for recall</small>
                      <p>{result.reason_for_recall || 'Not provided'}</p>
                    </div>

                    <div className="recall-reason">
                      <small>Code / lot / label information</small>
                      <p>{result.code_info || 'Not provided'}</p>
                    </div>

                    <div className="recall-reason">
                      <small>Distribution pattern</small>
                      <p>{result.distribution_pattern || 'Not provided'}</p>
                    </div>

                    <details className="recall-score-help">
                      <summary>How this review score works</summary>
                      <p>{riskExplanation(result)}</p>
                    </details>

                    <div className="audit-panel compact-audit">
                      <h4>Source context</h4>
                      <p>
                        {result.source.name} · Retrieved{' '}
                        {formatTimestamp(result.source.retrieval_timestamp)}
                      </p>
                      <p>{result.source.endpoint}</p>
                    </div>
                  </div>
                </details>
              ))}
            </div>
          </>
        )}

        {data && (
          <details className="foodradar-limitations">
            <summary>Limitations and public-data boundary</summary>
            <ul>
              {data.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
            <p>{data.public_data_disclaimer}</p>
          </details>
        )}
      </div>
    </section>
  )
}

export default FoodRadar
