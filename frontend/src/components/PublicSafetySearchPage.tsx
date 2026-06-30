import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  buildPublicSafetyAssistantContext,
  type AssistantChatContext,
} from '../api/assistant'
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
import SourceIntegrationBadge from './SourceIntegrationBadge'
import SourceDetailsDisclosure from './SourceDetailsDisclosure'

type PublicSafetySearchPageProps = {
  initialQuery: string
  initialRawQuery?: string
  setAssistantContext?: (context: AssistantChatContext | null) => void
}

type SearchOptions = {
  updateUrl?: boolean
  skipIfCompleted?: boolean
}

const exampleQueries = ['tire', 'scooter', 'air fryer', 'battery', 'Advil', 'Tylenol']

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
  'outbreak_context',
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
  outbreak_context: {
    label: 'Outbreak / investigation context',
    shortLabel: 'Outbreak context',
    description:
      'Public-health investigation or outbreak context. This is not automatically a recall or proof that a specific product caused illness.',
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

      {understanding.category_classification && (
        <div className="public-safety-detail-grid">
          <div>
            <small>Primary category</small>
            <strong>{formatQueryType(understanding.category_classification.primary_category)}</strong>
          </div>
          <div>
            <small>Category confidence</small>
            <strong>{formatQueryType(understanding.category_classification.confidence)}</strong>
          </div>
          <div>
            <small>Secondary categories</small>
            <strong>
              {understanding.category_classification.secondary_categories.length
                ? understanding.category_classification.secondary_categories.map(formatQueryType).join(', ')
                : 'None'}
            </strong>
          </div>
          <div>
            <small>Matched terms</small>
            <strong>
              {understanding.category_classification.matched_terms.length
                ? understanding.category_classification.matched_terms.join(', ')
                : 'None'}
            </strong>
          </div>
        </div>
      )}

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
    <section className="pharmacy-recall-panel public-safety-clarification-panel">
      <div className="pharmacy-panel-header">
        <div>
          <p className="eyebrow">Search needs a category</p>
          <h2>Choose a safety area to continue</h2>
          <span>Dav AI did not run a broad source sweep for this ambiguous query.</span>
        </div>
      </div>

      <div className="pharmacy-empty-card public-safety-clarification-options">
        <h3>What kind of item are you checking?</h3>
        <p>
          This query could belong to multiple safety categories. Choose the closest
          safety area to check the right official sources.
        </p>
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
      className="pharmacy-summary-strip public-safety-summary-strip"
      aria-label={`Summary for ${submittedQuery}`}
    >
      <div className="pharmacy-summary-strip__query">
        <small>Current query</small>
        <strong>{submittedQuery}</strong>
        <span>Public records, not a personal safety determination</span>
      </div>

      <dl className="pharmacy-summary-metrics">
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
    <section className="pharmacy-insight-card public-safety-export-card">
      <div className="pharmacy-insight-card__header">
        <div>
          <p className="eyebrow">Export</p>
          <h2>Download results</h2>
        </div>
      </div>
      <p className="pharmacy-insight-card__empty">
        Export the summary, returned records, checked sources, and limitations.
      </p>
      <button type="button" disabled>
        Download Excel
      </button>
    </section>
  )
}

const vehicleRecallExamples = [
  '2018 Toyota Camry',
  '2020 Honda Civic',
  '4T1B11HK5JU000001',
]

