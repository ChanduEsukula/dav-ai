import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  searchEverydaySafety,
  type EverydaySafetyRecord,
  type EverydaySafetySearchResponse,
  type EverydaySafetySort,
} from '../api/everydaySafety'
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

type FoodSafetyPageProps = {
  initialQuery: string
  initialRawQuery?: string
  goToPage: (page: ActivePage, query?: string, rawQuery?: string) => void
}

type FoodSearchOptions = {
  updateUrl?: boolean
  skipIfCompleted?: boolean
}

const foodExamples = ['Chicken', 'Protein powder', 'Peanut butter', 'Eggs', 'Lettuce']

function truncateText(value: string | null | undefined, maxLength = 92) {
  if (!value) return 'Product description unavailable'
  const normalizedValue = value.replace(/\s+/g, ' ').trim()
  if (normalizedValue.length <= maxLength) return normalizedValue
  return `${normalizedValue.slice(0, maxLength).trim()}...`
}

function sourceTypeLabel(
  sourceType: EverydaySafetyRecord['source_type'],
  sourceKind?: EverydaySafetyRecord['source_kind'],
) {
  if (sourceKind === 'normalized_public_notice') return 'Normalized public notice'
  if (sourceKind === 'public_notice') return 'Official public notice'
  if (sourceKind === 'structured_api') return 'Official API record'
  if (sourceType === 'FDA_NORMALIZED_PUBLIC_NOTICE') return 'Normalized public notice'
  return sourceType === 'USDA_FSIS_RECALL' ? 'USDA / FSIS recall' : 'FDA food enforcement'
}

function recordDate(record: EverydaySafetyRecord) {
  return record.recall_initiation_date || record.report_date
}

function FoodRecordRow({ record, index }: { record: EverydaySafetyRecord; index: number }) {
  const fullProductName = record.product_description || 'Product description unavailable'

  return (
    <details
      className="pharmacy-record-row food-record-row"
      key={`${record.record_id ?? record.recall_number ?? 'food-record'}-${index}`}
    >
      <summary>
        <span className="pharmacy-record-row__product">
          <span className="pharmacy-record-row__badges">
            <small>{record.classification || 'Unclassified'}</small>
            <small>{record.risk_score.label} review signal</small>
          </span>
          <strong title={fullProductName}>{truncateText(fullProductName)}</strong>
          <span>
            {record.recall_number ||
              record.record_id ||
              sourceTypeLabel(record.source_type, record.source_kind)}
          </span>
        </span>

        <span className="pharmacy-record-row__firm">
          <strong>{record.recalling_firm || 'Firm not listed'}</strong>
          <span>{record.status || 'Status not listed'}</span>
        </span>

        <span className="pharmacy-record-row__date">
          <strong>{formatDate(recordDate(record))}</strong>
          <span>{sourceTypeLabel(record.source_type, record.source_kind)}</span>
        </span>

        <span className="pharmacy-record-row__arrow" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </span>
      </summary>

      <div className="pharmacy-record-details food-record-details">
        <div className="pharmacy-record-details__wide">
          <span>Full product description</span>
          <strong>{fullProductName}</strong>
        </div>

        <div className="pharmacy-record-details__wide">
          <span>Reason</span>
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
          <span>Product quantity</span>
          <strong>{record.product_quantity || 'Not listed'}</strong>
        </div>

        <div className="pharmacy-record-details__wide">
          <span>Code or lot details</span>
          <strong>{record.code_info || 'Not listed'}</strong>
        </div>

        <div>
          <span>Source</span>
          <strong>{record.source.name}</strong>
        </div>

        <div>
          <span>Record type</span>
          <strong>{sourceTypeLabel(record.source_type, record.source_kind)}</strong>
        </div>

        {record.extraction_confidence && (
          <div>
            <span>Notice extraction</span>
            <strong>{record.extraction_confidence}</strong>
          </div>
        )}

        <div>
          <span>Retrieved</span>
          <strong>{formatTimestamp(record.source.retrieval_timestamp)}</strong>
        </div>

        <div className="pharmacy-record-details__wide">
          <span>Official source</span>
          <strong>
            {record.official_url ? (
              <a href={record.official_url} target="_blank" rel="noreferrer">
                Open official record
              </a>
            ) : (
              record.source.endpoint
            )}
          </strong>
        </div>
      </div>
    </details>
  )
}

