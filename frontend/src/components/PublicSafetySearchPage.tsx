import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  searchRealWorldSafety,
  type RealWorldSafetyRecord,
  type RealWorldSafetySearchResponse,
  type RealWorldSafetySourceRole,
} from '../api/realWorldSafety'
import { PAGE_IDS } from '../types/navigation'
import { getSearchComparisonKey, normalizeSearchTerm } from '../utils/queryNormalization'
import { formatDate, formatTimestamp } from '../utils/recallFormatters'
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

function formatRole(value: RealWorldSafetySourceRole) {
  return roleCopy[value]?.label ?? formatQueryType(value)
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

function resultRoleNotice(role: RealWorldSafetySourceRole) {
  if (role === 'reference_identity') {
    return 'Reference only - not a recall'
  }
  if (role === 'label_reference') {
    return 'Official label reference - not a recall'
  }
  if (role === 'signal_report') {
    return 'Signal report - not a recall or proof of causation'
  }
  if (role === 'recall_enforcement') {
    return 'Official recall/enforcement record'
  }
  return 'Public source record'
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

function StatusPill({
  active,
  label,
  caution = false,
}: {
  active: boolean
  label: string
  caution?: boolean
}) {
  const className = active
    ? caution
      ? 'public-safety-status-pill public-safety-status-pill--caution'
      : 'public-safety-status-pill public-safety-status-pill--success'
    : 'public-safety-status-pill public-safety-status-pill--neutral'

  return (
    <span className={className}>
      <strong>{active ? 'Yes' : 'No'}</strong>
      {label}
    </span>
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

function SearchOutcomeCard({
  data,
  submittedQuery,
}: {
  data: RealWorldSafetySearchResponse
  submittedQuery: string
}) {
  const summary = data.safety_intelligence_summary
  const isClarificationRequired = data.search_plan.clarification_required
  const visibleSuggestedSteps = isClarificationRequired
    ? []
    : getVisibleSuggestedSteps(data).slice(0, 2)
  const sourceIssueCount = data.sources_failed.length

  return (
    <section className="public-safety-panel public-safety-outcome-card">
      <div className="public-safety-section-heading">
        <span>Search outcome</span>
        <h2>{isClarificationRequired ? 'Choose a safety area to continue' : 'What Dav AI found in public records'}</h2>
      </div>

      <p className="public-safety-submitted-query">
        Showing results for: <strong>{submittedQuery}</strong>
      </p>

      <div className="public-safety-status-row">
        <StatusPill
          active={summary.recall_or_enforcement_found}
          label="Recall / enforcement found"
          caution
        />
        <StatusPill
          active={summary.reference_or_label_found}
          label="Reference / label found"
        />
        <StatusPill
          active={summary.signal_report_found}
          label="Signal report found"
          caution
        />
      </div>

      <p className="public-safety-summary-text">
        {isClarificationRequired
          ? 'This query could belong to multiple safety categories, so Dav AI did not run a broad source sweep. Choose the closest safety area to check the right official sources.'
          : summary.plain_language_summary}
      </p>

      <div className="public-safety-outcome-facts">
        <div>
          <small>Total matches</small>
          <strong>{data.total_matches}</strong>
        </div>
        <div>
          <small>Sources checked</small>
          <strong>{isClarificationRequired ? 'Not checked yet' : data.sources_checked.length}</strong>
        </div>
        <div className={sourceIssueCount > 0 ? 'public-safety-outcome-fact--issue' : ''}>
          <small>Source issues</small>
          <strong>{sourceIssueCount}</strong>
        </div>
      </div>

      {isClarificationRequired && (
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
      )}

      {visibleSuggestedSteps.length > 0 && (
        <div className="public-safety-list-block">
          <small>Next steps</small>
          <ul>
            {visibleSuggestedSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="public-safety-caveat">{summary.caveat}</p>
    </section>
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

function ResultCard({
  record,
  role,
}: {
  record: RealWorldSafetyRecord
  role: RealWorldSafetySourceRole
}) {
  const [expanded, setExpanded] = useState(false)
  const title = getRecordTitle(record)
  const reasonText = displayValue(
    record.reason || record.hazard_type,
    'No reason listed',
  )
  const reasonPreview = truncateText(reasonText)
  const remedyText = displayValue(record.remedy, 'No remedy listed')

  return (
    <article className={`public-safety-result public-safety-result--${role}`}>
      <div className="public-safety-result__topline">
        <div className="public-safety-result__source">
          <SourceBadge role={role}>{formatRole(role)}</SourceBadge>
          <span>{record.source_name}</span>
        </div>
        <span className="public-safety-result__date">
          {formatDate(record.published_date)}
        </span>
      </div>

      <div className="public-safety-result__heading">
        <h3>{title}</h3>
        <p>
          {displayValue(record.category, 'Uncategorized')}
        </p>
        <strong className={`public-safety-result__role-note public-safety-result__role-note--${role}`}>
          {resultRoleNotice(role)}
        </strong>
      </div>

      <div className="public-safety-result__preview">
        <div>
          <small>Reason / hazard preview</small>
          <p>{reasonPreview.text}</p>
        </div>
        {reasonPreview.truncated && <span>Long official text shortened.</span>}
      </div>

      {expanded && (
        <div className="public-safety-result__facts">
          <div className="public-safety-result__fact public-safety-result__fact--wide">
            <small>Full reason / hazard</small>
            <strong>{reasonText}</strong>
          </div>
          <div className="public-safety-result__fact public-safety-result__fact--wide">
            <small>Remedy / use</small>
            <strong>{remedyText}</strong>
          </div>
          <div>
            <small>Product</small>
            <strong>{displayValue(record.product_name)}</strong>
          </div>
          <div>
            <small>Brand</small>
            <strong>{displayValue(record.brand_name)}</strong>
          </div>
          <div>
            <small>Company</small>
            <strong>{displayValue(record.company_name)}</strong>
          </div>
          <div>
            <small>Recall / record number</small>
            <strong>{displayValue(record.recall_number)}</strong>
          </div>
          <div>
            <small>Source type</small>
            <strong>{record.source_type}</strong>
          </div>
          <div>
            <small>Source kind</small>
            <strong>{record.source_kind}</strong>
          </div>
          <div className="public-safety-result__fact public-safety-result__fact--wide">
            <small>Affected models</small>
            <strong>{displayList(record.affected_models)}</strong>
          </div>
          <div className="public-safety-result__fact public-safety-result__fact--wide">
            <small>Affected lots</small>
            <strong>{displayList(record.affected_lots)}</strong>
          </div>
        </div>
      )}

      <div className="public-safety-result__footer">
        <button
          type="button"
          className="public-safety-result__toggle"
          aria-expanded={expanded}
          onClick={() => setExpanded((current) => !current)}
        >
          {expanded ? 'Hide details' : 'Show details'}
        </button>
        <div>
          <span>Retrieved {formatTimestamp(record.retrieved_at)}</span>
          {record.record_url ? (
            <a href={record.record_url} target="_blank" rel="noreferrer">
              Open official record
            </a>
          ) : (
            <span>Official record URL not listed</span>
          )}
        </div>
      </div>
    </article>
  )
}

function ResultsList({
  data,
  roleLookup,
  submittedQuery,
}: {
  data: RealWorldSafetySearchResponse
  roleLookup: Map<string, RealWorldSafetySourceRole>
  submittedQuery: string
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
        <p>{data.safety_intelligence_summary.caveat}</p>
      </section>
    )
  }

  return (
    <section className="public-safety-results">
      <div className="public-safety-section-heading">
        <span>Returned records</span>
        <h2>Showing results for: {submittedQuery}</h2>
      </div>

      <div className="public-safety-results-list">
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
      const requestKey = `${cleanQuery.toLocaleLowerCase('en-US')}::${boundedLimit}`
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
        const response = await searchRealWorldSafety(cleanQuery, boundedLimit)

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

      await loadPublicSafetyRecords(nextInitialQuery, DEFAULT_LIMIT, {
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
    void loadPublicSafetyRecords(query, limit, { updateUrl: true })
  }

  function handleExampleClick(example: string) {
    setQuery(example)
    setError('')
    setHelper('')
    void loadPublicSafetyRecords(example, limit, { updateUrl: true })
  }

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
          <strong>Public records only. Not a safety guarantee. Verify official sources.</strong>
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
          Checking public records and source roles...
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
            Dav AI will show query understanding, source roles, official/public
            records, caveats, and next steps without creating synthetic results.
          </p>
        </section>
      )}

      {data && !loading && (
        <>
          <SearchOutcomeCard data={data} submittedQuery={submittedQuery} />
          <ResultsList
            data={data}
            roleLookup={roleLookup}
            submittedQuery={submittedQuery}
          />
          <QueryUnderstandingCard data={data} />
          <SourceRolesPanel data={data} />
          <SourceCoveragePanel data={data} />

          <CollapsiblePanel
            eyebrow="Public data boundary"
            title="What this response does not prove"
            className="public-safety-boundary"
          >
            <p>{data.public_data_disclaimer}</p>
            {data.limitations.length > 0 && (
              <ul>
                {data.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            )}
          </CollapsiblePanel>
        </>
      )}
    </section>
  )
}

export default PublicSafetySearchPage
