import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  buildCosmeticAssistantContext,
  type AssistantChatContext,
} from '../api/assistant'
import {
  searchCosmeticEvents,
  type CosmeticEventRecord,
  type CosmeticEventSearchResponse,
  type CosmeticProduct,
  type CosmeticRecallNotice,
} from '../api/cosmeticEvents'
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

type CosmeticSafetyPageProps = {
  initialQuery: string
  initialRawQuery?: string
  goToPage: (page: ActivePage, query?: string, rawQuery?: string) => void
  setAssistantContext?: (context: AssistantChatContext | null) => void
}

type CosmeticSearchOptions = {
  updateUrl?: boolean
  skipIfCompleted?: boolean
}

type CosmeticSort = 'score' | 'latest'

const cosmeticExamples = ['Sunscreen', 'Shampoo', 'Lipstick', 'Moisturizer', 'Hair dye']


function cosmeticDateValue(record: CosmeticEventRecord) {
  const raw = record.report_date || ''
  const digits = raw.replace(/\D/g, '')
  if (digits.length >= 8) return Number(digits.slice(0, 8))
  return 0
}

function cosmeticPriorityValue(record: CosmeticEventRecord) {
  const seriousBoost = String(record.serious || '').toLowerCase().startsWith('y') ? 100 : 0
  return seriousBoost + record.reactions.length * 10 + record.outcomes.length
}

function getCosmeticReportTitle(record: CosmeticEventRecord) {
  const product = record.products[0]

  return (
    product?.brand_name ||
    product?.name_brand ||
    product?.industry_name ||
    (record.report_number ? `Cosmetic report ${record.report_number}` : null) ||
    'Cosmetic event report'
  )
}

function productDetails(product: CosmeticProduct, index: number) {
  return {
    label:
      product.brand_name ||
      product.name_brand ||
      product.industry_name ||
      `Product ${index + 1}`,
    brand: product.brand_name || product.name_brand || 'Not listed',
    industry: product.industry_name || 'Not listed',
    industryCode: product.industry_code || 'Not listed',
  }
}

function truncateText(value: string | null | undefined, maxLength = 88) {
  if (!value) return 'Not listed'
  const normalizedValue = value.replace(/\s+/g, ' ').trim()
  if (normalizedValue.length <= maxLength) return normalizedValue
  return `${normalizedValue.slice(0, maxLength).trim()}...`
}

function compactList(values: string[], emptyLabel = 'Not listed') {
  if (values.length === 0) return emptyLabel
  return values.slice(0, 3).join(', ')
}


function getRecallNoticeTitle(notice: CosmeticRecallNotice) {
  return (
    notice.title ||
    notice.product_name ||
    notice.brand_name ||
    'FDA public recall or safety alert notice'
  )
}

function cosmeticNoticeSourceLabel(notice: CosmeticRecallNotice) {
  if (notice.source_kind === 'normalized_public_notice') {
    return 'Normalized public notice'
  }
  if (notice.source_kind === 'structured_api') return 'Official API record'
  return 'Official public notice'
}

