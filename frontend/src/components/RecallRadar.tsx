import { useMemo, useState } from 'react'
import type { RecallSearchResponse } from '../api/recalls'
import AuditPanel from './AuditPanel'
import SafetyBriefingPanel from './SafetyBriefingPanel'
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
  const hasNoResults = data && data.results.length === 0
  const hasResults = data && data.results.length > 0
  const topResult = hasResults ? data.results[0] : null

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

            <div className="consumer-summary__score" aria-hidden="true">
              <span>
                <strong>✓</strong>
                <small>Review below</small>
              </span>
            </div>
          </section>
        )}

        {hasResults && (
          <div className="results-grid" aria-label="Recall search results">
            {data.results.map((result) => (
              <article className="recall-card" key={result.recall_number}>
                <div className="recall-card-top">
                  <span className={`risk-pill risk-${result.risk_score.label.toLowerCase()}`}>
                    {result.risk_score.label} signal
                  </span>

                  <h3>{result.product_description}</h3>

                  <div className="recall-score-block">
                    <small>Risk score</small>
                    <strong>{result.risk_score.score}</strong>
                  </div>
                </div>

                <p className="reason">
                  <strong>Reason:</strong> {result.reason_for_recall}
                </p>

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

                <details>
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
              </article>
            ))}
          </div>
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