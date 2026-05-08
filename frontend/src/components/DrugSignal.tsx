import { useMemo, useState } from 'react'
import {
  searchDrugEvents,
  type DrugEventSearchResponse,
} from '../api/drugEvents'
import SafetyBriefingPanel from './SafetyBriefingPanel'
import { formatTimestamp } from '../utils/recallFormatters'
import { generateDrugEventBriefing } from '../utils/briefingGenerator'
import { briefingRoleLabels, type BriefingRole } from '../types/briefing'

const briefingRoles: BriefingRole[] = ['consumer', 'pharmacy', 'clinic', 'public_health']

function DrugSignal() {
  const [query, setQuery] = useState('')
  const [data, setData] = useState<DrugEventSearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [briefingRole, setBriefingRole] = useState<BriefingRole>('consumer')

  async function handleSearch() {
    const trimmedQuery = query.trim()

    if (!trimmedQuery) {
      setError('Enter a drug or medicinal product name to search FAERS reports.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await searchDrugEvents(trimmedQuery, 10)
      setData(response)
    } catch {
      setError(
        'Unable to load drug event data. Make sure the FastAPI backend is running on port 8000.'
      )
    } finally {
      setLoading(false)
    }
  }

  const hasNoResults = data && data.top_reactions.length === 0
  const maxReactionCount =
    data?.top_reactions.reduce((max, item) => Math.max(max, item.count), 0) ?? 0

  const briefing = useMemo(() => {
    if (!data) return null

    return generateDrugEventBriefing(data, briefingRole)
  }, [data, briefingRole])

  return (
    <section className="drugsignal reveal" id="drugsignal">
      <div className="section-heading">
        <p className="eyebrow">DrugSignal module</p>
        <h2>Explore public FAERS adverse-event reporting patterns.</h2>
        <p>
          Search a drug or medicinal product to view top reported reactions from
          openFDA Drug Event records. These reports are safety signals only and do
          not prove causation.
        </p>
      </div>

      <div className="drug-signal-panel">
        <div className="search-box">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                handleSearch()
              }
            }}
            placeholder="Search FAERS reports: metformin, ibuprofen, aspirin"
          />
          <button onClick={handleSearch} disabled={loading}>
            {loading ? 'Checking public data...' : 'Analyze'}
          </button>
        </div>

        {loading && (
          <p className="loading-helper">
            This may take a few seconds while the secure backend wakes up and checks public FAERS reporting data.
          </p>
        )}

        {error && <p className="error-message">{error}</p>}

        {data && (
          <div className="source-strip">
            <span>{data.count} FAERS records reviewed</span>
            <span>{data.source_name}</span>
            <span>Retrieved {formatTimestamp(data.retrieval_timestamp)}</span>
          </div>
        )}

        {data && (
          <div className="drug-intelligence-card">
            <div>
              <p className="eyebrow">DrugSignal Intelligence</p>
              <h3>{data.intelligence_score.score} / 100</h3>
              <p>
                Transparent signal score based on returned public FAERS records,
                reaction concentration, reaction diversity, and data confidence.
              </p>
            </div>

            <div className="drug-intelligence-grid">
              <div>
                <small>Signal strength</small>
                <span>{data.intelligence_score.label}</span>
              </div>

              <div>
                <small>Review priority</small>
                <span>{data.intelligence_score.review_priority}</span>
              </div>

              <div>
                <small>Data confidence</small>
                <span>{data.intelligence_score.data_confidence}</span>
              </div>

              <div>
                <small>Top reaction concentration</small>
                <span>{data.intelligence_score.top_reaction_concentration}%</span>
              </div>

              <div>
                <small>Score version</small>
                <span>{data.intelligence_score.score_version}</span>
              </div>
            </div>

            <ul className="drug-intelligence-limitations">
              {data.intelligence_score.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </div>
        )}

        {data && data.reaction_categories.length > 0 && (
          <div className="reaction-category-card">
            <div>
              <p className="eyebrow">Reaction Classification</p>
              <h3>Reaction categories</h3>
              <p>
                Rule-based NLP-style grouping of returned top reactions into
                explainable safety-signal categories.
              </p>
            </div>

            <div className="reaction-category-list">
              {data.reaction_categories.map((category) => (
                <div className="reaction-category-row" key={category.category}>
                  <div>
                    <span>{category.category}</span>
                    <small>{category.reactions.join(', ')}</small>
                  </div>

                  <strong>{category.count}</strong>
                </div>
              ))}
            </div>

            <p className="reaction-classifier-version">
              Classifier version: {data.reaction_classifier_version}
            </p>
          </div>
        )}

        {data && (
          <div className="drug-trend-card">
            <div>
              <p className="eyebrow">DrugSignal Trend Snapshot</p>
              <h3>{data.trend_snapshot.label}</h3>
              <p>{data.trend_snapshot.explanation}</p>
            </div>

            <div className="drug-trend-grid">
              <div>
                <small>Current records</small>
                <span>{data.trend_snapshot.current_record_count}</span>
              </div>

              <div>
                <small>Previous records</small>
                <span>{data.trend_snapshot.previous_record_count ?? 'N/A'}</span>
              </div>

              <div>
                <small>Previous audit ID</small>
                <span>{data.trend_snapshot.previous_audit_id ?? 'N/A'}</span>
              </div>

              <div>
                <small>Previous timestamp</small>
                <span>
                  {data.trend_snapshot.previous_created_at
                    ? formatTimestamp(data.trend_snapshot.previous_created_at)
                    : 'N/A'}
                </span>
              </div>

              <div>
                <small>Trend version</small>
                <span>{data.trend_snapshot.trend_version}</span>
              </div>
            </div>

            <p className="drug-trend-limitation">
              {data.trend_snapshot.limitation}
            </p>
          </div>
        )}

        {data && (
          <div className="drug-audit-panel">
            <div className="metadata-grid">
              <div>
                <small>Data Source</small>
                <span>{data.source_name}</span>
              </div>

              <div>
                <small>Endpoint</small>
                <span>{data.endpoint}</span>
              </div>

              <div>
                <small>Search Query</small>
                <span>{data.query}</span>
              </div>

              <div>
                <small>Record Count</small>
                <span>{data.count}</span>
              </div>

              <div>
                <small>Audit ID</small>
                <span>{data.audit.audit_id}</span>
              </div>

              <div>
                <small>Source ID</small>
                <span>{data.audit.source_id}</span>
              </div>

              <div>
                <small>Module</small>
                <span>{data.audit.module}</span>
              </div>

              <div>
                <small>Upstream Status</small>
                <span>{data.audit.upstream_status}</span>
              </div>

              <div>
                <small>Transform Version</small>
                <span>{data.audit.transform_version}</span>
              </div>
            </div>

            <p className="disclaimer">{data.faers_disclaimer}</p>
            <p className="disclaimer">{data.medical_disclaimer}</p>
          </div>
        )}

        {briefing && (
          <div className="briefing-control-panel">
            <div className="briefing-role-selector">
              <span>Briefing role</span>

              <div
                className="briefing-role-buttons"
                role="group"
                aria-label="Drug briefing role"
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
            <h3>No FAERS drug-event records matched this search.</h3>
            <p>
              This does not prove the drug is safe or unsafe. It only means no
              matching records were returned from the current openFDA Drug Event
              search. Try searching by generic name, brand name, or active ingredient.
            </p>
          </div>
        )}

        {data && data.top_reactions.length > 0 && (
          <div className="reaction-list">
            <h3>Top reported reactions</h3>

            {data.top_reactions.map((item) => {
              const barWidth =
                maxReactionCount > 0 ? `${(item.count / maxReactionCount) * 100}%` : '0%'

              return (
                <div className="reaction-row" key={item.reaction}>
                  <div className="reaction-main">
                    <span>{item.reaction}</span>
                    <div className="reaction-bar-track">
                      <div className="reaction-bar-fill" style={{ width: barWidth }} />
                    </div>
                  </div>

                  <strong>{item.count}</strong>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </section>
  )
}

export default DrugSignal