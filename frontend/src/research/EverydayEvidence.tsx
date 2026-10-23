import type {
  PublicBriefing,
  PublicLabel,
  PublicRecall,
  PublicFaers,
  PublicCoverage,
} from './contracts'
import { Source } from './Evidence'

const formatKey = (key: string) => key.replaceAll('_', ' ')

export function EverydayLimitations({ items }: { items: string[] }) {
  if (!items || items.length === 0) return null
  return (
    <div className="everyday-disclosures">
      <h4>Important Evidence Disclosures</h4>
      <ul>
        {items.map((item, idx) => (
          <li key={idx}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

export function EverydayCoverage({ value }: { value: PublicCoverage }) {
  return (
    <div className="everyday-coverage-pill">
      <span className="coverage-badge">Data Coverage: {value.state}</span>
      <span className="coverage-date">
        Snapshot: {value.source_date ?? value.as_of_date ?? 'frozen release'}
      </span>
      {value.empty_message && <p className="coverage-msg">{value.empty_message}</p>}
    </div>
  )
}

export function EverydayLabelCard({ card }: { card: PublicLabel }) {
  const fields = [
    { key: 'boxed_warning', title: 'Boxed Warning (Black Box)' },
    { key: 'warnings_and_precautions', title: 'Warnings and Precautions' },
    { key: 'warnings', title: 'General Warnings' },
    { key: 'contraindications', title: 'Who Should Not Take This (Contraindications)' },
    { key: 'drug_interactions', title: 'Drug Interactions' },
    { key: 'adverse_reactions', title: 'Documented Adverse Reactions' },
  ] as const

  return (
    <article className="everyday-card everyday-card-label" aria-label="Drug labeling information">
      <div className="everyday-card-header">
        <div className="card-title-group">
          <span className="card-badge badge-label">Official FDA Labeling</span>
          <h3>Prescription & Package Insert Information</h3>
        </div>
        <EverydayCoverage value={card.coverage} />
      </div>

      <p className="everyday-card-intro">
        FDA Structured Product Labeling contains approved medical prescribing guidance, boxed warnings, and precautions specific to this exact pharmaceutical formulation.
      </p>

      {card.records.length === 0 ? (
        <div className="everyday-alert alert-neutral">
          <p className="critical">No admitted exact-product label is available in this frozen evidence release.</p>
          <p>This release contains FDA labels matched directly to product NDCs. A missing stored label does not mean the medication has no warnings.</p>
        </div>
      ) : (
        card.records.map((record) => (
          <div className="everyday-record-block" key={`${record.label_set_id}-${record.label_version}`}>
            <div className="record-meta-bar">
              <span><strong>Version {record.label_version}</strong> (Effective: {record.effective_date})</span>
              <Source url={record.source_url} label="Official FDA Label Source" />
            </div>

            <div className="everyday-sections-list">
              {fields.map(({ key, title }) => {
                const text = record[key]
                return (
                  <details className="everyday-section-accordion" key={key} open={key === 'boxed_warning' && !!text}>
                    <summary className="everyday-section-summary">
                      <span className="section-title">{title}</span>
                      <span className={`section-status-tag ${text ? 'tag-available' : 'tag-missing'}`}>
                        {text ? 'Available' : 'Not listed'}
                      </span>
                    </summary>
                    <div className="everyday-section-content">
                      {text ? (
                        <p className="everyday-prose-text">{text}</p>
                      ) : (
                        <p className="everyday-empty-text">This section is not present in this official FDA label version.</p>
                      )}
                    </div>
                  </details>
                )
              })}
            </div>
          </div>
        ))
      )}

      {card.missing_sections.length > 0 && (
        <p className="everyday-disclaimer-subtle">
          Sections not listed in this label: {card.missing_sections.map(formatKey).join(', ')}.
        </p>
      )}

      <details className="everyday-learn-more">
        <summary>Learn more about FDA Drug Labels</summary>
        <p>
          FDA Structured Product Labels (SPL) are official documents submitted by manufacturers and approved by the FDA. They describe approved uses, contraindications, and known side effects observed in clinical trials.
        </p>
      </details>

      <EverydayLimitations items={card.limitations} />
    </article>
  )
}

export function EverydayRecallCard({ card }: { card: PublicRecall }) {
  const hasRecalls = card.records && card.records.length > 0

  return (
    <article className="everyday-card everyday-card-recall" aria-label="Historical recall evidence">
      <div className="everyday-card-header">
        <div className="card-title-group">
          <span className="card-badge badge-recall">FDA Enforcement</span>
          <h3>Historical Recall Actions</h3>
        </div>
        <EverydayCoverage value={card.coverage} />
      </div>

      <p className="everyday-card-intro">
        Historical FDA recall notices describe enforcement actions taken when a specific batch, lot, or packaging configuration failed quality standards.
      </p>

      {!hasRecalls ? (
        <div className="everyday-alert alert-positive">
          <strong>No historical recalls found for this exact NDC.</strong>
          <p>
            No recall actions were matched to this specific National Drug Code in our frozen dataset.
            <em> Note: Missing historical records do not guarantee that a product has never experienced an action outside our snapshot window.</em>
          </p>
        </div>
      ) : (
        <div className="everyday-recall-records">
          <p className="everyday-recall-count">
            Found {card.returned_count} historical recall record{card.returned_count === 1 ? '' : 's'} linked to this product.
          </p>
          {card.records.map((record) => (
            <div className="everyday-recall-item" key={record.recall_number}>
              <div className="recall-item-head">
                <span className="recall-num">Recall #{record.recall_number}</span>
                <span className="recall-class-badge">{record.classification}</span>
              </div>
              <p className="recall-reason">
                <strong>Reason:</strong> {record.reason_for_recall}
              </p>
              <div className="recall-details-grid">
                <div><strong>Recalling Firm:</strong> {record.recalling_firm ?? 'Firm not recorded'}</div>
                <div><strong>Initiated:</strong> {record.recall_initiation_date ?? 'Date unavailable'}</div>
                <div><strong>Lot Scope:</strong> {record.lot_scope} ({record.lot_information ?? 'See official record'})</div>
                <div><Source url={record.source_url} label="Official Enforcement Notice" /></div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="everyday-alert alert-neutral">
        <p className="critical">
          Lot scope may be unknown or restricted. A matching NDC does not establish that every lot or package is affected.
        </p>
      </div>

      <details className="everyday-learn-more">
        <summary>Understanding FDA Recall Classifications</summary>
        <ul>
          <li><strong>Class I:</strong> High probability of serious adverse health consequences or death.</li>
          <li><strong>Class II:</strong> May cause temporary or medically reversible adverse health consequences.</li>
          <li><strong>Class III:</strong> Not likely to cause adverse health consequences.</li>
        </ul>
      </details>

      <EverydayLimitations items={card.limitations} />
    </article>
  )
}

export function EverydayFaersCard({ card }: { card: PublicFaers }) {
  return (
    <article className="everyday-card everyday-card-faers" aria-label="Reported adverse events">
      <div className="everyday-card-header">
        <div className="card-title-group">
          <span className="card-badge badge-faers">Postmarket Signals</span>
          <h3>Reported Adverse Events (FAERS)</h3>
        </div>
        <EverydayCoverage value={card.coverage} />
      </div>

      <p className="everyday-card-intro">
        The FDA Adverse Event Reporting System (FAERS) collects spontaneous postmarket reports submitted by healthcare professionals and patients.
      </p>

      <div className="everyday-alert alert-warning">
        <strong>Understanding Spontaneous Reporting:</strong>
        <p className="critical">
          These reports are not selected-product or NDC-specific observations. They do not establish causation, incidence, comparative safety or individual risk. Never sum ingredient counts into a product total.
        </p>
      </div>

      {card.records.map((record) => (
        <div className="everyday-ingredient-block" key={record.ingredient_name}>
          <h4>Active Ingredient: {record.ingredient_name}</h4>
          {record.analytics ? (
            <div className="everyday-stats-overview">
              <div className="everyday-stat-tile">
                <span className="stat-label">Total Reports</span>
                <span className="stat-number">{record.analytics.report_count.toLocaleString()}</span>
                <span className="stat-sub">({record.analytics.window_start} – {record.analytics.window_end})</span>
              </div>
              <div className="everyday-stat-tile">
                <span className="stat-label">Serious Reports</span>
                <span className="stat-number">{record.analytics.serious_report_count.toLocaleString()}</span>
                <span className="stat-sub">Hospitalizations, life-threatening, or severe</span>
              </div>
              <div className="everyday-stat-tile">
                <span className="stat-label">Unique Patients</span>
                <span className="stat-number">{record.analytics.unique_case_count.toLocaleString()}</span>
                <span className="stat-sub">Deduplicated case count</span>
              </div>
            </div>
          ) : (
            <p className="everyday-empty-text">Detailed analytics unavailable for this ingredient.</p>
          )}

          {record.top_reported_reactions && record.top_reported_reactions.length > 0 && (
            <div className="everyday-reactions-section">
              <h5>Most Frequently Co-Reported Reactions</h5>
              <p className="reactions-hint">Listed by reporting frequency in the FAERS database:</p>
              <ol className="everyday-reactions-list">
                {record.top_reported_reactions.slice(0, 5).map((item) => (
                  <li key={item.rank} className="reaction-chip">
                    <span className="reaction-name">{item.reaction}</span>
                    <span className="reaction-count">({item.co_report_activity} reports)</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {record.source && (
            <div className="everyday-source-row">
              <Source url={record.source.source_url} label="Official FAERS Database Source" />
              <span>Export: {record.source.export_date}</span>
            </div>
          )}
        </div>
      ))}

      <div className="everyday-alert alert-neutral">
        <strong>The Non-Summing Rule:</strong> For combination medications with multiple ingredients, report counts cannot be added together. Doing so falsely doubles report totals because single patient reports often list multiple ingredients.
      </div>

      <details className="everyday-learn-more">
        <summary>Why FAERS Cannot Give You a "Safety Score"</summary>
        <p>
          FAERS does not track the total number of people taking a medication (the denominator), so it is impossible to calculate the true incidence rate or percentage of patients affected. Never compare raw report numbers between different medications.
        </p>
      </details>

      <EverydayLimitations items={card.limitations} />
    </article>
  )
}

export function EverydayBriefing({ briefing }: { briefing: PublicBriefing }) {
  const headings: Record<string, string> = {
    labels: 'Drug Labeling',
    recalls: 'Historical Recalls',
    faers: 'Adverse Events (FAERS)',
  }

  return (
    <section className="everyday-results-container briefing" aria-label="Research briefing">
      <div className="everyday-summary-banner">
        <div className="banner-drug-info">
          <span className="eyebrow">Medication Information Summary</span>
          <h2>{briefing.medication.brand_names.join(', ') || briefing.medication.generic_name}</h2>
          <p className="banner-specs">
            {briefing.medication.strength} · {briefing.medication.dosage_form} · NDC {briefing.medication.product_ndcs.join(', ')}
          </p>
        </div>
        <div className="banner-status-pill">
          <span className="status-label">Evidence Status:</span>
          <span className="status-val">{briefing.status.toUpperCase()}</span>
        </div>
      </div>

      <div className="everyday-cards-grid">
        {briefing.sections
          .filter((section) => section.status !== 'not_requested')
          .map((section) => (
            <div key={section.category} className="everyday-category-section">
              {section.evidence ? (
                section.evidence.type === 'drug_label_evidence' ? (
                  <EverydayLabelCard card={section.evidence} />
                ) : section.evidence.type === 'historical_recall_evidence' ? (
                  <EverydayRecallCard card={section.evidence} />
                ) : (
                  <EverydayFaersCard card={section.evidence} />
                )
              ) : (
                <article className="everyday-card">
                  <div className="everyday-card-header">
                    <h3>{headings[section.category] ?? section.category}</h3>
                    <span className="card-badge badge-neutral">{section.status}</span>
                  </div>
                  <p className="everyday-empty-text">
                    {section.reason ? formatKey(section.reason) : 'No evidence records available in this frozen release.'}
                  </p>
                </article>
              )}
            </div>
          ))}
      </div>

      <section className="everyday-card everyday-governance-card">
        <h3>Research Scope & Governance</h3>
        <EverydayLimitations items={briefing.limitations} />
        <details>
          <summary>Research execution details</summary>
          <p>
            {briefing.routing.mode === 'model'
              ? 'Native model-directed tool planning'
              : briefing.routing.mode === 'deterministic'
                ? 'Explicit deterministic execution · no model planning'
                : 'Deterministic completion of an incomplete model plan'}
          </p>
          <p>Model selected: {briefing.routing.model_planned_tools.join(', ') || 'none'}</p>
          <p>Backend selected: {briefing.routing.backend_completed_tools.join(', ') || 'none'}</p>
          <p>Evidence is verified and assembled by the backend. Model narrative is not used.</p>
        </details>
        <p className="everyday-disclaimer-footer">
          This educational evidence summary was retrieved from a frozen, read-only FDA release. It does not provide medical advice, diagnosis, or personalized treatment recommendations. Always consult a licensed healthcare professional for medical decisions.
        </p>
      </section>
    </section>
  )
}