function CosmeticRecallNoticeRow({
  notice,
  index,
}: {
  notice: CosmeticRecallNotice
  index: number
}) {
  const title = getRecallNoticeTitle(notice)

  return (
    <details
      className="pharmacy-record-row cosmetic-record-row"
      key={`${notice.source_name}-${notice.record_url ?? index}`}
    >
      <summary>
        <span className="pharmacy-record-row__product">
          <span className="pharmacy-record-row__badges">
            <small>{notice.category || 'FDA notice'}</small>
            <small>{cosmeticNoticeSourceLabel(notice)}</small>
          </span>
          <strong title={title}>{truncateText(title)}</strong>
          <span>{notice.brand_name || notice.product_name || 'Product details not listed'}</span>
        </span>

        <span className="pharmacy-record-row__firm">
          <strong>{notice.company_name || 'Company not listed'}</strong>
          <span>{notice.source_name}</span>
        </span>

        <span className="pharmacy-record-row__date">
          <strong>{formatDate(notice.published_date)}</strong>
          <span>{cosmeticNoticeSourceLabel(notice)}</span>
        </span>

        <span className="pharmacy-record-row__arrow" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </span>
      </summary>

      <div className="pharmacy-record-details cosmetic-record-details">
        <div className="pharmacy-record-details__wide">
          <span>Notice title</span>
          <strong>{title}</strong>
        </div>

        <div className="pharmacy-record-details__wide">
          <span>Reason / concern</span>
          <strong>{notice.reason || 'Not listed'}</strong>
        </div>

        {notice.remedy && (
          <div className="pharmacy-record-details__wide">
            <span>Remedy / action</span>
            <strong>{notice.remedy}</strong>
          </div>
        )}

        <div>
          <span>Product</span>
          <strong>{notice.product_name || 'Not listed'}</strong>
        </div>

        <div>
          <span>Brand</span>
          <strong>{notice.brand_name || 'Not listed'}</strong>
        </div>

        <div>
          <span>Company</span>
          <strong>{notice.company_name || 'Not listed'}</strong>
        </div>

        <div>
          <span>Source</span>
          <strong>{notice.source_name}</strong>
        </div>

        {notice.extraction_confidence && (
          <div>
            <span>Notice extraction</span>
            <strong>{notice.extraction_confidence}</strong>
          </div>
        )}

        {notice.record_url && (
          <div className="pharmacy-record-details__wide">
            <span>Official notice</span>
            <strong>
              <a href={notice.record_url} target="_blank" rel="noreferrer">
                Open FDA notice
              </a>
            </strong>
          </div>
        )}
      </div>
    </details>
  )
}

function CosmeticReportRow({
  record,
  index,
  sourceName,
  sourceEndpoint,
  retrievalTimestamp,
}: {
  record: CosmeticEventRecord
  index: number
  sourceName: string
  sourceEndpoint: string
  retrievalTimestamp: string
}) {
  const reportTitle = getCosmeticReportTitle(record)

  return (
    <details
      className="pharmacy-record-row cosmetic-record-row"
      key={`${record.report_number ?? 'cosmetic-report'}-${index}`}
    >
      <summary>
        <span className="pharmacy-record-row__product">
          <span className="pharmacy-record-row__badges">
            <small>{record.serious ? `Serious: ${record.serious}` : 'Serious not listed'}</small>
            <small>
              {record.reactions.length} reaction{record.reactions.length === 1 ? '' : 's'}
            </small>
          </span>
          <strong title={reportTitle}>{reportTitle}</strong>
          <span>{record.report_number || 'Report number not listed'}</span>
        </span>

        <span className="pharmacy-record-row__firm">
          <strong>{compactList(record.reactions)}</strong>
          <span>Top reported reactions</span>
        </span>

        <span className="pharmacy-record-row__date">
          <strong>{formatDate(record.report_date)}</strong>
          <span>{record.outcomes.length ? compactList(record.outcomes) : 'Outcome not listed'}</span>
        </span>

        <span className="pharmacy-record-row__arrow" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </span>
      </summary>

      <div className="pharmacy-record-details cosmetic-record-details">
        <div className="pharmacy-record-details__wide">
          <span>Reported reactions</span>
          <strong>{record.reactions.length ? record.reactions.join(', ') : 'Not listed'}</strong>
        </div>

        <div className="pharmacy-record-details__wide">
          <span>Reported outcomes</span>
          <strong>{record.outcomes.length ? record.outcomes.join(', ') : 'Not listed'}</strong>
        </div>

        <div>
          <span>Report number</span>
          <strong>{record.report_number || 'Not listed'}</strong>
        </div>

        <div>
          <span>Report date</span>
          <strong>{formatDate(record.report_date)}</strong>
        </div>

        <div>
          <span>Serious</span>
          <strong>{record.serious || 'Not listed'}</strong>
        </div>

        <div>
          <span>Products listed</span>
          <strong>{record.products.length}</strong>
        </div>

        <div className="pharmacy-record-details__wide cosmetic-product-details">
          <span>Product, brand, and industry details</span>
          {record.products.length > 0 ? (
            <div className="cosmetic-product-list">
              {record.products.map((product, productIndex) => {
                const details = productDetails(product, productIndex)

                return (
                  <article key={`${details.label}-${productIndex}`}>
                    <strong>{details.label}</strong>
                    <p>Brand: {details.brand}</p>
                    <p>Industry: {details.industry}</p>
                    <p>Industry code: {details.industryCode}</p>
                  </article>
                )
              })}
            </div>
          ) : (
            <strong>Not listed</strong>
          )}
        </div>

        <div>
          <span>Source</span>
          <strong>{sourceName}</strong>
        </div>

        <div>
          <span>Retrieved</span>
          <strong>{formatTimestamp(retrievalTimestamp)}</strong>
        </div>

        <div className="pharmacy-record-details__wide">
          <span>Source endpoint</span>
          <strong>{sourceEndpoint}</strong>
        </div>
      </div>
    </details>
  )
}

