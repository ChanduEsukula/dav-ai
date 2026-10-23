import type { PublicBriefing, PublicLabel, PublicRecall, PublicFaers, PublicCoverage } from './contracts'
import { isOfficialFdaUrl } from '../utils/sourceUrl'

const name = (key: string) => key.replaceAll('_', ' ')
export function Source({ url, label }: { url: string; label: string }) {
  const valid = isOfficialFdaUrl(url)
  return valid ? <a href={url} target="_blank" rel="noopener noreferrer">{label} ↗</a> : <span>Source URL unavailable · {label}</span>
}
export function Limitations({ items }: { items: string[] }) {
  const groups: Record<string, string[]> = {
    'Evidence availability and coverage': [], 'Historical recall applicability': [],
    'FAERS interpretation': [], 'Data freshness and provenance': [], 'Medical-use limitations': [],
  }
  for (const item of [...new Set(items)]) {
    const key = /medical|individualized|advice|endorsement/i.test(item) ? 'Medical-use limitations'
      : /faers|causat|incidence|ingredient|co-report|risk score/i.test(item) ? 'FAERS interpretation'
        : /recall|lot|package/i.test(item) ? 'Historical recall applicability'
          : /frozen|live|snapshot|source|provenance|date/i.test(item) ? 'Data freshness and provenance'
            : 'Evidence availability and coverage'
    groups[key].push(item)
  }
  return <div className="research-limitations">{Object.entries(groups).filter(([, rows]) => rows.length).map(([heading, rows]) => <details key={heading}><summary>{heading} ({rows.length})</summary><ul>{rows.map(row => <li key={row}>{row}</li>)}</ul></details>)}</div>
}
function Coverage({ value }: { value: PublicCoverage }) {
  return <div className="coverage"><strong>Coverage: {value.state}</strong><p>{value.reason_code && name(value.reason_code)} · Snapshot: {value.source_date ?? value.as_of_date ?? 'unavailable'}</p>{value.empty_message && <p>{value.empty_message}</p>}<Limitations items={value.limitations} /></div>
}
export function Labels({ card }: { card: PublicLabel }) {
  const fields = ['boxed_warning', 'warnings_and_precautions', 'warnings', 'contraindications', 'drug_interactions', 'adverse_reactions'] as const
  return <><p className="scope">Exact-product label evidence · no ingredient substitution</p><Coverage value={card.coverage} />
    {!card.records.length && <p className="critical">No admitted exact-product label is available in this frozen evidence release.</p>}
    <p>Missing labels or sections do not mean this medication has no warnings.</p>
    {card.records.map(row => <article className="record" key={`${row.label_set_id}-${row.label_version}`}><h3>Label version {row.label_version}</h3><p>Effective {row.effective_date} · {name(row.selection_status)} · {name(row.applicability_class)}</p><p>Link: {row.match_method} · {row.matched_value}</p><Source url={row.source_url} label={`${row.source} · ${row.source_record_id}`} />{fields.map(field => <details key={field}><summary>{name(field)} · {row[field] ? 'stored text' : 'unavailable'}</summary><p className="label-text">{row[field] ?? 'This section is unavailable in the admitted stored label.'}</p></details>)}</article>)}
    {card.missing_sections.length > 0 && <p>Missing sections: {card.missing_sections.map(name).join(', ')}</p>}<Limitations items={card.limitations} /></>
}
export function Recalls({ card }: { card: PublicRecall }) {
  return <><p className="scope">Historical product/package evidence</p><Coverage value={card.coverage} /><p className="critical">Lot scope may be unknown or restricted. A matching NDC does not establish that every lot or package is affected.</p><p>{card.interpretation}</p><p>{card.returned_count} of {card.record_count} stored records · {card.results_truncated ? 'truncated' : 'bounded result'}</p>{card.records.map(row => <article className="record" key={row.recall_number}><h3>{row.recall_number} · {row.classification}</h3><p>{row.reason_for_recall}</p><p>{row.recalling_firm ?? 'Firm unavailable'} · reported status: {row.reported_status ?? 'unavailable'}</p><p>Initiated: {row.recall_initiation_date ?? 'unavailable'} · Reported: {row.report_date ?? 'unavailable'}</p><p>Applicability: {name(row.applicability_class)} · {row.match_method} · {row.matched_value}</p><p>Lot scope: {row.lot_scope} · {row.lot_information ?? 'Lot information unavailable'}</p><Source url={row.source_url} label={`FDA recall source · ${row.source_record_id}`} /></article>)}<Limitations items={card.limitations} /></>
}
export function Faers({ card }: { card: PublicFaers }) {
  return <><p className="scope">Ingredient-level reporting associations</p><p className="critical">These reports are not selected-product or NDC-specific observations. They do not establish causation, incidence, comparative safety or individual risk. Never sum ingredient counts into a product total.</p><Coverage value={card.coverage} />{card.records.map(row => <article className="record" key={row.ingredient_name}><h3>{row.ingredient_name}</h3><Coverage value={row.coverage} />{row.analytics ? <><p>Reporting period: {row.analytics.window_start} – {row.analytics.window_end}</p><p>{row.analytics.count_unit} · {row.analytics.date_basis}</p><dl className="research-counts">{(['report_count', 'unique_case_count', 'serious_report_count', 'serious_known_report_count', 'death_report_count', 'hospitalization_report_count', 'disability_report_count', 'life_threatening_report_count', 'suspect_report_count', 'concomitant_report_count', 'interacting_report_count'] as const).map(key => <div key={key}><dt>{name(key)}</dt><dd>{row.analytics![key]}</dd></div>)}</dl><h4>Ranked reaction co-reporting terms</h4><ol>{row.top_reported_reactions.slice(0, 5).map(reaction => <li key={reaction.rank}>{reaction.reaction} · {reaction.co_report_activity} co-report activity · {reaction.active_months} active months</li>)}</ol>{row.top_reported_reactions.length > 5 && <details><summary>All ranked reaction terms ({row.top_reported_reactions.length})</summary><ol start={6}>{row.top_reported_reactions.slice(5).map(reaction => <li key={reaction.rank}>{reaction.reaction} · {reaction.co_report_activity} co-report activity · {reaction.active_months} active months</li>)}</ol></details>}<details><summary>Stored monthly reporting associations</summary><ul>{row.monthly.map(month => <li key={month.period}>{month.period}: {month.report_count} associations; {month.serious_report_count} serious</li>)}</ul></details><Limitations items={row.analytics.limitations} /></> : <p>Reporting analytics unavailable for this ingredient.</p>}{row.source && <><p><Source url={row.source.source_url} label={row.source.source_name} /> · Export {row.source.export_date} · Observed {row.source.observed_at ?? 'unavailable'}</p><details><summary>Stored source provenance</summary><p>Source record: {row.source.source_id}</p></details></>}</article>)}<p>{card.summary.limitation}</p><Limitations items={card.limitations} /></>
}
export function Briefing({ value }: { value: PublicBriefing }) {
  const headings = { labels: 'Drug labeling', recalls: 'Historical recalls', faers: 'FAERS reporting evidence' }
  return <section className="briefing" aria-label="Research briefing"><div className="research-result-header"><div><p className="eyebrow">Verified evidence briefing</p><h2>{value.medication.brand_names.join(', ') || value.medication.generic_name}</h2><p>{value.medication.strength} · {value.medication.dosage_form} · NDC {value.medication.product_ndcs.join(', ')}</p><p>Requested: {value.requested_categories.map(key => headings[key]).join(', ')}</p></div><strong className="research-status">{value.status}</strong></div>
    <div className="research-evidence">{value.sections.filter(section => section.status !== 'not_requested').map(section => <section className="panel" key={section.category}><div className="research-panel-heading"><h2>{headings[section.category]}</h2><span>{section.status}</span></div>{section.reason && <p className="critical">{name(section.reason)}</p>}{section.evidence && <><p className="snapshot">Release: {section.evidence.release.release_id} · Schema {section.evidence.release.schema_version} · Build {section.evidence.release.build_time_utc}</p>{section.evidence.type === 'drug_label_evidence' ? <Labels card={section.evidence} /> : section.evidence.type === 'historical_recall_evidence' ? <Recalls card={section.evidence} /> : <Faers card={section.evidence} />}</>}</section>)}</div>
    <section className="panel research-disclosures"><h2>Research limitations</h2><Limitations items={value.limitations} /><details><summary>Research execution details</summary><p>{value.routing.mode === 'model' ? 'Native model-directed tool planning' : value.routing.mode === 'deterministic' ? 'Explicit deterministic execution · no model planning' : 'Deterministic completion of an incomplete model plan'}</p><p>Model selected: {value.routing.model_planned_tools.join(', ') || 'none'}</p><p>Backend selected: {value.routing.backend_completed_tools.join(', ') || 'none'}</p><p>Evidence is verified and assembled by the backend. Model narrative is not used.</p></details></section></section>
}
