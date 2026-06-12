import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { searchDrugEvents, type DrugEventSearchResponse } from '../api/drugEvents'
import {
  searchRecalls,
  type RecallResult,
  type RecallSearchResponse,
  type RecallSort,
} from '../api/recalls'
import type { ActivePage } from '../types/navigation'
import { formatDate, formatTimestamp } from '../utils/recallFormatters'
import {
  getSearchComparisonKey,
  getTypoSuggestion,
  getWrongCategorySuggestion,
  normalizeSearchTerm,
} from '../utils/safetyRouteClassifier'

type PharmacySafetyPageProps = {
  initialQuery: string
  goToPage: (page: ActivePage, query?: string) => void
}

type PharmacySource = 'recall' | 'drug'

type PharmacySearchOptions = {
  updateUrl?: boolean
  skipIfCompleted?: boolean
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

function updatePharmacyQueryInUrl(query: string, mode: 'push' | 'replace') {
  const url = new URL(window.location.href)
  const currentPage = url.searchParams.get('page')
  const currentQuery = url.searchParams.get('q') ?? ''

  if (currentPage === 'pharmacy-safety' && currentQuery === query) return

  url.searchParams.set('page', 'pharmacy-safety')
  url.searchParams.set('q', query)

  if (mode === 'push') {
    window.history.pushState(null, '', url.toString())
  } else {
    window.history.replaceState(null, '', url.toString())
  }
}

function PharmacySafetyPage({ initialQuery, goToPage }: PharmacySafetyPageProps) {
  const normalizedInitialQuery = normalizeSearchTerm(initialQuery)
  const [query, setQuery] = useState(normalizedInitialQuery)
  const [submittedQuery, setSubmittedQuery] = useState(normalizedInitialQuery)
  const [recallData, setRecallData] = useState<RecallSearchResponse | null>(null)
  const [drugData, setDrugData] = useState<DrugEventSearchResponse | null>(null)
  const [recallSort, setRecallSort] = useState<RecallSort>('score')
  const [loading, setLoading] = useState(Boolean(normalizedInitialQuery))
  const [error, setError] = useState('')
  const [helper, setHelper] = useState('')
  const [notice, setNotice] = useState('')
  const [failedSources, setFailedSources] = useState<PharmacySource[]>([])
  const requestIdRef = useRef(0)
  const inFlightKeyRef = useRef('')
  const completedKeyRef = useRef('')
  const isMountedRef = useRef(true)

  useEffect(() => {
    isMountedRef.current = true

    return () => {
      isMountedRef.current = false
    }
  }, [])

  const loadPharmacyPreview = useCallback(
    async (
      nextQuery: string,
      nextSort: RecallSort,
      options: PharmacySearchOptions = {},
    ) => {
      const cleanQuery = normalizeSearchTerm(nextQuery)
      if (!cleanQuery) return

      const requestKey = `${getSearchComparisonKey(cleanQuery)}::${nextSort}`

      if (inFlightKeyRef.current === requestKey) return
      if (options.skipIfCompleted && completedKeyRef.current === requestKey) {
        setQuery(cleanQuery)
        setSubmittedQuery(cleanQuery)
        setError('')
        setHelper('')
        setNotice('')
        return
      }

      const requestId = requestIdRef.current + 1
      requestIdRef.current = requestId
      inFlightKeyRef.current = requestKey
      completedKeyRef.current = ''

      setQuery(cleanQuery)
      setSubmittedQuery(cleanQuery)
      setRecallData(null)
      setDrugData(null)
      setFailedSources([])
      setLoading(true)
      setError('')
      setHelper('')
      setNotice('')

      if (options.updateUrl) {
        updatePharmacyQueryInUrl(cleanQuery, 'push')
      }

      const [recallResult, drugResult] = await Promise.allSettled([
        searchRecalls(cleanQuery, 8, nextSort),
        searchDrugEvents(cleanQuery, 8),
      ])

      if (!isMountedRef.current || requestId !== requestIdRef.current) return

      const nextFailedSources: PharmacySource[] = []
      const nextRecallData = recallResult.status === 'fulfilled' ? recallResult.value : null
      const nextDrugData = drugResult.status === 'fulfilled' ? drugResult.value : null

      if (recallResult.status === 'rejected') nextFailedSources.push('recall')
      if (drugResult.status === 'rejected') nextFailedSources.push('drug')

      setRecallData(nextRecallData)
      setDrugData(nextDrugData)
      setFailedSources(nextFailedSources)

      if (!nextRecallData && !nextDrugData) {
        setError('Unable to load public records. Check backend/source availability.')
      } else if (nextFailedSources.length > 0) {
        setNotice(
          'Some public sources were unavailable. Showing the records that loaded successfully.',
        )
      } else {
        completedKeyRef.current = requestKey
      }

      inFlightKeyRef.current = ''
      setLoading(false)
    },
    [],
  )

  useEffect(() => {
    const cleanQuery = normalizeSearchTerm(initialQuery)
    let isCurrentEffect = true

    async function syncInitialQuery() {
      if (!cleanQuery) {
        await Promise.resolve()
        if (!isCurrentEffect) return

        requestIdRef.current += 1
        inFlightKeyRef.current = ''
        completedKeyRef.current = ''
        setQuery('')
        setSubmittedQuery('')
        setRecallData(null)
        setDrugData(null)
        setRecallSort('score')
        setLoading(false)
        setError('')
        setHelper('')
        setNotice('')
        setFailedSources([])
        return
      }

      const urlQuery = new URLSearchParams(window.location.search).get('q') ?? ''
      if (urlQuery !== cleanQuery) {
        updatePharmacyQueryInUrl(cleanQuery, 'replace')
      }

      setRecallSort('score')
      await loadPharmacyPreview(cleanQuery, 'score', { skipIfCompleted: true })
    }

    void syncInitialQuery()

    return () => {
      isCurrentEffect = false
    }
  }, [initialQuery, loadPharmacyPreview])

  function handleSearch() {
    const cleanInput = normalizeSearchTerm(query)
    const cleanSubmittedQuery = normalizeSearchTerm(submittedQuery)

    if (!cleanInput && !cleanSubmittedQuery) {
      setError('')
      setNotice('')
      setHelper(
        'Enter a product, drug, food, cosmetic, UPC, NDC, or lot term to search public records.',
      )
      return
    }

    if (!cleanInput) {
      void loadPharmacyPreview(cleanSubmittedQuery, recallSort)
      return
    }

    void loadPharmacyPreview(cleanInput, recallSort, {
      updateUrl: true,
      skipIfCompleted: true,
    })
  }

  function handleSortChange(nextSort: RecallSort) {
    const cleanSubmittedQuery = normalizeSearchTerm(submittedQuery)
    if (nextSort === recallSort || !cleanSubmittedQuery) return

    setRecallSort(nextSort)
    void loadPharmacyPreview(cleanSubmittedQuery, nextSort)
  }

  function handleExampleClick(example: string) {
    setQuery(example)
    setError('')
    setHelper('')
    setNotice('')
    void loadPharmacyPreview(example, recallSort, {
      updateUrl: true,
      skipIfCompleted: true,
    })
  }

  function handleTypoSuggestion(correctedQuery: string) {
    setQuery(correctedQuery)
    void loadPharmacyPreview(correctedQuery, recallSort, { updateUrl: true })
  }

  const recallResults = recallData?.results ?? []
  const topReactions = drugData?.top_reactions.slice(0, 5) ?? []
  const topReactionCount = Math.max(topReactions[0]?.count ?? 0, 1)
  const displayQuery = submittedQuery || 'a medication or drug product'
  const hasResults = Boolean(recallData || drugData)
  const hasZeroResults =
    Boolean(recallData && drugData) && recallData?.count === 0 && drugData?.count === 0
  const wrongCategorySuggestion = useMemo(
    () => getWrongCategorySuggestion('pharmacy', submittedQuery),
    [submittedQuery],
  )
  const typoSuggestion = hasZeroResults ? getTypoSuggestion(submittedQuery) : null
  const loadedSourceNames = [recallData?.source_name, drugData?.source_name].filter(
    (sourceName): sourceName is string => Boolean(sourceName),
  )
  const sourceLabel =
    loadedSourceNames.length > 0
      ? loadedSourceNames.join(' + ')
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
              handleSearch()
            }}
          >
            <label htmlFor="pharmacy-page-search">Search pharmacy records</label>
            <div>
              <input
                id="pharmacy-page-search"
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value)
                  if (helper) setHelper('')
                }}
                placeholder="Search another drug, brand, ingredient, or NDC"
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
                onClick={() => handleExampleClick(example)}
              >
                {example}
              </button>
            ))}
          </div>

          {typoSuggestion && hasZeroResults && !loading && (
            <div className="pharmacy-typo-suggestion" role="status" aria-live="polite">
              <span>
                Spelling suggestion: did you mean <strong>{typoSuggestion}</strong>?
              </span>
              <button type="button" onClick={() => handleTypoSuggestion(typoSuggestion)}>
                Use {typoSuggestion}
              </button>
            </div>
          )}

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

      {helper && (
        <p className="safety-search-guidance" role="status">
          {helper}
        </p>
      )}

      {notice && (
        <p className="safety-search-guidance" role="status">
          {notice}
        </p>
      )}

      {wrongCategorySuggestion && !loading && (
        <aside className="safety-route-suggestion" aria-live="polite">
          <span>{wrongCategorySuggestion.message}</span>
          <button
            type="button"
            onClick={() =>
              goToPage(wrongCategorySuggestion.page, normalizeSearchTerm(submittedQuery))
            }
          >
            Open {wrongCategorySuggestion.label}
          </button>
        </aside>
      )}

      {hasZeroResults && !loading && (
        <aside className="safety-search-guidance" aria-live="polite">
          <span>
            No public records returned for this exact search. Check spelling or try a
            simpler/generic term.
          </span>
        </aside>
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
              <dd>{failedSources.includes('recall') ? 'Unavailable' : (recallData?.count ?? 0)}</dd>
            </div>
            <div>
              <dt>FAERS reports</dt>
              <dd>{failedSources.includes('drug') ? 'Unavailable' : (drugData?.count ?? 0)}</dd>
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