function VehicleRecallCheckCard({
  onExampleClick,
}: {
  onExampleClick: (example: string) => void
}) {
  return (
    <section className="pharmacy-insight-card public-safety-vehicle-card">
      <div>
        <p className="eyebrow">Vehicle Recall Check</p>
        <h2>Search by year, make, model, or VIN.</h2>
      </div>

      <p>
        Dav AI routes vehicle searches to NHTSA recall sources when the query looks
        like a vehicle, tire, car seat, equipment item, or VIN.
      </p>

      <div className="public-safety-vehicle-example-grid" aria-label="Vehicle recall examples">
        {vehicleRecallExamples.map((example) => (
          <button key={example} type="button" onClick={() => onExampleClick(example)}>
            {example}
          </button>
        ))}
      </div>

      <ul>
        <li>Use year/make/model for a quick recall search.</li>
        <li>Use VIN when available for better vehicle-specific verification.</li>
        <li>Always verify the exact VIN and campaign status on the official NHTSA page.</li>
      </ul>
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
      eyebrow="Evidence types"
      title="Evidence types found"
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

function formatSourceFreshnessValue(value: string | null | undefined) {
  if (!value) return 'Not listed'
  return value.replace(/_/g, ' ')
}

function formatSourceFreshnessStatus({
  upstreamStatus,
  sourceSnapshotStatus,
  sourcePullId,
}: {
  upstreamStatus: string
  sourceSnapshotStatus?: string | null
  sourcePullId?: string | null
}) {
  if (upstreamStatus === 'error') return 'Source issue reported'
  if (sourceSnapshotStatus === 'stored' || sourcePullId) return 'Pulled and stored'
  if (upstreamStatus === 'success') return 'Checked during this search'
  if (upstreamStatus === 'empty') return 'Checked; no records returned'
  return formatSourceFreshnessValue(upstreamStatus)
}

function SourceCoveragePanel({
  data,
}: {
  data: RealWorldSafetySearchResponse
}) {
  const auditsBySourceId = new Map(
    data.source_audits.map((audit) => [audit.source_id, audit]),
  )
  const freshnessBySourceId = new Map(
  (data.source_freshness ?? []).map((freshness) => [freshness.source_id, freshness]),
  )

  return (
    <CollapsiblePanel
      eyebrow="How this search was run"
      title="Sources checked and verification links"
      className="public-safety-source-coverage"
    >
      <div className="public-safety-coverage-grid">
        {data.sources_checked.map((source) => {
          const audit = auditsBySourceId.get(source.source_id)
          const freshness = freshnessBySourceId.get(source.source_id)

          return (
            <div key={`${source.source_id}-${source.source_name}`}>
              <small>{source.upstream_status}</small>
              <strong>{source.source_name}</strong>
              <SourceIntegrationBadge
                sourceId={source.source_id}
                sourceName={source.source_name}
                sourceType={source.source_type}
              />
              <span>
                {source.record_count} records | {source.source_type}
              </span>

              <div className="public-safety-source-freshness">
                <small>Source freshness</small>
                <span>
  {freshness?.user_label ??
    formatSourceFreshnessStatus({
      upstreamStatus: source.upstream_status,
      sourceSnapshotStatus: audit?.source_snapshot_status,
      sourcePullId: audit?.source_pull_id,
    })}
</span>
                <span>
                  Checked:{' '}
                  {formatPublicSafetyDate(freshness?.checked_at ?? data.retrieval_timestamp)}
                </span>
                {freshness?.explanation && <span>{freshness.explanation}</span>}
                {(freshness?.source_snapshot_status ?? audit?.source_snapshot_status) && (
                  <span>
                    Snapshot:{' '}
                    {formatSourceFreshnessValue(
                      freshness?.source_snapshot_status ?? audit?.source_snapshot_status,
                    )}
                  </span>
                )}
                {(freshness?.source_pull_id ?? audit?.source_pull_id) && (
                  <span>Source pull stored</span>
                )}
                {(freshness?.source_payload_hash ?? audit?.source_payload_hash) && (
                  <span>Payload hash captured</span>
                )}
              </div>

              <SourceDetailsDisclosure
                sourceId={source.source_id}
                sourceName={source.source_name}
                sourceType={source.source_type}
                sourceKind={source.source_kind}
                sourceUrl={source.source_url}
                recordCount={source.record_count}
                upstreamStatus={source.upstream_status}
                retrievedAt={freshness?.checked_at ?? data.retrieval_timestamp}
              />
            </div>
          )
        })}
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
    <section className="pharmacy-insight-card public-safety-interpretation-card">
      <div>
        <p className="eyebrow">What to verify next</p>
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

function IdentifierCheckPanel({
  data,
}: {
  data: RealWorldSafetySearchResponse
}) {
  const detectedItems = data.identifier_check.detected
  const verifyItems = data.identifier_check.to_verify.slice(0, 6)

  return (
    <section className="pharmacy-insight-card public-safety-identifier-card">
      <div>
        <p className="eyebrow">Identifier check</p>
        <h2>Verify the exact item before acting.</h2>
      </div>

      <p>{data.identifier_check.user_message}</p>

      {detectedItems.length > 0 && (
        <div className="public-safety-identifier-section">
          <small>Detected from your search</small>
          <div className="public-safety-identifier-list">
            {detectedItems.map((item) => (
              <div key={`${item.type}-${item.value}-${item.source}`}>
                <strong>{item.label}</strong>
                <span>{item.value ?? 'Not listed'}</span>
                <em>{item.reason}</em>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="public-safety-identifier-section">
        <small>Verify from returned records</small>
        <div className="public-safety-identifier-list">
          {verifyItems.map((item) => (
            <div key={`${item.type}-${item.value ?? 'missing'}-${item.source}`}>
              <strong>{item.label}</strong>
              <span>{item.value ?? 'Check official record'}</span>
              <em>{item.reason}</em>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function PublicSafetyBoundaryCard({
  data,
}: {
  data?: RealWorldSafetySearchResponse
}) {
  return (
    <section className="pharmacy-safety-card public-safety-boundary-card">
      <div>
        <p className="eyebrow">Safety boundary</p>
        <h2>Verify the exact record before acting.</h2>
      </div>
      <ul>
        <li>Match product, brand, model, lot, code, and date details.</li>
        <li>No returned record is proof that an item is safe.</li>
        <li>Open the official source for current instructions and status.</li>
      </ul>
      <p className="pharmacy-safety-card__source">
        {data?.public_data_disclaimer ??
          'Public records only. This is not a safety guarantee or professional guidance.'}
      </p>
    </section>
  )
}

function PublicSafetyEmptyWorkspace({
  onVehicleExampleClick,
}: {
  onVehicleExampleClick: (example: string) => void
}) {
  return (
    <div className="pharmacy-workspace public-safety-workspace">
      <section className="pharmacy-recall-panel public-safety-record-panel">
        <div className="pharmacy-panel-header">
          <div>
            <p className="eyebrow">Public records</p>
            <h2>Matched public records</h2>
            <span>Search to load official and public safety records</span>
          </div>
        </div>

        <div className="pharmacy-empty-card pharmacy-empty-card--quiet">
          <h3>Public records will appear here.</h3>
          <p>
            Search above to check source links, affected products, models, lots,
            remedies, and public safety context.
          </p>
        </div>
      </section>

      <aside className="pharmacy-insight-rail">
        <VehicleRecallCheckCard onExampleClick={onVehicleExampleClick} />

        <section className="pharmacy-insight-card public-safety-interpretation-card">
          <div>
            <p className="eyebrow">What to verify next</p>
            <h2>Use returned public records as a starting point.</h2>
          </div>
          <p>
            Start with a product, identifier, vehicle, drug, device, UPC, VIN, or NDC.
            Dav AI will show matching records with official links.
          </p>
        </section>

        <PublicSafetyBoundaryCard />
      </aside>
    </div>
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

function publicSafetySourceKindLabel(kind: string) {
  if (kind === 'normalized_public_notice') return 'Normalized public notice'
  if (kind === 'public_notice') return 'Official public notice'
  return 'Official API record'
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
    case 'outbreak_context':
      return 'Outbreak context'
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
          <span>{publicSafetySourceKindLabel(record.source_kind)}</span>
          <SourceIntegrationBadge
            sourceName={record.source_name}
            sourceType={record.source_type}
          />
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

        {record.extraction_confidence && (
          <div>
            <span>Notice extraction</span>
            <strong>{record.extraction_confidence}</strong>
          </div>
        )}

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
          <strong>{publicSafetySourceKindLabel(record.source_kind)}</strong>
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
      <section className="pharmacy-recall-panel public-safety-record-panel">
        <div className="pharmacy-panel-header">
          <div>
            <p className="eyebrow">Public records</p>
            <h2>Matched public records</h2>
            <span>Showing results for: {submittedQuery}</span>
          </div>
        </div>

        <div className="pharmacy-empty-card public-safety-no-results">
          <h3>No matching public records returned.</h3>
          <p>{data.no_match_explanation}</p>
        </div>
      </section>
    )
  }

  return (
    <section className="pharmacy-recall-panel public-safety-record-panel">
      <div className="pharmacy-panel-header">
        <div>
          <p className="eyebrow">Public records</p>
          <h2>Matched public records</h2>
          <span>
            Showing {data.results.length} of {data.total_matches} returned record
            {data.total_matches === 1 ? '' : 's'} for {submittedQuery}
          </span>
        </div>

        <div
          className="recall-sort-control"
          role="group"
          aria-label="Sort public safety records"
        >
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

      <div className="pharmacy-record-table" aria-label="Public safety search results">
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
  setAssistantContext,
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
      nextSort: RealWorldSafetySort,
      options: SearchOptions = {},
    ) => {
      const cleanQuery = normalizeSearchTerm(nextQuery)
      if (!cleanQuery) {
        setHelper(
          'Enter a product, vehicle, NDC, UPC, VIN, drug, device, or consumer product to search public safety records.',
        )
        setError('')
        setAssistantContext?.(null)
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
        setAssistantContext?.(null)
        return
      }

      const requestId = requestIdRef.current + 1
      requestIdRef.current = requestId
      inFlightKeyRef.current = requestKey
      completedKeyRef.current = ''

      setQuery(cleanQuery)
      setSubmittedQuery(cleanQuery)
      setData(null)
      setAssistantContext?.(null)
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
        if (response.total_matches > 0) {
          setAssistantContext?.(buildPublicSafetyAssistantContext(response))
        } else {
          setAssistantContext?.(null)
        }
        completedKeyRef.current = requestKey
      } catch {
        if (isMountedRef.current && requestId === requestIdRef.current) {
          setAssistantContext?.(null)
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
    [setAssistantContext],
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
        setAssistantContext?.(null)
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
  }, [initialQuery, initialRawQuery, loadPublicSafetyRecords, setAssistantContext])

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
    <section className="safety-area-page safety-area-page--public pharmacy-detail-page public-safety-page">
      <header className="pharmacy-overview public-safety-overview">
        <div className="pharmacy-overview__main">
          <p className="eyebrow">Public Safety</p>
          <h1>
            {submittedQuery ? (
              <>
                Safety review for <span>{submittedQuery}</span>
              </>
            ) : (
              'Search public safety records'
            )}
          </h1>
          <p className="pharmacy-overview__description">
            Search recalls, labels, vehicles, devices, drugs, and consumer-product
            safety records from relevant public sources.
          </p>

          <form
            className="pharmacy-page-search public-safety-page-search"
            onSubmit={(event) => {
              event.preventDefault()
              handleSubmit()
            }}
          >
            <label htmlFor="public-safety-query">Safety record search</label>
            <div className="public-safety-search-controls">
              <QueryTypeahead
                id="public-safety-query"
                value={query}
                onChange={(nextQuery) => {
                  setQuery(nextQuery)
                  if (helper) setHelper('')
                }}
                area="public_safety"
                placeholder="Search tire, scooter, Advil, NDC, VIN, or UPC"
                ariaDescribedBy="public-safety-helper"
                showWorkflow
              />
              <select
                id="public-safety-limit"
                aria-label="Result limit"
                value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}
              >
                <option value={10}>10 results</option>
                <option value={15}>15 results</option>
                <option value={25}>25 results</option>
              </select>
              <button type="submit" disabled={loading}>
                {loading ? 'Checking...' : 'Search'}
              </button>
            </div>
          </form>

          <div
            className="pharmacy-example-row public-safety-example-row"
            aria-label="Public safety examples"
          >
            <span>Try</span>
            {exampleQueries.map((example) => (
              <button key={example} type="button" onClick={() => handleExampleClick(example)}>
                {example}
              </button>
            ))}
          </div>

          <p className="pharmacy-source-line public-safety-source-line">
            <span aria-hidden="true" />
            <strong>Public safety records</strong>
            <span>CPSC + FDA + NHTSA where relevant</span>
            <span>Not a safety guarantee</span>
          </p>
          <p id="public-safety-helper" className="public-safety-search-helper">
            Search a product, identifier, vehicle, drug, or device.
          </p>
        </div>
      </header>

      {helper && (
        <p className="safety-search-guidance" role="status">
          {helper}
        </p>
      )}

      {error && (
        <p className="error-message pharmacy-page-error" role="alert">
          {error}
        </p>
      )}

      {loading && (
        <p className="safety-area-status" role="status" aria-live="polite">
          Checking public safety records...
        </p>
      )}

      {hasUnsubmittedDraft && (
        <p className="safety-search-guidance" role="status">
          {unsubmittedDraftMessage}
        </p>
      )}

      {!loading && !data && !error && (
        <PublicSafetyEmptyWorkspace onVehicleExampleClick={handleExampleClick} />
      )}

      {data && !loading && (
        <section className="public-safety-vehicle-inline">
          <VehicleRecallCheckCard onExampleClick={handleExampleClick} />
        </section>
      )}

      {data && !loading && (
        <>
          <PublicSafetySummaryStrip data={data} submittedQuery={submittedQuery} />

          <div className="pharmacy-workspace public-safety-workspace">
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

            <aside className="pharmacy-insight-rail">
              <PublicSafetyDownloadCard />
              <IdentifierCheckPanel data={data} />
              <PublicSafetyInterpretationCard data={data} />
              <PublicSafetyBoundaryCard data={data} />
            </aside>
          </div>

          <PublicSafetyAdvancedDetails data={data} />
        </>
      )}
    </section>
  )
}

export default PublicSafetySearchPage