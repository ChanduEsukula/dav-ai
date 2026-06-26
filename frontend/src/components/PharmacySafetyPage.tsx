import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  buildDrugEventAssistantContext,
  buildRecallAssistantContext,
  type AssistantChatContext,
} from '../api/assistant'
import { searchDrugEvents, type DrugEventSearchResponse } from '../api/drugEvents'
import {
  searchRecalls,
  type RecallResult,
  type RecallSearchResponse,
  type RecallSort,
} from '../api/recalls'
import { PAGE_IDS, type ActivePage } from '../types/navigation'
import { formatDate, formatTimestamp } from '../utils/recallFormatters'
import {
  getSearchComparisonKey,
  getWrongCategorySuggestion,
  normalizeSearchTerm,
} from '../utils/safetyRouteClassifier'
import { normalizeSafetyQuery } from '../utils/queryNormalization'
import { writeSafetyQueryToUrl } from '../utils/safetyQueryUrl'
import QueryNormalizationNotice from './QueryNormalizationNotice'
import QueryTypeahead from './QueryTypeahead'

type PharmacySafetyPageProps = {
  initialQuery: string
  initialRawQuery?: string
  goToPage: (page: ActivePage, query?: string, rawQuery?: string) => void
  setAssistantContext?: (context: AssistantChatContext | null) => void
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

function recallSourceLabel(record: RecallResult) {
  if (record.source_kind === 'normalized_public_notice') {
    return 'Normalized public notice'
  }
  if (record.source_kind === 'public_notice') {
    return 'Official public notice'
  }
  return 'Official API record'
}

function PharmacyRecallRow({ record, index }: { record: RecallResult; index: number }) {
  const fullProductName = record.product_description || 'Product description unavailable'
  const noticeConfidence = record.extraction_confidence
    ? `Notice extraction: ${record.extraction_confidence}`
    : null

  return (
    <details
      className="pharmacy-record-row"
      key={`${record.recall_number ?? 'recall'}-${index}`}
    >
      <summary>
        <span className="pharmacy-record-row__product">
          <span className="pharmacy-record-row__badges">
            <small>{record.classification || recallSourceLabel(record)}</small>
            <small>{noticeConfidence || `${record.risk_score.label} review signal`}</small>
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
          <span>{recallSourceLabel(record)}</span>
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

        {record.remedy && (
          <div className="pharmacy-record-details__wide">
            <span>Remedy / action</span>
            <strong>{record.remedy}</strong>
          </div>
        )}

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

        <div>
          <span>Record type</span>
          <strong>{recallSourceLabel(record)}</strong>
        </div>

        {record.record_url && (
          <div className="pharmacy-record-details__wide">
            <span>Official source</span>
            <strong>
              <a href={record.record_url} target="_blank" rel="noreferrer">
                Open official record
              </a>
            </strong>
          </div>
        )}
      </div>
    </details>
  )
}

function PharmacySafetyPage({
  initialQuery,
  initialRawQuery,
  goToPage,
  setAssistantContext,
}: PharmacySafetyPageProps) {
  const initialNormalization = normalizeSafetyQuery(
    initialRawQuery || initialQuery,
    'pharmacy',
  )
  const normalizedInitialQuery = initialNormalization.normalizedQuery
  const [query, setQuery] = useState(initialNormalization.rawQuery)
  const [submittedQuery, setSubmittedQuery] = useState(normalizedInitialQuery)
  const [submittedRawQuery, setSubmittedRawQuery] = useState(
    initialNormalization.rawQuery,
  )
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
      const normalization = normalizeSafetyQuery(nextQuery, 'pharmacy')
      const cleanQuery = normalization.normalizedQuery
      if (!cleanQuery) {
        setAssistantContext?.(null)
        return
      }

      const requestKey = `${getSearchComparisonKey(cleanQuery)}::${nextSort}`

      if (inFlightKeyRef.current === requestKey) return
      if (options.skipIfCompleted && completedKeyRef.current === requestKey) {
        setQuery(normalization.rawQuery)
        setSubmittedQuery(cleanQuery)
        setSubmittedRawQuery(normalization.rawQuery)
        setError('')
        setHelper('')
        setNotice('')
        return
      }

      const requestId = requestIdRef.current + 1
      requestIdRef.current = requestId
      inFlightKeyRef.current = requestKey
      completedKeyRef.current = ''

      setQuery(normalization.rawQuery)
      setSubmittedQuery(cleanQuery)
      setSubmittedRawQuery(normalization.rawQuery)
      setRecallData(null)
      setDrugData(null)
      setFailedSources([])
      setLoading(true)
      setError('')
      setHelper('')
      setNotice('')
      setAssistantContext?.(null)

      if (options.updateUrl) {
        writeSafetyQueryToUrl(
          PAGE_IDS.PHARMACY_SAFETY,
          cleanQuery,
          normalization.rawQuery,
          'push',
        )
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
        setAssistantContext?.(null)
        setError('Unable to load public records. Check backend/source availability.')
      } else if (nextFailedSources.length > 0) {
        setNotice(
          'Some public sources were unavailable. Showing the records that loaded successfully.',
        )
      } else {
        completedKeyRef.current = requestKey
      }

      if (nextDrugData && nextDrugData.count > 0) {
        setAssistantContext?.(buildDrugEventAssistantContext(nextDrugData))
      } else if (nextRecallData && nextRecallData.count > 0) {
        setAssistantContext?.(buildRecallAssistantContext(nextRecallData))
      } else {
        setAssistantContext?.(null)
      }

      inFlightKeyRef.current = ''
      setLoading(false)
    },
    [setAssistantContext],
  )

  useEffect(() => {
    const normalization = normalizeSafetyQuery(
      initialRawQuery || initialQuery,
      'pharmacy',
    )
    const cleanQuery = normalization.normalizedQuery
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
        setSubmittedRawQuery('')
        setRecallData(null)
        setDrugData(null)
        setRecallSort('score')
        setLoading(false)
        setError('')
        setHelper('')
        setNotice('')
        setFailedSources([])
        setAssistantContext?.(null)
        return
      }

      writeSafetyQueryToUrl(
        PAGE_IDS.PHARMACY_SAFETY,
        cleanQuery,
        normalization.rawQuery,
        'replace',
      )

      setRecallSort('score')
      await loadPharmacyPreview(normalization.rawQuery, 'score', {
        skipIfCompleted: true,
      })
    }

    void syncInitialQuery()

    return () => {
      isCurrentEffect = false
    }
  }, [initialQuery, initialRawQuery, loadPharmacyPreview, setAssistantContext])

  function handleSearch() {
    const cleanInput = normalizeSearchTerm(query)
    const cleanSubmittedQuery = normalizeSearchTerm(submittedQuery)

    if (!cleanInput && !cleanSubmittedQuery) {
      setError('')
      setNotice('')
      setAssistantContext?.(null)
      setHelper(
        'Enter a drug, brand, active ingredient, or product wording to search public records.',
      )
      return
    }

    if (!cleanInput) {
      void loadPharmacyPreview(submittedRawQuery || cleanSubmittedQuery, recallSort)
      return
    }

    void loadPharmacyPreview(cleanInput, recallSort, {
      updateUrl: true,
      skipIfCompleted: true,
    })
  }

  function handleSortChange(nextSort: RecallSort) {
    const cleanSubmittedQuery = normalizeSearchTerm(submittedQuery)
    if (nextSort === recallSort || !cleanSubmittedQuery || recallResults.length === 0) return

    setRecallSort(nextSort)
    void loadPharmacyPreview(submittedRawQuery || cleanSubmittedQuery, nextSort)
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
  const hasWrongCategoryOnly = Boolean(wrongCategorySuggestion && hasZeroResults)
  const loadedSourceNames = Array.from(
    new Set(
      [
        ...(recallData?.sources_checked?.map((source) => source.source_name) ?? []),
        recallData?.source_name,
        drugData?.source_name,
      ].filter((sourceName): sourceName is string => Boolean(sourceName)),
    ),
  )
  const sourceLabel =
    loadedSourceNames.length > 0
      ? loadedSourceNames.join(' + ')
      : 'openFDA enforcement + openFDA FAERS'
  const recallSortDisabled = loading || recallResults.length === 0

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
              <QueryTypeahead
                id="pharmacy-page-search"
                value={query}
                onChange={(nextQuery) => {
                  setQuery(nextQuery)
                  if (helper) setHelper('')
                }}
                area="pharmacy"
                placeholder="Search another drug, brand, ingredient, or product"
              />
              <button type="submit" disabled={loading}>
                {loading ? 'Checking...' : 'Search'}
              </button>
            </div>
          </form>

          <QueryNormalizationNotice
            rawQuery={submittedRawQuery}
            normalizedQuery={submittedQuery}
          />

          {wrongCategorySuggestion && !loading && (
            <div className="pharmacy-query-guidance">
              <aside className="safety-route-suggestion" aria-live="polite">
                <span>{wrongCategorySuggestion.message}</span>
                <button
                  type="button"
                  onClick={() => {
                    const routeQuery = normalizeSearchTerm(submittedQuery)
                    if (
                      getSearchComparisonKey(routeQuery) !==
                      getSearchComparisonKey(submittedRawQuery)
                    ) {
                      goToPage(
                        wrongCategorySuggestion.page,
                        routeQuery,
                        submittedRawQuery,
                      )
                      return
                    }

                    goToPage(wrongCategorySuggestion.page, routeQuery)
                  }}
                >
                  Open {wrongCategorySuggestion.label}
                </button>
              </aside>
            </div>
          )}

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

      {hasZeroResults && !hasWrongCategoryOnly && !loading && (
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
              <dd>
                {drugData
                  ? drugData.count > 0
                    ? drugData.intelligence_score.label
                    : 'No returned reports'
                  : 'Not available'}
              </dd>
            </div>
            <div>
              <dt>Review priority</dt>
              <dd>
                {drugData
                  ? drugData.count > 0
                    ? drugData.intelligence_score.review_priority
                    : 'Verify other sources'
                  : 'Not available'}
              </dd>
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

            <div className="recall-sort-wrapper">
              <div
                className="recall-sort-control"
                role="group"
                aria-label="Sort pharmacy recall records"
              >
                <button
                  type="button"
                  className={recallSort === 'score' ? 'active' : ''}
                  aria-pressed={recallSort === 'score'}
                  onClick={() => void handleSortChange('score')}
                  disabled={recallSortDisabled}
                >
                  Priority
                </button>

                <button
                  type="button"
                  className={recallSort === 'latest' ? 'active' : ''}
                  aria-pressed={recallSort === 'latest'}
                  onClick={() => void handleSortChange('latest')}
                  disabled={recallSortDisabled}
                >
                  Latest
                </button>
              </div>

              {!loading && recallResults.length === 0 && (
                <small className="sort-helper-text">
                  Search first to sort matching records.
                </small>
              )}
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
              <h3>
                {hasWrongCategoryOnly
                  ? `This looks better suited for ${wrongCategorySuggestion?.label}.`
                  : 'No matching recall records returned.'}
              </h3>
              <p>
                {hasWrongCategoryOnly
                  ? `Open ${wrongCategorySuggestion?.label} to review the more relevant public records for this search.`
                  : 'Try a generic name, brand, strength, active ingredient, or simpler product wording. No match does not prove a medication is safe.'}
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
              {drugData && drugData.count > 0 && (
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
                    <dd>
                      {drugData.count > 0
                        ? drugData.intelligence_score.label
                        : 'No returned reports'}
                    </dd>
                  </div>
                  <div>
                    <dt>Confidence</dt>
                    <dd>
                      {drugData.count > 0
                        ? drugData.intelligence_score.data_confidence
                        : 'Not assessable'}
                    </dd>
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
                                  Math.round((reaction.count / topReactionCount) * 100),
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
