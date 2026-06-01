import { useMemo, useState } from 'react'
import type { RecallSearchResponse } from '../api/recalls'
import AuditPanel from './AuditPanel'
import SafetyBriefingPanel from './SafetyBriefingPanel'
import SafeInsightCards, { type SafeInsightCard } from './SafeInsightCards'
import { formatDate, formatTimestamp, riskExplanation } from '../utils/recallFormatters'
import { generateRecallBriefing } from '../utils/briefingGenerator'
import { briefingRoleLabels, type BriefingRole } from '../types/briefing'

type RecallRadarProps = {
  query: string
  setQuery: (query: string) => void
  data: RecallSearchResponse | null
  loading: boolean
  error: string
  handleSearch: () => void
}

const briefingRoles: BriefingRole[] = ['consumer', 'pharmacy', 'clinic', 'public_health']

function RecallRadar({
  query,
  setQuery,
  data,
  loading,
  error,
  handleSearch,
}: RecallRadarProps) {
  const [briefingRole, setBriefingRole] = useState<BriefingRole>('consumer')
  const [sortMode, setSortMode] = useState<'score' | 'latest'>('score')

  const hasNoResults = data && data.results.length === 0
  const hasResults = data && data.results.length > 0
  const topResult = hasResults ? data.results[0] : null

  const safeInsightCards: SafeInsightCard[] = data
    ? [
        {
          label: 'Source-backed',
          title: 'Public FDA source and retrieval time are visible.',
          detail: `${data.source_name} returned ${data.count} record${
            data.count === 1 ? '' : 's'
          } for this search, retrieved ${formatTimestamp(data.retrieval_timestamp)}.`,
          tone: 'source',
        },
        {
          label: 'Review signal',
          title: hasResults
            ? `Highest matched signal: ${topResult?.risk_score.label ?? 'Unknown'}`
            : 'No matched recall records returned.',
          detail: hasResults
            ? 'DavAI can highlight records to review, but you should verify product name, firm, lot details, and recall date.'
            : 'No match does not prove a product is safe or unsafe. Try another brand, ingredient, or product name.',
          tone: 'review',
        },
        {
          label: 'Safety boundary',
          title: 'This is not medical advice or a safety guarantee.',
          detail:
            'DavAI summarizes public recall data only. It does not diagnose, treat, or replace FDA, clinician, or pharmacist guidance.',
          tone: 'safety',
        },
      ]
    : []

  const sortedResults = useMemo(() => {
    if (!data) return []

    return [...data.results].sort((left, right) => {
      if (sortMode === 'latest') {
        return (
          Number(right.recall_initiation_date || 0) -
          Number(left.recall_initiation_date || 0)
        )
      }

      return right.risk_score.score - left.risk_score.score
    })
  }, [data, sortMode])

  const briefing = useMemo(() => {
    if (!data) return null

    return generateRecallBriefing(data, briefingRole)
  }, [data, briefingRole])

  return (
    <section className="recallradar" id="recallradar">
      <div className="section-heading">
        <p className="eyebrow">RecallRadar live module</p>
        <h2>Search public FDA recall signals.</h2>
        <p>
          Enter a product, drug, brand, or category. Dav AI checks public recall records,
          highlights matched results, and explains what to review next.
        </p>
      </div>

      <div className="search-panel">
        <div className="search-box">
          <div className="search-field">
            <label className="field-label" htmlFor="recall-search">
              Recall search
            </label>

            <input
              id="recall-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  handleSearch()
                }
              }}
              placeholder="Search recalls: eye drops, insulin, metformin"
              aria-describedby="recall-search-helper"
            />

            <p className="field-helper" id="recall-search-helper">
              Public FDA recall records only. Not medical advice or clinical decision support.
            </p>
          </div>

          <button type="button" onClick={handleSearch} disabled={loading}>
            {loading ? 'Checking public data...' : 'Analyze'}
          </button>
        </div>

        {loading && (
          <p className="loading-helper" role="status" aria-live="polite">
            This may take a few seconds while the secure backend wakes up and checks public FDA
            recall sources.
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
            <span>Public FDA source: {data.source_name}</span>
            <span>Retrieved {formatTimestamp(data.retrieval_timestamp)}</span>
          </div>
        )}

        {hasNoResults && (
          <div className="empty-state">
            <h3>No FDA recall records matched this search.</h3>
            <p>
              This does not prove the product is safe or unsafe. It only means no matching
              records were returned from the current openFDA Drug Enforcement search. Try
              searching by brand name, product name, ingredient, or category.
            </p>
          </div>
        )}

        {data && <SafeInsightCards cards={safeInsightCards} />}

        {topResult && (
          <section className="consumer-summary" aria-label="Recall safety summary">
            <div className="consumer-summary__icon" aria-hidden="true">
              <svg viewBox="0 0 48 48" focusable="false">
                <path d="M24 6l14 5v11c0 9-5.6 16.6-14 20-8.4-3.4-14-11-14-20V11l14-5z" />
                <path d="M17 24l5 5 10-12" />
              </svg>
            </div>

            <div className="consumer-summary__content">
              <h3>
                DavAI found {data?.count ?? 0} public FDA recall record
                {data?.count === 1 ? '' : 's'} that may match your search.
              </h3>

              <div className="consumer-summary__signal">
                <span>Highest signal:</span>
                <strong>{topResult.risk_score.label}</strong>
              </div>

              <p>
                Review the matched recalls below. This is public FDA recall data and not medical
                advice. Use the details to check whether a record may apply to your product.
              </p>
            </div>
          </section>
        )}

        {hasResults && (
          <>
            <div className="recall-results-toolbar">
              <div>
                <span>Sort results</span>
                <p>Choose how recall records are ordered.</p>
              </div>

              <div className="recall-sort-control" role="group" aria-label="Sort recall results">
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

            <div className="results-grid" aria-label="Recall search results">
              {sortedResults.map((result) => (
                <details className="recall-card recall-card--compact" key={result.recall_number}>
                  <summary className="recall-card-summary">
                    <span className="recall-card-icon" aria-hidden="true">
                      <svg viewBox="0 0 48 48" focusable="false">
                        <path d="M24 6l14 5v11c0 9-5.6 16.6-14 20-8.4-3.4-14-11-14-20V11l14-5z" />
                        <path d="M17 24l5 5 10-12" />
                      </svg>
                    </span>

                    <span className={`risk-pill risk-${result.risk_score.label.toLowerCase()}`}>
                      {result.risk_score.label} signal
                    </span>

                    <h3 className="recall-card-title">{result.product_description}</h3>

                    <span className="recall-card-expand" aria-hidden="true">
                      <svg viewBox="0 0 24 24" focusable="false">
                        <path d="M6 9l6 6 6-6" />
                      </svg>
                    </span>

                    <span className="recall-score-inline">
                      <strong>{result.risk_score.score}</strong>
                      <small>Risk score</small>
                    </span>
                  </summary>

                  <div className="recall-card-expanded">
                    <div className="recall-full-name-panel">
                      <small>Full product description</small>
                      <strong>{result.product_description}</strong>
                    </div>

                    <div className="recall-firm-panel">
                      <small>Recalling firm / manufacturer</small>
                      <strong>{result.recalling_firm || 'Unknown'}</strong>
                    </div>

                    <details className="recall-score-help">
                      <summary>How this score works</summary>
                      <div>
                        <p>
                          DavAI uses a transparent rule-based score. It reviews FDA class, recall
                          status, recency, and distribution scope. Higher scores mean the record
                          may deserve closer review, not that the product is personally unsafe.
                        </p>

                        <ul>
                          <li>
                            FDA class contribution:{' '}
                            {result.risk_score.components.classification_score}
                          </li>
                          <li>
                            Status contribution: {result.risk_score.components.status_score}
                          </li>
                          <li>
                            Recency contribution: {result.risk_score.components.recency_score}
                          </li>
                          <li>Scope contribution: {result.risk_score.components.scope_score}</li>
                        </ul>

                        <p>Score version: {result.risk_score.score_version}</p>
                      </div>
                    </details>

                    <div className="metadata-grid">
                      <div>
                        <small>FDA class</small>
                        <span>{result.classification || 'Unknown'}</span>
                      </div>
                      <div>
                        <small>Status</small>
                        <span>{result.status || 'Unknown'}</span>
                      </div>
                      <div>
                        <small>Recall date</small>
                        <span>{formatDate(result.recall_initiation_date)}</span>
                      </div>
                      <div>
                        <small>Firm</small>
                        <span>{result.recalling_firm || 'Unknown'}</span>
                      </div>
                    </div>

                    <p className="reason">
                      <strong>Reason:</strong> {result.reason_for_recall}
                    </p>

                    <div className="consumer-guidance-grid">
                      <p className="plain-explanation">
                        <strong>What this means</strong>
                        {riskExplanation(result)}
                      </p>

                      <div className="check-next-card">
                        <strong>What to check next</strong>
                        <ul>
                          <li>Verify the product name and lot details.</li>
                          <li>Compare the firm and recall date.</li>
                          <li>Review FDA instructions if available.</li>
                        </ul>
                      </div>
                    </div>

                    <details className="recall-technical-details">
                      <summary>Technical scoring details</summary>
                      <div className="audit-box">
                        <p>Source: {result.source.name}</p>
                        <p>Retrieved: {formatTimestamp(result.source.retrieval_timestamp)}</p>
                        <p>Score version: {result.risk_score.score_version}</p>
                        <p>
                          Components: class {result.risk_score.components.classification_score},
                          status {result.risk_score.components.status_score}, recency{' '}
                          {result.risk_score.components.recency_score}, scope{' '}
                          {result.risk_score.components.scope_score}
                        </p>
                      </div>
                    </details>
                  </div>
                </details>
              ))}
            </div>
          </>
        )}

        {briefing && (
          <div className="briefing-control-panel">
            <div className="briefing-role-selector">
              <span id="recall-briefing-role-label">Briefing role</span>

              <div
                className="briefing-role-buttons"
                role="group"
                aria-labelledby="recall-briefing-role-label"
              >
                {briefingRoles.map((role) => (
                  <button
                    key={role}
                    type="button"
                    className={`briefing-role-button ${briefingRole === role ? 'active' : ''}`}
                    aria-pressed={briefingRole === role}
                    onClick={() => setBriefingRole(role)}
                  >
                    {briefingRoleLabels[role]}
                  </button>
                ))}
              </div>
            </div>

            <SafetyBriefingPanel briefing={briefing} />
          </div>
        )}

        {data && (
          <details className="recall-provenance-details">
            <summary>Technical provenance and audit trail</summary>
            <AuditPanel query={query} response={data} />
          </details>
        )}
      </div>
    </section>
  )
}

export default RecallRadar