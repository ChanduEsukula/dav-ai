import { useMemo, useState } from 'react'
import {
  searchCosmeticEvents,
  type CosmeticEventSearchResponse,
} from '../api/cosmeticEvents'
import SafeInsightCards, { type SafeInsightCard } from './SafeInsightCards'
import { formatDate, formatTimestamp } from '../utils/recallFormatters'

function productLabel(record: CosmeticEventSearchResponse['records'][number]) {
  const firstProduct = record.products[0]

  if (!firstProduct) return 'Cosmetic product not specified'

  return (
    firstProduct.brand_name ||
    firstProduct.name_brand ||
    firstProduct.industry_name ||
    'Cosmetic product not specified'
  )
}

function CosmeticSignal() {
  const [query, setQuery] = useState('')
  const [data, setData] = useState<CosmeticEventSearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSearch() {
    const trimmedQuery = query.trim()

    if (!trimmedQuery) {
      setError('Enter a cosmetic brand, product, reaction, or outcome keyword.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await searchCosmeticEvents(trimmedQuery, 10)
      setData(response)
    } catch {
      setError(
        'Unable to load cosmetic event data. Make sure the FastAPI backend is running on port 8000.'
      )
    } finally {
      setLoading(false)
    }
  }

  const hasNoResults = data && data.records.length === 0
  const hasResults = data && data.records.length > 0
  const topReaction = data?.top_reactions[0] ?? null
  const maxReactionCount =
    data?.top_reactions.reduce((max, item) => Math.max(max, item.count), 0) ?? 0

  const insightCards: SafeInsightCard[] = useMemo(() => {
    if (!data) return []

    return [
      {
        label: 'Source-backed',
        title: 'Public openFDA cosmetic-event source is visible.',
        detail: `${data.source_name} returned ${data.count} public cosmetic-event record${
          data.count === 1 ? '' : 's'
        }, retrieved ${formatTimestamp(data.retrieval_timestamp)}.`,
        tone: 'source',
      },
      {
        label: 'Review signal',
        title: `${data.signal_score.label} cosmetic reporting signal.`,
        detail: `CosmeticSignal score: ${data.signal_score.score}/100. Treat this as a public reporting pattern, not proof of product harm.`,
        tone: 'review',
      },
      {
        label: 'Safety boundary',
        title: 'Cosmetic reports do not prove causation.',
        detail:
          'Reports may be incomplete, duplicated, delayed, or influenced by reporting behavior. Verify official FDA context before taking action.',
        tone: 'safety',
      },
    ]
  }, [data])

  return (
    <section className="cosmeticsignal" id="cosmeticsignal">
      <div className="section-heading">
        <p className="eyebrow">CosmeticSignal module</p>
        <h2>Explore public cosmetic adverse-event reports.</h2>
        <p>
          Search skincare, makeup, hair, fragrance, or cosmetic product keywords. DAV AI checks
          public openFDA cosmetic-event reports and keeps source, audit, and safety boundaries
          visible.
        </p>
      </div>

      <div className="cosmetic-signal-panel">
        <div className="search-box">
          <div className="search-field">
            <label className="field-label" htmlFor="cosmetic-signal-search">
              Cosmetic brand, product, reaction, or outcome
            </label>

            <input
              id="cosmetic-signal-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  handleSearch()
                }
              }}
              placeholder="Search: face cream, hair dye, sunscreen, rash"
              aria-describedby="cosmetic-signal-search-helper"
            />

            <p className="field-helper" id="cosmetic-signal-search-helper">
              Public cosmetic adverse-event reports only. Not medical advice, causation, or official
              safety guidance.
            </p>
          </div>

          <button type="button" onClick={handleSearch} disabled={loading}>
            {loading ? 'Checking public data...' : 'Analyze cosmetics'}
          </button>
        </div>

        {loading && (
          <p className="loading-helper" role="status" aria-live="polite">
            Checking openFDA Cosmetic Event public reporting data.
          </p>
        )}

        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}

        {data && (
          <div className="source-strip" role="status" aria-live="polite">
            <span>{data.count} cosmetic reports reviewed</span>
            <span>Public FDA source: {data.source_name}</span>
            <span>Retrieved {formatTimestamp(data.retrieval_timestamp)}</span>
          </div>
        )}

        {data && <SafeInsightCards cards={insightCards} />}

        {data && (
          <section className="drug-intelligence-card" aria-label="CosmeticSignal summary">
            <div className="drug-intelligence-score">
              <p className="eyebrow">CosmeticSignal</p>
              <h3>{data.signal_score.score} / 100</h3>
              <span>{data.signal_score.label}</span>
            </div>

            <div className="drug-intelligence-copy">
              <h4>{data.signal_score.label} public cosmetic reporting signal</h4>
              <p>
                Transparent signal score based on returned public cosmetic-event report volume,
                reaction concentration, and reaction diversity.
              </p>
              <p className="drug-score-boundary">
                Public reports only. This does not prove causation or provide medical advice.
              </p>
            </div>

            <div className="drug-intelligence-grid">
              <div>
                <small>Review priority</small>
                <span>{data.signal_score.review_priority}</span>
              </div>

              <div>
                <small>Data confidence</small>
                <span>{data.signal_score.data_confidence}</span>
              </div>

              <div>
                <small>Top reaction concentration</small>
                <span>{data.signal_score.top_reaction_concentration}%</span>
              </div>

              <div>
                <small>Score version</small>
                <span>{data.signal_score.score_version}</span>
              </div>
            </div>

            <details className="drug-score-details">
              <summary>How this cosmetic signal score works</summary>
              <ul>
                {data.signal_score.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </details>
          </section>
        )}

        {hasNoResults && (
          <div className="empty-state">
            <h3>No public cosmetic-event reports matched this search.</h3>
            <p>
              No match does not prove the product is safe or unsafe. Try a brand name, product
              type, ingredient, reaction term, or broader cosmetic category.
            </p>
          </div>
        )}

        {data && data.top_reactions.length > 0 && (
          <details className="drug-compact-section" open>
            <summary>
              <span>
                <h3>Top reported cosmetic reactions</h3>
                <small>
                  {data.top_reactions.length} reactions
                  {topReaction ? ` · top: ${topReaction.reaction}` : ''}
                </small>
              </span>
            </summary>

            <div className="reaction-list">
              {data.top_reactions.map((item) => {
                const barWidth =
                  maxReactionCount > 0 ? `${(item.count / maxReactionCount) * 100}%` : '0%'

                return (
                  <div className="reaction-row" key={item.reaction}>
                    <div>
                      <span>{item.reaction}</span>
                      <div className="reaction-bar" aria-hidden="true">
                        <i style={{ width: barWidth }} />
                      </div>
                    </div>

                    <strong>{item.count}</strong>
                  </div>
                )
              })}
            </div>
          </details>
        )}

        {hasResults && (
          <div className="results-grid" aria-label="CosmeticSignal event records">
            {data.records.map((record, index) => (
              <details
                className="recall-card recall-card--compact cosmetic-card"
                key={`${record.report_number ?? 'cosmetic'}-${index}`}
              >
                <summary className="recall-card-summary">
                  <span className={`risk-pill risk-${data.signal_score.label.toLowerCase()}`}>
                    {data.signal_score.label} signal
                  </span>

                  <h3 className="recall-card-title">{productLabel(record)}</h3>

                  <span className="recall-date-inline">
                    <strong>{formatDate(record.report_date)}</strong>
                    <small>Report date</small>
                  </span>
                </summary>

                <div className="recall-card-expanded">
                  <div className="details-grid">
                    <div>
                      <span>Report number</span>
                      <strong>{record.report_number || 'Not provided'}</strong>
                    </div>

                    <div>
                      <span>Serious</span>
                      <strong>{record.serious || 'Not provided'}</strong>
                    </div>

                    <div>
                      <span>Report date</span>
                      <strong>{formatDate(record.report_date)}</strong>
                    </div>

                    <div>
                      <span>Products listed</span>
                      <strong>{record.products.length}</strong>
                    </div>
                  </div>

                  <div className="recall-reason">
                    <small>Reported reactions</small>
                    <p>{record.reactions.length ? record.reactions.join(', ') : 'Not provided'}</p>
                  </div>

                  <div className="recall-reason">
                    <small>Reported outcomes</small>
                    <p>{record.outcomes.length ? record.outcomes.join(', ') : 'Not provided'}</p>
                  </div>

                  <div className="recall-reason">
                    <small>Products</small>
                    <p>
                      {record.products.length
                        ? record.products
                            .map(
                              (product) =>
                                product.brand_name ||
                                product.name_brand ||
                                product.industry_name ||
                                'Unnamed product'
                            )
                            .join(', ')
                        : 'Not provided'}
                    </p>
                  </div>
                </div>
              </details>
            ))}
          </div>
        )}

        {data && (
          <details className="foodradar-limitations">
            <summary>Cosmetic public-data boundary</summary>
            <p>{data.cosmetic_disclaimer}</p>
            <p>{data.medical_disclaimer}</p>
          </details>
        )}
      </div>
    </section>
  )
}

export default CosmeticSignal
