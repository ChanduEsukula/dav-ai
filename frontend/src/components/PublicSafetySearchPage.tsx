import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  searchRealWorldSafety,
  type RealWorldSafetyRecord,
  type RealWorldSafetySearchResponse,
  type RealWorldSafetySort,
  type RealWorldSafetySourceRole,
} from '../api/realWorldSafety'
import { PAGE_IDS } from '../types/navigation'
import { getSearchComparisonKey, normalizeSearchTerm } from '../utils/queryNormalization'
import { formatDate } from '../utils/recallFormatters'
import { writeSafetyQueryToUrl } from '../utils/safetyQueryUrl'
import QueryTypeahead from './QueryTypeahead'

type PublicSafetySearchPageProps = {
  initialQuery: string
  initialRawQuery?: string
}

type SearchOptions = {
  updateUrl?: boolean
  skipIfCompleted?: boolean
}

const exampleQueries = [
  'tire',
  'scooter',
  'air fryer',
  'car seat',
  'battery',
  'NDC 66715 6547',
  'Advil',
  'tylonal',
  'blood sugar monitor',
]

const DEFAULT_LIMIT = 10

const clarificationOptions = [
  'Consumer product recall',
  'Drug / OTC label',
  'Food or supplement',
  'Cosmetic product',
  'Medical device',
  'Vehicle',
]

const roleOrder: RealWorldSafetySourceRole[] = [
  'recall_enforcement',
  'reference_identity',
  'label_reference',
  'signal_report',
  'other',
]

const roleCopy: Record<
  RealWorldSafetySourceRole,
  { label: string; shortLabel: string; description: string }
> = {
  recall_enforcement: {
    label: 'Recall / enforcement',
    shortLabel: 'Recall',
    description: 'Official recall, enforcement, public notice, or safety action records.',
  },
  reference_identity: {
    label: 'Reference identity',
    shortLabel: 'Reference',
    description: 'Drug, NDC, VIN, or identity records used to confirm what the item is.',
  },
  label_reference: {
    label: 'Label reference',
    shortLabel: 'Label',
    description: 'Official drug label or SPL context, not a recall by itself.',
  },
  signal_report: {
    label: 'Signal reports',
    shortLabel: 'Signal',
    description: 'Public adverse-event signals. These are not recalls or proof of causation.',
  },
  other: {
    label: 'Other',
    shortLabel: 'Other',
    description: 'Sources that do not fit the primary source roles.',
  },
}

function displayValue(value: string | null | undefined, fallback = 'Not listed') {
  const cleanValue = value?.trim()
  return cleanValue || fallback
}

function displayList(values: string[] | undefined, fallback = 'None listed') {
  if (!values?.length) return fallback
  return values.join(', ')
}

function formatQueryType(value: string) {
  return value.replace(/_/g, ' ')
}

function quoteTerms(values: string[]) {
  return values.map((value) => `"${value}"`).join(', ')
}

function normalizeSentence(value: string) {
  return value.trim().replace(/\s+/g, ' ').toLocaleLowerCase('en-US')
}

