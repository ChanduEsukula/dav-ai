import { useEffect, useState } from 'react'
import { searchDrugEvents, type DrugEventSearchResponse } from '../api/drugEvents'
import {
  searchRecalls,
  type RecallResult,
  type RecallSearchResponse,
  type RecallSort,
} from '../api/recalls'
import { formatDate, formatTimestamp } from '../utils/recallFormatters'

type PharmacySafetyPageProps = {
  initialQuery: string
}

function truncateText(value: string | null | undefined, maxLength = 88) {
  if (!value) return 'Not listed'
  if (value.length <= maxLength) return value
  return `${value.slice(0, maxLength).trim()}...`
}

function compactProductName(value: string | null | undefined) {
  if (!value) return 'Product description unavailable'

  const normalizedValue = value.replace(/\s+/g, ' ').trim()
  const primaryDescription = normalizedValue
    .split(/(?:Distributed by:|Manufactured by:|NDC:?)/i)[0]
    ?.trim()

  return truncateText(primaryDescription || normalizedValue)
}

function PharmacyRecallRow({ record, index }: { record: RecallResult; index: number }) {
  const fullProductName = record.product_description || 'Product description unavailable'

  return (
    <details
      className="pharmacy-record-row"
      key={`${record.recall_number ?? 'recall'}-${index}`}
    >
      <summary>
        <span className="pharmacy-record-row__product">
          <span className="pharmacy-record-row__badges">
            <small>{record.classification || 'Unclassified'}</small>
            <small>{record.risk_score.label} review signal</small>
          </span>
          <strong title={fullProductName}>{compactProductName(fullProductName)}</strong>
          <span>{record.recall_number || 'Recall number not listed'}</span>
        </span>

        <span className="pharmacy-record-row__firm">
          <strong>{record.recalling_firm || 'Firm not listed'}</strong>
          <span>{record.status || 'Status not listed'}</span>
        </span>

        <span className="pharmacy-record-row__date">
          <strong>{formatDate(record.recall_initiation_date)}</strong>
          <span>Initiated</span>
        </span>

        <span className="pharmacy-record-row__arrow" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </span>
      </summary>

      <div className="pharmacy-record-details">
        <div className="pharmacy-record-details__wide">
          <span>Full product description</span>
          <strong>{fullProductName}</strong>
        </div>

        <div className="pharmacy-record-details__wide">
          <span>Reason for recall</span>
          <strong>{record.reason_for_recall || 'Not listed'}</strong>
        </div>

        <div>
          <span>Distribution</span>
          <strong>{record.distribution_pattern || 'Not listed'}</strong>
        </div>

        <div>
          <span>Review priority</span>
          <strong>
            {record.risk_score.label} ({record.risk_score.score})
          </strong>
        </div>
      </div>
    </details>
  )
}