function FoodSafetyPage({
  initialQuery,
  initialRawQuery,
  goToPage,
}: FoodSafetyPageProps) {
  const initialNormalization = normalizeSafetyQuery(
    initialRawQuery || initialQuery,
    'food',
  )
  const normalizedInitialQuery = initialNormalization.normalizedQuery
  const [query, setQuery] = useState(initialNormalization.rawQuery)
  const [submittedQuery, setSubmittedQuery] = useState(normalizedInitialQuery)
  const [submittedRawQuery, setSubmittedRawQuery] = useState(
    initialNormalization.rawQuery,
  )
  const [data, setData] = useState<EverydaySafetySearchResponse | null>(null)
  const [sort, setSort] = useState<EverydaySafetySort>('score')
  const [loading, setLoading] = useState(Boolean(normalizedInitialQuery))
  const [error, setError] = useState('')
  const [helper, setHelper] = useState('')
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

  const loadFoodRecords = useCallback(
    async (
      nextQuery: string,
      nextSort: EverydaySafetySort,
      options: FoodSearchOptions = {},
    ) => {
      const normalization = normalizeSafetyQuery(nextQuery, 'food')
      const cleanQuery = normalization.normalizedQuery
      if (!cleanQuery) return

      const requestKey = `${getSearchComparisonKey(cleanQuery)}::${nextSort}`
      if (inFlightKeyRef.current === requestKey) return

      if (options.skipIfCompleted && completedKeyRef.current === requestKey) {
        setQuery(normalization.rawQuery)
        setSubmittedQuery(cleanQuery)
        setSubmittedRawQuery(normalization.rawQuery)
        setError('')
        setHelper('')
        return
      }

      const requestId = requestIdRef.current + 1
      requestIdRef.current = requestId
      inFlightKeyRef.current = requestKey
      completedKeyRef.current = ''

      setQuery(normalization.rawQuery)
      setSubmittedQuery(cleanQuery)
      setSubmittedRawQuery(normalization.rawQuery)
      setData(null)
      setLoading(true)
      setError('')
      setHelper('')

      if (options.updateUrl) {
        writeSafetyQueryToUrl(
          PAGE_IDS.FOOD_SAFETY,
          cleanQuery,
          normalization.rawQuery,
          'push',
        )
      }

      try {
        const response = await searchEverydaySafety(
          cleanQuery,
          8,
          'food_supplement',
          nextSort,
        )

        if (!isMountedRef.current || requestId !== requestIdRef.current) return

        setData(response)
        completedKeyRef.current = requestKey
      } catch {
        if (isMountedRef.current && requestId === requestIdRef.current) {
          setError('Unable to load public records. Check backend/source availability.')
        }
      } finally {
        if (isMountedRef.current && requestId === requestIdRef.current) {
          inFlightKeyRef.current = ''
          setLoading(false)
        }
      }
    },
    [],
  )

  useEffect(() => {
    const normalization = normalizeSafetyQuery(
      initialRawQuery || initialQuery,
      'food',
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
        setData(null)
        setSort('score')
        setLoading(false)
        setError('')
        setHelper('')
        return
      }

      writeSafetyQueryToUrl(
        PAGE_IDS.FOOD_SAFETY,
        cleanQuery,
        normalization.rawQuery,
        'replace',
      )

      setSort('score')
      await loadFoodRecords(normalization.rawQuery, 'score', {
        skipIfCompleted: true,
      })
    }

    void syncInitialQuery()

    return () => {
      isCurrentEffect = false
    }
  }, [initialQuery, initialRawQuery, loadFoodRecords])

  function handleSearch() {
    const cleanInput = normalizeSearchTerm(query)
    const cleanSubmittedQuery = normalizeSearchTerm(submittedQuery)

    if (!cleanInput && !cleanSubmittedQuery) {
      setError('')
      setHelper(
        'Enter a food, supplement, brand, ingredient, or product wording to search public records.',
      )
      return
    }

    if (!cleanInput) {
      void loadFoodRecords(submittedRawQuery || cleanSubmittedQuery, sort)
      return
    }

    void loadFoodRecords(cleanInput, sort, {
      updateUrl: true,
      skipIfCompleted: true,
    })
  }

  function handleSortChange(nextSort: EverydaySafetySort) {
    const cleanSubmittedQuery = normalizeSearchTerm(submittedQuery)
    if (nextSort === sort || !cleanSubmittedQuery) return

    setSort(nextSort)
    void loadFoodRecords(submittedRawQuery || cleanSubmittedQuery, nextSort)
  }

  function handleExampleClick(example: string) {
    setQuery(example)
    setError('')
    setHelper('')
    void loadFoodRecords(example, sort, {
      updateUrl: true,
      skipIfCompleted: true,
    })
  }

  const records = data?.results ?? []
  const displayQuery = submittedQuery || 'a food or supplement product'
  const topResult = records[0] ?? null
  const wrongCategorySuggestion = useMemo(
    () => getWrongCategorySuggestion('food', submittedQuery),
    [submittedQuery],
  )
  const hasZeroResults = data?.count === 0 && !loading
  const hasWrongCategoryOnly = Boolean(wrongCategorySuggestion && hasZeroResults)
  const sourceNames = data?.sources_checked.map((source) => source.source_name) ?? []
  const sourceLabel =
    sourceNames.length > 0
      ? sourceNames.join(' + ')
      : 'FDA food enforcement + USDA / FSIS records'

  return (
    <section className="safety-area-page safety-area-page--food pharmacy-detail-page food-detail-page">
      <header className="pharmacy-overview food-overview">
        <div className="pharmacy-overview__main">
          <p className="eyebrow">Food & Supplement Safety</p>

          <h1>
            {submittedQuery ? (
              <>
                Safety review for <span>{submittedQuery}</span>
              </>
            ) : (
              'Search food and supplement safety records'
            )}
          </h1>

          <p className="pharmacy-overview__description">
            Compare public food, supplement, meat, poultry, and egg-product safety records.
          </p>

          <form
            className="pharmacy-page-search food-page-search"
            onSubmit={(event) => {
              event.preventDefault()
              handleSearch()
            }}
          >
            <label htmlFor="food-page-search">Search food safety records</label>
            <div>
              <QueryTypeahead
                id="food-page-search"
                value={query}
                onChange={(nextQuery) => {
                  setQuery(nextQuery)
                  if (helper) setHelper('')
                }}
                area="food"
                placeholder="Search another food, supplement, brand, or ingredient"
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

          <div className="pharmacy-example-row" aria-label="Example food safety searches">
            <span>Try</span>
            {foodExamples.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => handleExampleClick(example)}
              >
                {example}
              </button>
            ))}
          </div>

          <p className="pharmacy-source-line food-source-line">
            <span aria-hidden="true" />
            <strong>Public food records</strong>
            <span>{sourceLabel}</span>
            <span>Not a safety guarantee</span>
          </p>
        </div>
      </header>

      {loading && (
        <p className="safety-area-status" role="status" aria-live="polite">
          Checking food and supplement public records...
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

      {hasZeroResults && !hasWrongCategoryOnly && (
        <aside className="safety-search-guidance" aria-live="polite">
          <span>
            No public records returned for this exact search. Check spelling or try a
            simpler/generic term.
          </span>
        </aside>
      )}

      {data && (
        <section
          className="pharmacy-summary-strip food-summary-strip"
          aria-label={`Summary for ${displayQuery}`}
        >
          <div className="pharmacy-summary-strip__query">
            <small>Current query</small>
            <strong>{displayQuery}</strong>
            <span>Public records, not a product safety determination</span>
          </div>

          <dl className="pharmacy-summary-metrics">
            <div>
              <dt>Possible matches</dt>
              <dd>{data.count}</dd>
            </div>
            <div>
              <dt>Sources checked</dt>
              <dd>{data.sources_checked.length}</dd>
            </div>
            <div>
              <dt>Review focus</dt>
              <dd>{topResult?.risk_score.label ?? 'Verify'}</dd>
            </div>
            <div>
              <dt>Search strategy</dt>
              <dd title={data.search_strategy_used}>{data.search_strategy_used}</dd>
            </div>
          </dl>
        </section>
      )}

      <div className="pharmacy-workspace food-workspace">
        <section className="pharmacy-recall-panel food-record-panel" id="food-safety-records">
          <div className="pharmacy-panel-header">
            <div>
              <p className="eyebrow">Food records</p>
              <h2>Matched food records</h2>
              <span>
                {data
                  ? `Showing ${records.length} of ${data.count} returned record${
                      data.count === 1 ? '' : 's'
                    }`
                  : 'Search to load food and supplement records'}
              </span>
            </div>

            <div
              className="recall-sort-control"
              role="group"
              aria-label="Sort food safety records"
            >
              <button
                type="button"
                className={sort === 'score' ? 'active' : ''}
                aria-pressed={sort === 'score'}
                onClick={() => handleSortChange('score')}
                disabled={loading}
              >
                Priority
              </button>
              <button
                type="button"
                className={sort === 'latest' ? 'active' : ''}
                aria-pressed={sort === 'latest'}
                onClick={() => handleSortChange('latest')}
                disabled={loading}
              >
                Latest
              </button>
            </div>
          </div>

          {records.length > 0 ? (
            <div className="pharmacy-record-table" aria-label="Food safety search results">
              <div className="pharmacy-record-table__head" aria-hidden="true">
                <span>Product and record</span>
                <span>Firm and status</span>
                <span>Date and source</span>
                <span />
              </div>

              {records.map((record, index) => (
                <FoodRecordRow
                  key={`${record.record_id ?? record.recall_number ?? 'food-record'}-${index}`}
                  record={record}
                  index={index}
                />
              ))}
            </div>
          ) : data ? (
            <div className="pharmacy-empty-card food-empty-card">
              <h3>
                {hasWrongCategoryOnly
                  ? `This looks better suited for ${wrongCategorySuggestion?.label}.`
                  : 'No matching food or supplement records returned.'}
              </h3>
              <p>
                {hasWrongCategoryOnly
                  ? `Open ${wrongCategorySuggestion?.label} to review the more relevant public records for this search.`
                  : 'Check spelling or try a simpler product, brand, ingredient, or category term. No result does not prove a food or supplement is safe.'}
              </p>
            </div>
          ) : (
            <div className="pharmacy-empty-card pharmacy-empty-card--quiet">
              <h3>Food safety records will appear here.</h3>
              <p>Search above to compare possible public food and supplement matches.</p>
            </div>
          )}
        </section>

        <aside className="pharmacy-insight-rail">
          <section className="pharmacy-insight-card food-source-card">
            <div className="pharmacy-insight-card__header">
              <div>
                <p className="eyebrow">Source coverage</p>
                <h2>Public records checked</h2>
              </div>
              {data && <span className="food-source-count">{data.sources_checked.length}</span>}
            </div>

            {data ? (
              <div className="food-source-list">
                {data.sources_checked.map((source) => (
                  <article key={source.source_id}>
                    <div>
                      <strong>{source.source_name}</strong>
                      <span>{sourceTypeLabel(source.source_type, source.source_kind)}</span>
                    </div>
                    <dl>
                      <div>
                        <dt>Status</dt>
                        <dd>{source.upstream_status}</dd>
                      </div>
                      <div>
                        <dt>Records</dt>
                        <dd>{source.record_count}</dd>
                      </div>
                    </dl>
                    <p>{source.endpoint}</p>
                  </article>
                ))}
              </div>
            ) : (
              <p className="pharmacy-insight-card__empty">
                Search above to see which public sources were checked.
              </p>
            )}
          </section>

          <section className="pharmacy-safety-card food-verification-card">
            <div>
              <p className="eyebrow">Verification boundary</p>
              <h2>Verify the exact item before acting.</h2>
            </div>
            <ul>
              <li>Match brand, product, package, lot, and code details.</li>
              <li>Review firm, date, reason, and distribution.</li>
              <li>No result does not prove a food or supplement is safe.</li>
            </ul>
            <p className="pharmacy-safety-card__source">
              Public records only. This is not official recall instruction or a safety
              guarantee.
              {data && ` Retrieved ${formatTimestamp(data.retrieval_timestamp)}.`}
            </p>
          </section>
        </aside>
      </div>
    </section>
  )
}

export default FoodSafetyPage