function CosmeticSafetyPage({
  initialQuery,
  initialRawQuery,
  goToPage,
  setAssistantContext,
}: CosmeticSafetyPageProps) {
  const initialNormalization = normalizeSafetyQuery(
    initialRawQuery || initialQuery,
    'cosmetic',
  )
  const normalizedInitialQuery = initialNormalization.normalizedQuery
  const [query, setQuery] = useState(initialNormalization.rawQuery)
  const [submittedQuery, setSubmittedQuery] = useState(normalizedInitialQuery)
  const [submittedRawQuery, setSubmittedRawQuery] = useState(
    initialNormalization.rawQuery,
  )
  const [data, setData] = useState<CosmeticEventSearchResponse | null>(null)
  const [sort, setSort] = useState<CosmeticSort>('score')
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

  const loadCosmeticReports = useCallback(
    async (nextQuery: string, options: CosmeticSearchOptions = {}) => {
      const normalization = normalizeSafetyQuery(nextQuery, 'cosmetic')
      const cleanQuery = normalization.normalizedQuery
      if (!cleanQuery) {
        setAssistantContext?.(null)
        return
      }

      const requestKey = getSearchComparisonKey(cleanQuery)
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
      setAssistantContext?.(null)

      if (options.updateUrl) {
        writeSafetyQueryToUrl(
          PAGE_IDS.COSMETIC_SAFETY,
          cleanQuery,
          normalization.rawQuery,
          'push',
        )
      }

      try {
        const response = await searchCosmeticEvents(cleanQuery, 8)

        if (!isMountedRef.current || requestId !== requestIdRef.current) return

        setData(response)
        if (response.count > 0) {
          setAssistantContext?.(buildCosmeticAssistantContext(response))
        } else {
          setAssistantContext?.(null)
        }
        completedKeyRef.current = requestKey
      } catch {
        if (isMountedRef.current && requestId === requestIdRef.current) {
          setAssistantContext?.(null)
          setError('Unable to load public records. Check backend/source availability.')
        }
      } finally {
        if (isMountedRef.current && requestId === requestIdRef.current) {
          inFlightKeyRef.current = ''
          setLoading(false)
        }
      }
    },
    [setAssistantContext],
  )

  useEffect(() => {
    const normalization = normalizeSafetyQuery(
      initialRawQuery || initialQuery,
      'cosmetic',
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
        setLoading(false)
        setError('')
        setHelper('')
        setAssistantContext?.(null)
        return
      }

      writeSafetyQueryToUrl(
        PAGE_IDS.COSMETIC_SAFETY,
        cleanQuery,
        normalization.rawQuery,
        'replace',
      )

      await loadCosmeticReports(normalization.rawQuery, { skipIfCompleted: true })
    }

    void syncInitialQuery()

    return () => {
      isCurrentEffect = false
    }
  }, [initialQuery, initialRawQuery, loadCosmeticReports, setAssistantContext])

  function handleSearch() {
    const cleanInput = normalizeSearchTerm(query)
    const cleanSubmittedQuery = normalizeSearchTerm(submittedQuery)

    if (!cleanInput && !cleanSubmittedQuery) {
      setError('')
      setAssistantContext?.(null)
      setHelper(
        'Enter a cosmetic, brand, ingredient, or personal-care product to search public reports.',
      )
      return
    }

    if (!cleanInput) {
      void loadCosmeticReports(submittedRawQuery || cleanSubmittedQuery)
      return
    }

    void loadCosmeticReports(cleanInput, {
      updateUrl: true,
      skipIfCompleted: true,
    })
  }

  function handleExampleClick(example: string) {
    setQuery(example)
    setError('')
    setHelper('')
    void loadCosmeticReports(example, {
      updateUrl: true,
      skipIfCompleted: true,
    })
  }

  const records = data?.records ?? []
  const sortedRecords = useMemo(() => {
    const nextRecords = [...records]

    if (sort === 'latest') {
      return nextRecords.sort(
        (first, second) => cosmeticDateValue(second) - cosmeticDateValue(first),
      )
    }

    return nextRecords.sort(
      (first, second) =>
        cosmeticPriorityValue(second) - cosmeticPriorityValue(first) ||
        cosmeticDateValue(second) - cosmeticDateValue(first),
    )
  }, [records, sort])
  const recallNotices = data?.recall_notices ?? []
  const displayQuery = submittedQuery || 'a cosmetic or personal-care product'
  const topReaction = data?.top_reactions[0] ?? null
  const topReactions = data?.top_reactions.slice(0, 5) ?? []
  const topReactionCount = Math.max(topReaction?.count ?? 0, 1)
  const wrongCategorySuggestion = useMemo(
    () => getWrongCategorySuggestion('cosmetic', submittedQuery),
    [submittedQuery],
  )
  const routeSuggestionLabel = wrongCategorySuggestion?.label
  const hasZeroReports = data?.count === 0 && !loading
  const hasWrongCategoryOnly = Boolean(wrongCategorySuggestion && hasZeroReports)

  return (
    <section className="safety-area-page safety-area-page--cosmetic pharmacy-detail-page cosmetic-detail-page">
      <header className="pharmacy-overview cosmetic-overview">
        <div className="pharmacy-overview__main">
          <p className="eyebrow">Cosmetic Safety</p>

          <h1>
            {submittedQuery ? (
              <>
                Safety review for <span>{submittedQuery}</span>
              </>
            ) : (
              'Search cosmetic safety records'
            )}
          </h1>

          <p className="pharmacy-overview__description">
            Review public cosmetic-event reports and FDA recall or safety alert notices in one place.
          </p>

          <form
            className="pharmacy-page-search cosmetic-page-search"
            onSubmit={(event) => {
              event.preventDefault()
              handleSearch()
            }}
          >
            <label htmlFor="cosmetic-page-search">Search cosmetic safety records</label>
            <div>
              <QueryTypeahead
                id="cosmetic-page-search"
                value={query}
                onChange={(nextQuery) => {
                  setQuery(nextQuery)
                  if (helper) setHelper('')
                }}
                area="cosmetic"
                placeholder="Search cosmetic, brand, ingredient, or personal-care product"
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
                <span>
                  This looks more like a {routeSuggestionLabel} search. Open{' '}
                  {routeSuggestionLabel} for better results?
                </span>
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
                  Open {routeSuggestionLabel}
                </button>
              </aside>
            </div>
          )}

          <div className="pharmacy-example-row" aria-label="Example cosmetic searches">
            <span>Try</span>
            {cosmeticExamples.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => handleExampleClick(example)}
              >
                {example}
              </button>
            ))}
          </div>

          <p className="pharmacy-source-line cosmetic-source-line">
            <span aria-hidden="true" />
            <strong>Public FDA records</strong>
            <span>Cosmetic event reports + FDA notices</span>
            <span>Signal, not proof</span>
          </p>
        </div>
      </header>

      {loading && (
        <p className="safety-area-status" role="status" aria-live="polite">
          Checking cosmetic-event public reports...
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

      {hasZeroReports && !hasWrongCategoryOnly && (
        <aside className="safety-search-guidance" aria-live="polite">
          <span>
            No cosmetic-event reports returned for this exact search. Check spelling or try a simpler
            brand/product term.
          </span>
        </aside>
      )}

      {data && (
        <section
          className="pharmacy-summary-strip cosmetic-summary-strip"
          aria-label={`Summary for ${displayQuery}`}
        >
          <div className="pharmacy-summary-strip__query">
            <small>Current query</small>
            <strong>{displayQuery}</strong>
            <span>Public event reports and FDA notices, not a safety guarantee</span>
          </div>

          <dl className="pharmacy-summary-metrics">
            <div>
              <dt>Public reports</dt>
              <dd>{data.count}</dd>
            </div>
            <div>
              <dt>Top reaction</dt>
              <dd title={topReaction?.reaction}>{topReaction?.reaction ?? 'None returned'}</dd>
            </div>
            <div>
              <dt>Review signal</dt>
              <dd>{data.count > 0 ? data.signal_score.label : 'No returned reports'}</dd>
            </div>
            <div>
              <dt>Recall / alerts</dt>
              <dd>{recallNotices.length}</dd>
            </div>
          </dl>
        </section>
      )}

      <div className="pharmacy-workspace cosmetic-workspace">
        <section
          className="pharmacy-recall-panel cosmetic-record-panel"
          id="cosmetic-event-reports"
        >
          <div className="pharmacy-panel-header">
            <div>
              <p className="eyebrow">Event reports</p>
              <h2>Matched cosmetic reports</h2>
              <span>
                {data
                  ? `Showing ${records.length} of ${data.count} returned report${
                      data.count === 1 ? '' : 's'
                    }`
                  : 'Search to load cosmetic-event reports'}
              </span>
            </div>

            <div className="recall-sort-control" aria-label="Sort cosmetic reports">
              <button
                type="button"
                className={sort === 'score' ? 'active' : ''}
                aria-pressed={sort === 'score'}
                disabled={!data || records.length === 0 || loading}
                onClick={() => setSort('score')}
              >
                Priority
              </button>
              <button
                type="button"
                className={sort === 'latest' ? 'active' : ''}
                aria-pressed={sort === 'latest'}
                disabled={!data || records.length === 0 || loading}
                onClick={() => setSort('latest')}
              >
                Latest
              </button>
            </div>
          </div>

          {records.length > 0 && data ? (
            <div className="pharmacy-record-table" aria-label="Cosmetic event search results">
              <div className="pharmacy-record-table__head" aria-hidden="true">
                <span>Product and report</span>
                <span>Reactions</span>
                <span>Date and outcome</span>
                <span />
              </div>

              {sortedRecords.map((record, index) => (
                <CosmeticReportRow
                  key={`${record.report_number ?? 'cosmetic-report'}-${index}`}
                  record={record}
                  index={index}
                  sourceName={data.source_name}
                  sourceEndpoint={data.endpoint}
                  retrievalTimestamp={data.retrieval_timestamp}
                />
              ))}
            </div>
          ) : data ? (
            <div className="pharmacy-empty-card cosmetic-empty-card">
              <h3>
                {hasWrongCategoryOnly
                  ? `This looks better suited for ${routeSuggestionLabel}.`
                  : 'No matching cosmetic-event reports returned.'}
              </h3>
              <p>
                {hasWrongCategoryOnly
                  ? `Open ${routeSuggestionLabel} to review the more relevant public records for this search.`
                  : 'Try a simpler brand, product, ingredient, or personal-care category. No result does not prove a cosmetic is safe.'}
              </p>
            </div>
          ) : (
            <div className="pharmacy-empty-card pharmacy-empty-card--quiet">
              <h3>Cosmetic-event reports will appear here.</h3>
              <p>Search above to review public reports, reactions, outcomes, and product context.</p>
            </div>
          )}

          {data && (
            <div className="cosmetic-recall-notice-section">
              <div className="pharmacy-panel-header">
                <div>
                  <p className="eyebrow">Recall / safety alerts</p>
                  <h2>FDA public notices</h2>
                  <span>
                    {recallNotices.length > 0
                      ? `Showing ${recallNotices.length} matching public notice${
                          recallNotices.length === 1 ? '' : 's'
                        }`
                      : 'No FDA public recall or safety alert notices matched this search'}
                  </span>
                </div>
              </div>

              {recallNotices.length > 0 ? (
                <div className="pharmacy-record-table" aria-label="Cosmetic FDA recall and alert notices">
                  <div className="pharmacy-record-table__head" aria-hidden="true">
                    <span>Notice and product</span>
                    <span>Company</span>
                    <span>Date</span>
                    <span />
                  </div>

                  {recallNotices.map((notice, index) => (
                    <CosmeticRecallNoticeRow
                      key={`${notice.source_name}-${notice.record_url ?? index}`}
                      notice={notice}
                      index={index}
                    />
                  ))}
                </div>
              ) : (
                <div className="pharmacy-empty-card pharmacy-empty-card--quiet">
                  <h3>No matching FDA public notices.</h3>
                  <p>
                    This does not prove the product is safe. It only means this public
                    FDA notice source did not return a matching notice for the exact search.
                  </p>
                </div>
              )}
            </div>
          )}

        </section>

        <aside className="pharmacy-insight-rail">
          <section className="pharmacy-insight-card cosmetic-signal-card">
            <div className="pharmacy-insight-card__header">
              <div>
                <p className="eyebrow">Signal summary</p>
                <h2>{hasZeroReports ? 'No returned-report signal' : 'Public reporting pattern'}</h2>
              </div>
              {data && (
                <span className="cosmetic-signal-badge">
                  {data.count > 0 ? `${data.signal_score.score}/100` : 'No reports'}
                </span>
              )}
            </div>

            {data ? (
              <>
                <dl className="pharmacy-event-metrics cosmetic-signal-metrics">
                  <div>
                    <dt>Signal</dt>
                    <dd>{data.count > 0 ? data.signal_score.label : 'No returned reports'}</dd>
                  </div>
                  <div>
                    <dt>Priority</dt>
                    <dd>
                      {data.count > 0
                        ? data.signal_score.review_priority
                        : 'Verify other sources'}
                    </dd>
                  </div>
                  <div>
                    <dt>Confidence</dt>
                    <dd>
                      {data.count > 0 ? data.signal_score.data_confidence : 'Not assessable'}
                    </dd>
                  </div>
                  <div>
                    <dt>Top concentration</dt>
                    <dd>
                      {data.count > 0
                        ? `${data.signal_score.top_reaction_concentration}%`
                        : 'N/A'}
                    </dd>
                  </div>
                </dl>

                <div className="pharmacy-reaction-summary">
                  <div className="pharmacy-subsection-heading">
                    <strong>Top reported reactions</strong>
                    <span>Count in returned reports</span>
                  </div>

                  {topReactions.length > 0 ? (
                    <div className="pharmacy-reaction-list cosmetic-reaction-list">
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
                    <p className="pharmacy-insight-card__empty">
                      No top reactions returned for this search.
                    </p>
                  )}
                </div>

                <div className="cosmetic-limitations">
                  <strong>Signal limitations</strong>
                  {data.signal_score.limitations.length > 0 ? (
                    <ul>
                      {data.signal_score.limitations.map((limitation) => (
                        <li key={limitation}>{limitation}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>No additional limitations were returned.</p>
                  )}
                </div>
              </>
            ) : (
              <p className="pharmacy-insight-card__empty">
                Search above to load signal context and leading reactions.
              </p>
            )}
          </section>

          <section className="pharmacy-safety-card cosmetic-boundary-card">
            <div>
              <p className="eyebrow">Source boundary</p>
              <h2>Interpret reports as signals, not proof.</h2>
            </div>
            <ul>
              <li>Reports may be incomplete, delayed, duplicated, or influenced by reporting.</li>
              <li>Reported reactions do not prove product causation.</li>
              <li>Review product, report date, reactions, outcomes, and source context.</li>
            </ul>
            <p className="pharmacy-safety-card__source">
              Public reports only. Reported reactions do not prove product causation. This is not
              medical advice, diagnosis, or official safety guidance.
              {data &&
                ` Retrieved ${formatTimestamp(data.retrieval_timestamp)} from ${data.source_name}.`}
            </p>
          </section>
        </aside>
      </div>
    </section>
  )
}

export default CosmeticSafetyPage
