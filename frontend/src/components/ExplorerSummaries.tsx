import type { DrugEvidence, DrugSafety } from '../api/drugCatalog'
import { EvidenceBar } from './EvidencePanel'

export function RecallSummary({ evidence }: { evidence: DrugEvidence }) {
  const records = evidence.recalls.records
  const classes = [...new Set(records.map(item => item.classification || 'Unspecified'))]
  const counts = classes.map(label => ({ label, value: records.filter(record => (record.classification || 'Unspecified') === label).length }))
  return <><p className="summary-scope">Coverage: {evidence.recalls.coverage.state}</p>
    <p className="summary-number">{records.length}<small>linked records in this response</small></p>
    {counts.map(item => <EvidenceBar key={item.label} {...item} max={Math.max(...counts.map(row => row.value))} unit="historical recall records" />)}
    <p className="summary-limit">Historical links do not establish current recall status or that all lots were affected. Missing links do not mean the product has never been recalled.</p></>
}

export function FaersSummary({ evidence }: { evidence: DrugEvidence }) {
  return <><p className="summary-scope">Coverage: {evidence.adverse_events.coverage.state}</p>
    {evidence.adverse_events.records.slice(0, 2).map(ingredient => {
      const analytics = ingredient.analytics
      const rows = ingredient.top_reported_reactions.filter(row => Number.isSafeInteger(row.co_report_activity) && row.co_report_activity >= 0).slice(0, 3)
      return <div className="ingredient-bars" key={ingredient.ingredient_id}><strong>{ingredient.ingredient_name}</strong>
        {analytics ? <><p className="summary-window">{analytics.window_start} → {analytics.window_end}</p>
          <p className="summary-unit">Reaction co-report activity · relative to the largest shown value for this ingredient</p>
          {rows.map(row => <EvidenceBar key={row.rank} label={row.reaction} value={row.co_report_activity} max={Math.max(...rows.map(item => item.co_report_activity))} unit="reaction co-report activity" />)}
          {!rows.length && <p>No stored top-reaction rows available.</p>}</>
          : <p>No stored analytics available for this ingredient. Missing data is not a zero count.</p>}
      </div>
    })}
    {evidence.adverse_events.records.length > 2 && <p>Additional ingredients appear in the expanded records.</p>}
    {!evidence.adverse_events.records.length && <p>No ingredient reporting records in this response.</p>}
    <p className="summary-limit">Ingredient-level reporting only. Not causation, incidence, patient counts or individual risk. Do not add ingredients into a product total.</p></>
}

const labelFields = ['boxed_warning', 'warnings_and_precautions', 'warnings', 'contraindications', 'adverse_reactions', 'drug_interactions'] as const
export type LabelEvidence = DrugSafety['labels'] & { drug_id: string }
export function LabelSummary({ labels }: { labels?: LabelEvidence }) {
  const selected = labels?.records.filter(record => record.selection_status === 'SELECTED_STORED') ?? []
  return <><p className="summary-scope">Coverage: {labels?.coverage.state ?? 'Not established'}</p>
    <p className="summary-unit">Selected exact-product label sections · presence, not severity</p>
    <ul className="label-presence">{labelFields.map(field => {
      const present = selected.some(record => typeof record[field] === 'string' && !!record[field]?.trim())
      return <li key={field}><span>{field.replaceAll('_', ' ')}</span><strong>{present ? 'Stored' : 'Not established'}</strong><span className={present ? 'is-present' : ''} aria-hidden="true" /></li>
    })}</ul>
    <p className="summary-limit">Missing label text does not mean no warnings exist. Expand to inspect versions, provenance and section states.</p></>
}