function getVisibleSuggestedSteps(data: RealWorldSafetySearchResponse) {
  const summary = data.safety_intelligence_summary
  const expansionKeys = new Set(
    summary.expansion_explanations.map((explanation) => normalizeSentence(explanation)),
  )
  const seen = new Set<string>()

  return summary.suggested_next_steps.filter((step) => {
    const key = normalizeSentence(step)
    if (!key || expansionKeys.has(key) || seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function truncateText(value: string, maxLength = 320) {
  const normalizedValue = value.replace(/\s+/g, ' ').trim()
  if (normalizedValue.length <= maxLength) {
    return {
      text: normalizedValue,
      truncated: false,
    }
  }

  return {
    text: `${normalizedValue.slice(0, maxLength).trim()}...`,
    truncated: true,
  }
}

function getRecordTitle(record: RealWorldSafetyRecord) {
  return (
    record.title ||
    record.product_name ||
    record.brand_name ||
    record.company_name ||
    'Public safety record'
  )
}

function createSourceRoleLookup(data: RealWorldSafetySearchResponse | null) {
  const lookup = new Map<string, RealWorldSafetySourceRole>()
  if (!data) return lookup

  for (const role of roleOrder) {
    const matchedSources =
      data.safety_intelligence_summary.matched_sources_by_role[role] ?? []
    const checkedSources =
      data.safety_intelligence_summary.checked_sources_by_role[role] ?? []

    for (const sourceName of [...matchedSources, ...checkedSources]) {
      lookup.set(sourceName, role)
    }
  }

  return lookup
}

function SourceBadge({
  role,
  children,
}: {
  role: RealWorldSafetySourceRole
  children: string
}) {
  return (
    <span className={`public-safety-badge public-safety-badge--${role}`}>
      {children}
    </span>
  )
}

function CollapsiblePanel({
  eyebrow,
  title,
  className = '',
  children,
}: {
  eyebrow: string
  title: string
  className?: string
  children: ReactNode
}) {
  return (
    <details className={`public-safety-disclosure ${className}`}>
      <summary>
        <span>
          <small>{eyebrow}</small>
          <strong>{title}</strong>
        </span>
        <em>Show</em>
      </summary>
      <div className="public-safety-disclosure__body">{children}</div>
    </details>
  )
}

function QueryUnderstandingCard({
  data,
}: {
  data: RealWorldSafetySearchResponse
}) {
  const understanding = data.query_understanding
  const identifiers = understanding.detected_identifiers
  const detectedIdentifierEntries = (['vin', 'ndc', 'upc'] as const)
    .map((identifier) => ({
      identifier,
      value: identifiers[identifier],
    }))
    .filter((entry) => Boolean(entry.value))
  const helpfulExpansion = understanding.expansion_search_terms_used.length
    ? `Dav AI also checked ${quoteTerms(understanding.expansion_search_terms_used)} because it is a known related search term for the original query.`
    : understanding.expanded_terms.length
      ? `Dav AI recognized ${quoteTerms(understanding.expanded_terms)} as related search context, but those terms did not add extra records in this response.`
      : 'Dav AI used the normalized query without extra expansion terms.'

  return (
    <CollapsiblePanel
      eyebrow="Technical details"
      title="Query understanding"
      className="public-safety-query-understanding"
    >
      <p className="public-safety-insight-note">{helpfulExpansion}</p>

      <div className="public-safety-detail-grid">
        <div>
          <small>Raw query</small>
          <strong>{displayValue(data.raw_query, 'None')}</strong>
        </div>
        <div>
          <small>Normalized query</small>
          <strong>{displayValue(understanding.normalized_query, 'None')}</strong>
        </div>
        <div>
          <small>Search query</small>
          <strong>{displayValue(understanding.search_query, 'None')}</strong>
        </div>
        <div>
          <small>Type hints</small>
          <strong>
            {understanding.query_type_hints.length
              ? understanding.query_type_hints.map(formatQueryType).join(', ')
              : 'Unknown'}
          </strong>
        </div>
      </div>

      <div className="public-safety-chip-block">
        <small>Corrections applied</small>
        <div className="public-safety-chip-row">
          {understanding.corrections_applied.length ? (
            understanding.corrections_applied.map((correction) => (
              <span key={correction}>{correction}</span>
            ))
          ) : (
            <span>No correction needed</span>
          )}
        </div>
      </div>

      <div className="public-safety-chip-grid">
        <div className="public-safety-chip-block">
          <small>Expanded terms</small>
          <div className="public-safety-chip-row">
            {understanding.expanded_terms.length ? (
              understanding.expanded_terms.map((term) => <span key={term}>{term}</span>)
            ) : (
              <span>No expansion terms</span>
            )}
          </div>
        </div>

        <div className="public-safety-chip-block">
          <small>Expansion terms used</small>
          <div className="public-safety-chip-row">
            {understanding.expansion_search_terms_used.length ? (
              understanding.expansion_search_terms_used.map((term) => (
                <span key={term}>{term}</span>
              ))
            ) : (
              <span>No expansion records added</span>
            )}
          </div>
        </div>
      </div>

      {detectedIdentifierEntries.length > 0 && (
        <div className="public-safety-identifiers">
          {detectedIdentifierEntries.map(({ identifier, value }) => (
            <div key={identifier}>
              <small>{identifier.toUpperCase()}</small>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      )}
    </CollapsiblePanel>
  )
}

function formatPublicSafetyDate(value: string | null | undefined) {
  if (!value) return 'Date not listed'

  const parsed = new Date(value)
  if (!Number.isNaN(parsed.getTime())) {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(parsed)
  }

  return formatDate(value)
}

function SearchOutcomeCard({
  data,
}: {
  data: RealWorldSafetySearchResponse
}) {
  if (!data.search_plan.clarification_required) return null

  return (
    <section className="public-safety-panel public-safety-outcome-card">
      <div className="public-safety-section-heading">
        <span>Search needs a category</span>
        <h2>Choose a safety area to continue</h2>
      </div>

      <p className="public-safety-summary-text">
        This query could belong to multiple safety categories, so Dav AI did not run a
        broad source sweep. Choose the closest safety area to check the right official
        sources.
      </p>

      <div className="public-safety-list-block public-safety-clarification-options">
        <small>Choose one category</small>
        <div className="public-safety-chip-row">
          {clarificationOptions.map((option) => (
            <button key={option} type="button">
              {option}
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}

function PublicSafetySummaryStrip({
  data,
  submittedQuery,
}: {
  data: RealWorldSafetySearchResponse
  submittedQuery: string
}) {
  const sourcesChecked = data.search_plan.clarification_required
    ? 'Not checked yet'
    : data.sources_checked.length

  return (
    <section
      className="public-safety-summary-strip"
      aria-label={`Summary for ${submittedQuery}`}
    >
      <div className="public-safety-summary-strip__query">
        <small>Current query</small>
        <strong>{submittedQuery}</strong>
        <span>Public records, not a personal safety determination</span>
      </div>

      <dl className="public-safety-summary-metrics">
        <div>
          <dt>Detected area</dt>
          <dd>{formatQueryType(data.search_plan.intent)}</dd>
        </div>
        <div>
          <dt>Matches</dt>
          <dd>{data.total_matches}</dd>
        </div>
        <div>
          <dt>Sources checked</dt>
          <dd>{sourcesChecked}</dd>
        </div>
        <div className={data.sources_failed.length > 0 ? 'has-issues' : ''}>
          <dt>Source issues</dt>
          <dd>{data.sources_failed.length}</dd>
        </div>
      </dl>
    </section>
  )
}

function PublicSafetyDownloadCard() {
  return (
    <div className="public-safety-download-action" aria-label="Export results">
      <span>
        <small>Export</small>
        <strong>Download Excel</strong>
      </span>
      <button type="button" disabled aria-label="Download Excel">
        <svg viewBox="0 0 24 24" focusable="false" aria-hidden="true">
          <path d="M12 3v11m0 0 4-4m-4 4-4-4M5 19h14" />
        </svg>
      </button>
    </div>
  )
}

function SourceRolesPanel({
  data,
}: {
  data: RealWorldSafetySearchResponse
}) {
  const summary = data.safety_intelligence_summary

  return (
    <CollapsiblePanel
      eyebrow="Source roles"
      title="Matched sources by evidence type"
      className="public-safety-source-roles"
    >
      <div className="public-safety-role-grid">
        {roleOrder.map((role) => {
          const matchedSources = summary.matched_sources_by_role[role] ?? []
          const checkedSources = summary.checked_sources_by_role[role] ?? []
          const checkedOnly = checkedSources.filter(
            (source) => !matchedSources.includes(source),
          )

          return (
            <article key={role} className={`public-safety-role public-safety-role--${role}`}>
              <div>
                <SourceBadge role={role}>{roleCopy[role].shortLabel}</SourceBadge>
                <h3>{roleCopy[role].label}</h3>
                <p>{roleCopy[role].description}</p>
              </div>

              <div className="public-safety-source-list">
                {matchedSources.length ? (
                  matchedSources.map((sourceName) => (
                    <span key={sourceName}>{sourceName}</span>
                  ))
                ) : (
                  <span>No matched source in this role</span>
                )}
              </div>

              {checkedOnly.length > 0 && (
                <small className="public-safety-checked-only">
                  Also checked: {checkedOnly.join(', ')}
                </small>
              )}
            </article>
          )
        })}
      </div>
    </CollapsiblePanel>
  )
}

function SourceCoveragePanel({
  data,
}: {
  data: RealWorldSafetySearchResponse
}) {
  return (
    <CollapsiblePanel
      eyebrow="Source coverage"
      title="Sources checked for this search"
      className="public-safety-source-coverage"
    >
      <div className="public-safety-coverage-grid">
        {data.sources_checked.map((source) => (
          <div key={`${source.source_id}-${source.source_name}`}>
            <small>{source.upstream_status}</small>
            <strong>{source.source_name}</strong>
            <span>
              {source.record_count} records | {source.source_type}
            </span>
          </div>
        ))}
      </div>

      {data.sources_failed.length > 0 && (
        <div className="public-safety-failed-sources">
          <small>Sources with issues</small>
          {data.sources_failed.map((source) => (
            <p key={`${source.source_id}-${source.reason}`}>
              <strong>{source.source_name}:</strong> {source.reason}
            </p>
          ))}
        </div>
      )}
    </CollapsiblePanel>
  )
}

function PublicSafetyInterpretationCard({
  data,
}: {
  data: RealWorldSafetySearchResponse
}) {
  const visibleSuggestedSteps = getVisibleSuggestedSteps(data).slice(0, 2)

  return (
    <section className="public-safety-rail-card public-safety-interpretation-card">
      <div>
        <span className="public-safety-eyebrow">What to verify next</span>
        <h2>Use the returned records as a starting point.</h2>
      </div>

      <p>{data.safety_intelligence_summary.plain_language_summary}</p>

      {visibleSuggestedSteps.length > 0 && (
        <ul>
          {visibleSuggestedSteps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ul>
      )}

      <p className="public-safety-primary-caveat">
        Public records only. Not a safety guarantee. Verify official sources.
      </p>
    </section>
  )
}

function PublicSafetyAdvancedDetails({
  data,
}: {
  data: RealWorldSafetySearchResponse
}) {
  return (
    <CollapsiblePanel
      eyebrow="Optional technical context"
      title="Advanced source details"
      className="public-safety-advanced-details"
    >
      <div className="public-safety-advanced-details__stack">
        <section className="public-safety-advanced-summary">
          <div className="public-safety-detail-grid">
            <div>
              <small>Detected intent</small>
              <strong>{formatQueryType(data.search_plan.intent)}</strong>
            </div>
            <div>
              <small>Confidence</small>
              <strong>{formatQueryType(data.search_plan.confidence)}</strong>
            </div>
            <div>
              <small>Planned sources</small>
              <strong>{data.search_plan.sources_to_check.length}</strong>
            </div>
            <div>
              <small>Clarification required</small>
              <strong>{data.search_plan.clarification_required ? 'Yes' : 'No'}</strong>
            </div>
          </div>
          <p>{data.search_plan.reason}</p>
        </section>

        <QueryUnderstandingCard data={data} />
        <SourceRolesPanel data={data} />
        <SourceCoveragePanel data={data} />

        <section className="public-safety-advanced-boundary">
          <h3>Public data boundary</h3>
          <p>{data.public_data_disclaimer}</p>
          {data.limitations.length > 0 && (
            <ul>
              {data.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </CollapsiblePanel>
  )
}

function publicSafetyRoleLabel(role: RealWorldSafetySourceRole) {
  switch (role) {
    case 'recall_enforcement':
      return 'Recall / enforcement'
    case 'reference_identity':
      return 'Reference'
    case 'label_reference':
      return 'Label'
    case 'signal_report':
      return 'Signal report'
    default:
      return 'Public record'
  }
}

function publicSafetyCategoryLabel(record: RealWorldSafetyRecord) {
  return formatQueryType(record.category || record.source_type || 'Public record')
}

function ResultCard({
  record,
  role,
}: {
  record: RealWorldSafetyRecord
  role: RealWorldSafetySourceRole
}) {
  const title = getRecordTitle(record)
  const reasonText = displayValue(
    record.reason || record.hazard_type,
    'No reason listed',
  )
  const remedyText = displayValue(record.remedy, 'No remedy listed')
  const sourceOrCompany = record.company_name || record.source_name || 'Source not listed'

  return (
    <details
      className={`pharmacy-record-row public-safety-record-row public-safety-record-row--${role}`}
      key={record.raw_payload_hash}
    >
      <summary aria-label="Show details">
        <span className="pharmacy-record-row__product">
          <span className="pharmacy-record-row__badges">
            <small>{publicSafetyCategoryLabel(record)}</small>
            <small>{publicSafetyRoleLabel(role)}</small>
          </span>
          <strong title={title}>{truncateText(title, 96).text}</strong>
          <span>{record.recall_number || record.product_name || 'Record ID not listed'}</span>
        </span>

        <span className="pharmacy-record-row__firm">
          <strong>{sourceOrCompany}</strong>
          <span>{record.source_name}</span>
        </span>

        <span className="pharmacy-record-row__date">
          <strong>{formatPublicSafetyDate(record.published_date)}</strong>
          <span>{record.source_kind === 'public_notice' ? 'Public notice' : 'Structured API'}</span>
        </span>

        <span className="pharmacy-record-row__arrow" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </span>
      </summary>

      <div className="pharmacy-record-details public-safety-record-details">
        <div className="pharmacy-record-details__wide">
          <span>Reason / hazard</span>
          <strong>{reasonText}</strong>
        </div>

        <div className="pharmacy-record-details__wide">
          <span>Remedy / use</span>
          <strong>{remedyText}</strong>
        </div>

        <div>
          <span>Product</span>
          <strong>{displayValue(record.product_name)}</strong>
        </div>

        <div>
          <span>Brand</span>
          <strong>{displayValue(record.brand_name)}</strong>
        </div>

        <div>
          <span>Company</span>
          <strong>{displayValue(record.company_name)}</strong>
        </div>

        <div>
          <span>Recall / record number</span>
          <strong>{displayValue(record.recall_number)}</strong>
        </div>

        {(record.affected_models?.length ?? 0) > 0 && (
          <div className="pharmacy-record-details__wide">
            <span>Affected models</span>
            <strong>{displayList(record.affected_models)}</strong>
          </div>
        )}

        {(record.affected_lots?.length ?? 0) > 0 && (
          <div className="pharmacy-record-details__wide">
            <span>Affected lots</span>
            <strong>{displayList(record.affected_lots)}</strong>
          </div>
        )}

        <div>
          <span>Source</span>
          <strong>{record.source_name}</strong>
        </div>

        <div>
          <span>Source type</span>
          <strong>{record.source_kind === 'public_notice' ? 'Public notice' : 'Structured API'}</strong>
        </div>

        {record.record_url && (
          <div className="pharmacy-record-details__wide">
            <span>Official record</span>
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

function ResultsList({
  data,
  roleLookup,
  submittedQuery,
  sort,
  sortDisabled,
  handleSortChange,
}: {
  data: RealWorldSafetySearchResponse
  roleLookup: Map<string, RealWorldSafetySourceRole>
  submittedQuery: string
  sort: RealWorldSafetySort
  sortDisabled: boolean
  handleSortChange: (nextSort: RealWorldSafetySort) => void
}) {
  if (data.search_plan.clarification_required) {
    return null
  }

  if (data.total_matches === 0) {
    return (
      <section className="public-safety-panel public-safety-no-results">
        <div className="public-safety-section-heading">
          <span>No returned records</span>
          <h2>Showing results for: {submittedQuery}</h2>
        </div>

        <p>{data.no_match_explanation}</p>
      </section>
    )
  }

  return (
    <section className="public-safety-results">
      <div className="public-safety-results-header">
        <div className="public-safety-section-heading">
          <span>Returned records</span>
          <h2>Showing results for: {submittedQuery}</h2>
        </div>

        <div className="recall-sort-control" aria-label="Sort public safety records">
          <button
            type="button"
            className={sort === 'score' ? 'active' : ''}
            aria-pressed={sort === 'score'}
            disabled={sortDisabled}
            onClick={() => handleSortChange('score')}
          >
            Priority
          </button>
          <button
            type="button"
            className={sort === 'latest' ? 'active' : ''}
            aria-pressed={sort === 'latest'}
            disabled={sortDisabled}
            onClick={() => handleSortChange('latest')}
          >
            Latest
          </button>
        </div>
      </div>

      <div className="pharmacy-record-table public-safety-record-table">
        <div className="pharmacy-record-table__head" aria-hidden="true">
          <span>Record and product</span>
          <span>Source / company</span>
          <span>Date</span>
          <span />
        </div>

        {data.results.map((record, index) => (
          <ResultCard
            key={`${record.source_name}-${record.raw_payload_hash}-${index}`}
            record={record}
            role={roleLookup.get(record.source_name) ?? 'other'}
          />
        ))}
      </div>
    </section>
  )
}

function PublicSafetySearchPage({
  initialQuery,
  initialRawQuery,
}: PublicSafetySearchPageProps) {
  const initialSearchTerm = normalizeSearchTerm(initialRawQuery || initialQuery)
  const [query, setQuery] = useState(initialSearchTerm)
  const [submittedQuery, setSubmittedQuery] = useState(initialSearchTerm)
  const [limit, setLimit] = useState(DEFAULT_LIMIT)
  const [sort, setSort] = useState<RealWorldSafetySort>('score')
  const [data, setData] = useState<RealWorldSafetySearchResponse | null>(null)
  const [loading, setLoading] = useState(Boolean(initialSearchTerm))
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

  const loadPublicSafetyRecords = useCallback(
    async (
      nextQuery: string,
      nextLimit: number,
      nextSort: RealWorldSafetySort = sort,
      options: SearchOptions = {},
    ) => {
      const cleanQuery = normalizeSearchTerm(nextQuery)
      if (!cleanQuery) {
        setHelper(
          'Enter a product, vehicle, NDC, UPC, VIN, drug, device, or consumer product to search public safety records.',
        )
        setError('')
        return
      }

      const boundedLimit = Math.min(Math.max(nextLimit, 1), 25)
      const requestKey = `${cleanQuery.toLocaleLowerCase('en-US')}::${boundedLimit}::${nextSort}`
      if (inFlightKeyRef.current === requestKey) return

      if (options.skipIfCompleted && completedKeyRef.current === requestKey) {
        setQuery(cleanQuery)
        setSubmittedQuery(cleanQuery)
        setError('')
        setHelper('')
        return
      }

      const requestId = requestIdRef.current + 1
      requestIdRef.current = requestId
      inFlightKeyRef.current = requestKey
      completedKeyRef.current = ''

      setQuery(cleanQuery)
      setSubmittedQuery(cleanQuery)
      setData(null)
      setLoading(true)
      setError('')
      setHelper('')

      if (options.updateUrl) {
        writeSafetyQueryToUrl(PAGE_IDS.PUBLIC_SAFETY, cleanQuery, cleanQuery, 'push')
      }

      try {
        const response = await searchRealWorldSafety(cleanQuery, boundedLimit, nextSort)

        if (!isMountedRef.current || requestId !== requestIdRef.current) return

        setData(response)
        completedKeyRef.current = requestKey
      } catch {
        if (isMountedRef.current && requestId === requestIdRef.current) {
          setError(
            'Unable to load public safety records. Check backend/source availability and try again.',
          )
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
    const nextInitialQuery = normalizeSearchTerm(initialRawQuery || initialQuery)
    let isCurrentEffect = true

    async function syncInitialQuery() {
      if (!nextInitialQuery) {
        await Promise.resolve()
        if (!isCurrentEffect) return

        requestIdRef.current += 1
        inFlightKeyRef.current = ''
        completedKeyRef.current = ''
        setQuery('')
        setSubmittedQuery('')
        setData(null)
        setLoading(false)
        setError('')
        setHelper('')
        return
      }

      await loadPublicSafetyRecords(nextInitialQuery, DEFAULT_LIMIT, 'score', {
        skipIfCompleted: true,
      })
    }

    void syncInitialQuery()

    return () => {
      isCurrentEffect = false
    }
  }, [initialQuery, initialRawQuery, loadPublicSafetyRecords])

  const roleLookup = useMemo(() => createSourceRoleLookup(data), [data])
  const cleanDraftQuery = normalizeSearchTerm(query)
  const hasUnsubmittedDraft =
    Boolean(data) &&
    !loading &&
    getSearchComparisonKey(cleanDraftQuery) !== getSearchComparisonKey(submittedQuery)

  const unsubmittedDraftMessage = cleanDraftQuery
    ? `Showing results for ${submittedQuery}. Search ${cleanDraftQuery} to update results.`
    : `Showing results for ${submittedQuery}. Enter a new query and press Search to update results.`

  function handleSubmit() {
    void loadPublicSafetyRecords(query, limit, sort, { updateUrl: true })
  }

  function handleExampleClick(example: string) {
    setQuery(example)
    setError('')
    setHelper('')
    void loadPublicSafetyRecords(example, limit, sort, { updateUrl: true })
  }

  function handleSortChange(nextSort: RealWorldSafetySort) {
    if (nextSort === sort || !submittedQuery || loading) return

    setSort(nextSort)
    void loadPublicSafetyRecords(submittedQuery, limit, nextSort, {
      skipIfCompleted: true,
    })
  }

  const sortDisabled =
    loading || !data || data.search_plan.clarification_required || data.total_matches === 0

  return (
    <section className="public-safety-page">
      <section className="public-safety-hero">
        <div className="public-safety-hero__copy">
          <span className="public-safety-eyebrow">Public Safety Search</span>
          <h1>Search public safety records with source intelligence.</h1>
          <p>
            Search public recall, reference, label, vehicle, device, and
            consumer-product safety records.
          </p>
        </div>

        <form
          className="public-safety-search-form"
          onSubmit={(event) => {
            event.preventDefault()
            handleSubmit()
          }}
        >
          <div className="public-safety-search-field">
            <label htmlFor="public-safety-query">Safety record search</label>
            <QueryTypeahead
              id="public-safety-query"
              value={query}
              onChange={(nextQuery) => {
                setQuery(nextQuery)
                if (helper) setHelper('')
              }}
              area="public_safety"
              placeholder="Search: tire, air fryer, Advil, NDC 66715 6547"
              ariaDescribedBy="public-safety-helper"
              showWorkflow
            />
            <p id="public-safety-helper">
              Try a product, brand, VIN, NDC, UPC, device, vehicle, or consumer-product
              term.
            </p>
          </div>

          <div className="public-safety-form-actions">
            <label htmlFor="public-safety-limit">Limit</label>
            <select
              id="public-safety-limit"
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value))}
            >
              <option value={10}>10</option>
              <option value={15}>15</option>
              <option value={25}>25</option>
            </select>
            <button type="submit" disabled={loading}>
              {loading ? 'Checking...' : 'Search public records'}
            </button>
          </div>
        </form>

        <div className="public-safety-examples" aria-label="Public safety examples">
          {exampleQueries.map((example) => (
            <button key={example} type="button" onClick={() => handleExampleClick(example)}>
              {example}
            </button>
          ))}
        </div>
      </section>

      {helper && (
        <p className="public-safety-guidance" role="status">
          {helper}
        </p>
      )}

      {error && (
        <p className="public-safety-error" role="alert">
          {error}
        </p>
      )}

      {loading && (
        <p className="public-safety-loading" role="status" aria-live="polite">
          Checking public safety records...
        </p>
      )}

      {hasUnsubmittedDraft && (
        <p className="public-safety-draft-notice" role="status">
          {unsubmittedDraftMessage}
        </p>
      )}

      {!loading && !data && !error && (
        <section className="public-safety-empty">
          <h2>Start with a real product, identifier, or vehicle term.</h2>
          <p>
            Dav AI will check public sources and return matching records with links
            for official verification.
          </p>
        </section>
      )}

      {data && !loading && (
        <>
          <PublicSafetySummaryStrip data={data} submittedQuery={submittedQuery} />

          <div className="public-safety-workspace">
            {data.search_plan.clarification_required ? (
              <SearchOutcomeCard data={data} />
            ) : (
              <ResultsList
                data={data}
                roleLookup={roleLookup}
                submittedQuery={submittedQuery}
                sort={sort}
                sortDisabled={sortDisabled}
                handleSortChange={handleSortChange}
              />
            )}

            <aside className="public-safety-insight-rail">
              <PublicSafetyDownloadCard />
              <PublicSafetyInterpretationCard data={data} />
            </aside>
          </div>

          <PublicSafetyAdvancedDetails data={data} />
        </>
      )}
    </section>
  )
}

export default PublicSafetySearchPage
