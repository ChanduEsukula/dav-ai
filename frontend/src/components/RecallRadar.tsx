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

  const briefing = useMemo(() => {
    if (!data) return null

    return generateRecallBriefing(data, briefingRole)
  }, [data, briefingRole])

  return (
    <section className="recallradar reveal" id="recallradar">
      <div className="section-heading">
        <p className="eyebrow">RecallRadar live module</p>
        <h2>Search public FDA recall signals.</h2>
        <p>
          Enter a product, drug, brand, or category. MedTrek AI fetches live public
          recall records, scores the signal, and keeps source details visible.
        </p>
      </div>

      <div className="search-panel">
        <div className="search-box">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                handleSearch()
              }
            }}
            placeholder="Search recalls: eye drops, insulin, metformin"
          />
          <button onClick={handleSearch} disabled={loading}>
            {loading ? 'Checking public data...' : 'Analyze'}
          </button>
        </div>

        {loading && (
          <p className="loading-helper">
            This may take a few seconds while the secure backend wakes up and checks public FDA recall sources.
          </p>
        )}

        {error && <p className="error-message">{error}</p>}

        {data && (
          <div className="source-strip">
            <span>{data.count} records matched</span>
            <span>{data.source_name}</span>
            <span>Retrieved {formatTimestamp(data.retrieval_timestamp)}</span>
          </div>
        )}

        {data && <AuditPanel query={query} response={data} />}

        {briefing && (
          <div className="briefing-control-panel">
            <div className="briefing-role-selector">
              <span>Briefing role</span>

              <div
                className="briefing-role-buttons"
                role="group"
                aria-label="Recall briefing role"
              >
                {briefingRoles.map((role) => (
                  <button
                    key={role}
                    type="button"
                    className={`briefing-role-button ${briefingRole === role ? 'active' : ''}`}
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

        {hasNoResults && (
          <div className="empty-state">
            <h3>No FDA recall records matched this search.</h3>
            <p>
              This does not prove the product is safe or unsafe. It only means no
              matching records were returned from the current openFDA Drug Enforcement
              search. Try searching by brand name, product name, ingredient, or category.
            </p>
          </div>
        )}

        {data && data.results.length > 0 && (
          <div className="results-grid">
            {data.results.map((result) => (
              <article className="recall-card" key={result.recall_number}>
                <div className="recall-card-top">
                  <span className={`risk-pill risk-${result.risk_score.label.toLowerCase()}`}>
                    {result.risk_score.label} signal
                  </span>
                  <strong>{result.risk_score.score}</strong>
                </div>

                <h3>{result.product_description}</h3>

                <p className="reason">{result.reason_for_recall}</p>

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

                <p className="plain-explanation">{riskExplanation(result)}</p>

                <details>
                  <summary>Technical audit details</summary>
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
      </div>
    </section>
  )
}

export default RecallRadar