function PharmacySafetyPage({ initialQuery }: PharmacySafetyPageProps) {
  const [query, setQuery] = useState(initialQuery)
  const [submittedQuery, setSubmittedQuery] = useState(initialQuery)
  const [recallData, setRecallData] = useState<RecallSearchResponse | null>(null)
  const [drugData, setDrugData] = useState<DrugEventSearchResponse | null>(null)
  const [recallSort, setRecallSort] = useState<RecallSort>('score')
  const [loading, setLoading] = useState(Boolean(initialQuery))
  const [error, setError] = useState('')

  async function loadPharmacyPreview(nextQuery: string, nextSort: RecallSort = recallSort) {
    const cleanQuery = nextQuery.trim()

    if (!cleanQuery) {
      setError('Enter a drug, medication, brand, ingredient, or NDC.')
      return
    }

    setLoading(true)
    setError('')
    setSubmittedQuery(cleanQuery)

    const nextParams = new URLSearchParams(window.location.search)
    nextParams.set('page', 'pharmacy-safety')
    nextParams.set('q', cleanQuery)
    window.history.replaceState(null, '', `?${nextParams.toString()}`)

    try {
      const [recallResponse, drugResponse] = await Promise.all([
        searchRecalls(cleanQuery, 8, nextSort),
        searchDrugEvents(cleanQuery, 8),
      ])

      setRecallData(recallResponse)
      setDrugData(drugResponse)
    } catch {
      setError('Unable to load pharmacy safety records. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const cleanQuery = initialQuery.trim()
    if (!cleanQuery) return

    let isMounted = true

    async function loadInitial() {
      setLoading(true)
      setError('')

      try {
        const [recallResponse, drugResponse] = await Promise.all([
          searchRecalls(cleanQuery, 8, 'score'),
          searchDrugEvents(cleanQuery, 8),
        ])

        if (isMounted) {
          setRecallData(recallResponse)
          setDrugData(drugResponse)
          setSubmittedQuery(cleanQuery)
          setQuery(cleanQuery)
          setRecallSort('score')
        }
      } catch {
        if (isMounted) {
          setError('Unable to load pharmacy safety records. Make sure the backend is running.')
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    void loadInitial()

    return () => {
      isMounted = false
    }
  }, [initialQuery])

  async function handleSortChange(nextSort: RecallSort) {
    if (nextSort === recallSort || !submittedQuery.trim()) return

    setRecallSort(nextSort)
    await loadPharmacyPreview(submittedQuery, nextSort)
  }

  const recallResults = recallData?.results ?? []
  const topReactions = drugData?.top_reactions.slice(0, 5) ?? []
  const topReactionCount = Math.max(topReactions[0]?.count ?? 0, 1)
  const displayQuery = submittedQuery || 'a medication or drug product'
  const hasResults = Boolean(recallData || drugData)
  const sourceLabel =
    recallData || drugData
      ? `${recallData?.source_name ?? 'openFDA enforcement'} + ${
          drugData?.source_name ?? 'openFDA FAERS'
        }`
      : 'openFDA enforcement + openFDA FAERS'

  return (
    <section className="safety-area-page safety-area-page--pharmacy pharmacy-detail-page">
      <header className="pharmacy-overview">
        <div className="pharmacy-overview__main">
          <p className="eyebrow">Pharmacy Safety</p>

          <h1>
            {submittedQuery ? (
              <>
                Safety review for <span>{submittedQuery}</span>
              </>
            ) : (
              'Search pharmacy safety records'
            )}
          </h1>

          <p className="pharmacy-overview__description">
            Compare official recall records with public adverse-event reporting patterns. These
            sources answer different questions and should be reviewed separately.
          </p>

          <form
            className="pharmacy-page-search"
            onSubmit={(event) => {
              event.preventDefault()
              void loadPharmacyPreview(query, recallSort)
            }}
          >
            <label htmlFor="pharmacy-page-search">Search pharmacy records</label>
            <div>
              <input
                id="pharmacy-page-search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Drug, brand, ingredient, or NDC"
              />
              <button type="submit" disabled={loading}>
                {loading ? 'Checking...' : 'Search'}
              </button>
            </div>
          </form>

          <div className="pharmacy-example-row" aria-label="Example pharmacy searches">
            <span>Try</span>
            {['Xanax', 'Metformin', 'Ibuprofen', 'Amoxicillin'].map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => {
                  setQuery(example)
                  void loadPharmacyPreview(example, recallSort)
                }}
              >
                {example}
              </button>
            ))}
          </div>

          <p className="pharmacy-source-line">
            <span aria-hidden="true" />
            <strong>Public FDA records</strong>
            <span>{sourceLabel}</span>
            <span>Not clinical guidance</span>
          </p>
        </div>
      </header>

      {loading && (
        <p className="safety-area-status" role="status" aria-live="polite">
          Checking pharmacy public records...
        </p>
      )}

      {error && (
        <p className="error-message pharmacy-page-error" role="alert">
          {error}
        </p>
      )}

      {hasResults && (
        <section className="pharmacy-summary-strip" aria-label={`Summary for ${displayQuery}`}>
          <div className="pharmacy-summary-strip__query">
            <small>Current query</small>
            <strong>{displayQuery}</strong>
            <span>Public records, not a personal safety determination</span>
          </div>

          <dl className="pharmacy-summary-metrics">
            <div>
              <dt>Recall matches</dt>
              <dd>{recallData?.count ?? 0}</dd>
            </div>
            <div>
              <dt>FAERS reports</dt>
              <dd>{drugData?.count ?? 0}</dd>
            </div>
            <div>
              <dt>Reporting signal</dt>
              <dd>{drugData?.intelligence_score.label ?? 'Not available'}</dd>
            </div>
            <div>
              <dt>Review priority</dt>
              <dd>{drugData?.intelligence_score.review_priority ?? 'Not available'}</dd>
            </div>
          </dl>
        </section>
      )}

      <div className="pharmacy-workspace">
        <section className="pharmacy-recall-panel" id="pharmacy-recall-records">
          <div className="pharmacy-panel-header">
            <div>
              <p className="eyebrow">Recall records</p>
              <h2>Matched official records</h2>
              <span>
                {recallData
                  ? `Showing ${recallResults.length} of ${recallData.count} returned record${
                      recallData.count === 1 ? '' : 's'
                    }`
                  : 'Search to load recall records'}
              </span>
            </div>

            <div
              className="recall-sort-control"
              role="group"
              aria-label="Sort pharmacy recall records"
            >
              <button
                type="button"
                className={recallSort === 'score' ? 'active' : ''}
                onClick={() => void handleSortChange('score')}
                disabled={loading}
              >
                Priority
              </button>
              <button
                type="button"
                className={recallSort === 'latest' ? 'active' : ''}
                onClick={() => void handleSortChange('latest')}
                disabled={loading}
              >
                Latest
              </button>
            </div>
          </div>

          {recallResults.length > 0 ? (
            <div className="pharmacy-record-table" aria-label="Recall search results">
              <div className="pharmacy-record-table__head" aria-hidden="true">
                <span>Product and record</span>
                <span>Firm and status</span>
                <span>Date</span>
                <span />
              </div>

              {recallResults.map((record, index) => (
                <PharmacyRecallRow
                  key={`${record.recall_number ?? 'recall'}-${index}`}
                  record={record}
                  index={index}
                />
              ))}
            </div>
          ) : recallData ? (
            <div className="pharmacy-empty-card">
              <h3>No matching recall records returned.</h3>
              <p>
                Try a generic name, brand, strength, product wording, or NDC. No match does not
                prove a medication is safe.
              </p>
            </div>
          ) : (
            <div className="pharmacy-empty-card pharmacy-empty-card--quiet">
              <h3>Recall results will appear here.</h3>
              <p>Search above to compare official recall records and public event patterns.</p>
            </div>
          )}
        </section>

        <aside className="pharmacy-insight-rail">
          <section className="pharmacy-insight-card" id="pharmacy-event-patterns">
            <div className="pharmacy-insight-card__header">
              <div>
                <p className="eyebrow">Event patterns</p>
                <h2>FAERS reporting summary</h2>
              </div>
              {drugData && (
                <span className="pharmacy-signal-badge">
                  {drugData.intelligence_score.score}/100
                </span>
              )}
            </div>

            {drugData ? (
              <>
                <dl className="pharmacy-event-metrics">
                  <div>
                    <dt>Signal</dt>
                    <dd>{drugData.intelligence_score.label}</dd>
                  </div>
                  <div>
                    <dt>Confidence</dt>
                    <dd>{drugData.intelligence_score.data_confidence}</dd>
                  </div>
                </dl>

                <div className="pharmacy-reaction-summary">
                  <div className="pharmacy-subsection-heading">
                    <strong>Top reported reactions</strong>
                    <span>Count in returned records</span>
                  </div>

                  {topReactions.length > 0 ? (
                    <div className="pharmacy-reaction-list">
                      {topReactions.map((reaction) => (
                        <div key={reaction.reaction}>
                          <span>
                            <strong>{reaction.reaction}</strong>
                            <i
                              aria-hidden="true"
                              style={{
                                width: `${Math.max(
                                  8,
                                  Math.round((reaction.count / topReactionCount) * 100)
                                )}%`,
                              }}
                            />
                          </span>
                          <b>{reaction.count}</b>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p>No top reactions returned for this search.</p>
                  )}
                </div>

                <details className="pharmacy-interpretation">
                  <summary>
                    <span>How to interpret this signal</span>
                    <strong aria-hidden="true">+</strong>
                  </summary>
                  <div>
                    <p>
                      FAERS reports can identify reporting patterns, but they cannot establish
                      incidence, causation, or personal risk.
                    </p>
                    <p>
                      Retrieved {formatTimestamp(drugData.retrieval_timestamp)} from{' '}
                      {drugData.source_name}.
                    </p>
                  </div>
                </details>
              </>
            ) : (
              <p className="pharmacy-insight-card__empty">
                Search above to load the reporting signal and leading reactions.
              </p>
            )}
          </section>

          <section className="pharmacy-safety-card">
            <div>
              <p className="eyebrow">Safety boundary</p>
              <h2>Use these records to verify, not diagnose.</h2>
            </div>
            <ul>
              <li>Recall records and adverse-event reports answer different questions.</li>
              <li>Reports are signals, not proof of harm or causation.</li>
              <li>Verify the product, strength, firm, date, and official source.</li>
            </ul>
            {recallData && (
              <p className="pharmacy-safety-card__source">
                Recall records retrieved {formatTimestamp(recallData.retrieval_timestamp)}.
              </p>
            )}
          </section>
        </aside>
      </div>
    </section>
  )
}

export default PharmacySafetyPage