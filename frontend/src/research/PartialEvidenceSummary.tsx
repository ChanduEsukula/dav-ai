import type { PublicBriefing, PublicCoverage, PublicSection } from './contracts'
import { isOfficialFdaUrl } from '../utils/sourceUrl'

// This recognizes only general evidence-inventory requests. Category keywords
// cannot establish that a clinical, temporal, comparative, or personal question
// was answered. Unknown words/scope therefore abstain, including mixed questions.
function inventoryScope(briefing: PublicBriefing) {
  let question = briefing.question?.trim().toLowerCase() ?? ''
  if (!question) return null
  for (const name of [...briefing.medication.brand_names, briefing.medication.generic_name,
    ...briefing.medication.active_ingredients].filter((name): name is string => !!name)) {
    const escaped = name.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    question = question.replace(new RegExp(`\\b${escaped}\\b`, 'g'), ' ')
  }
  question = question.replace(/[-–]/g, ' ').replace(/\bshow me\b/g, 'show')
  const labels = /\b(label(?:ing|s)?|warnings?|boxed|contraindications?|interactions?|precautions?|package insert)\b/.test(question)
  const recalls = /\b(recalls?|recalled|enforcement actions?)\b/.test(question)
  const faers = /\b(faers|adverse[ -]events?|reported reactions?|spontaneous reports?|postmarket reporting)\b/.test(question)
  const rest = question.replace(/\b(label(?:ing|s)?|warnings?|boxed|contraindications?|interactions?|precautions?|package insert|recalls?|recalled|enforcement actions?|faers|adverse[ -]events?|reported reactions?|spontaneous reports?|postmarket reporting)\b/g, ' ')
    .replace(/\b(what|which|are|is|the|a|an|and|or|of|for|on|in|this|medication|product|drug|available|stored|historical|evidence|records?|reports?|show|list|summarize|please|about|has|been)\b/g, ' ')
  if (/[^\s?,.]/.test(rest) || !(labels || recalls || faers)) return null
  return { labels, recalls, faers }
}

function usable(section: PublicSection | undefined) {
  return section?.status === 'available' || section?.status === 'incomplete'
}

function Coverage({ coverage }: { coverage: PublicCoverage }) {
  return <p>Coverage: {coverage.state}. {coverage.bounded && 'Bounded evidence. '}
    {coverage.truncated && 'Stored results are truncated. '}
    See the evidence card for coverage details and source limitations.</p>
}

export function PartialEvidenceSummary({ briefing }: { briefing: PublicBriefing }) {
  const scope = inventoryScope(briefing)
  if (!scope) return null
  const productRef = briefing.medication.product_ref
  const section = (category: PublicSection['category']) => briefing.requested_categories.includes(category)
    ? briefing.sections.find(item => item.category === category) : undefined
  const labelSection = scope.labels ? section('labels') : undefined
  const recallSection = scope.recalls ? section('recalls') : undefined
  const faersSection = scope.faers ? section('faers') : undefined
  const labels = usable(labelSection) && labelSection?.evidence?.type === 'drug_label_evidence'
    && labelSection.evidence.product_ref === productRef ? labelSection.evidence : null
  const recalls = usable(recallSection) && recallSection?.evidence?.type === 'historical_recall_evidence'
    && recallSection.evidence.product_ref === productRef
    && recallSection.evidence.product?.product_ref === productRef ? recallSection.evidence : null
  const faers = usable(faersSection) && faersSection?.evidence?.type === 'faers_reporting_evidence'
    && faersSection.evidence.product_ref === productRef ? faersSection.evidence : null
  const ingredients = faers?.records.filter(record => record.scope === 'INGREDIENT'
    && briefing.medication.active_ingredients.some(name => name.toLowerCase() === record.ingredient_name.toLowerCase())
    && record.analytics !== null && record.source !== null
    && record.analytics.count_unit === 'deduplicated ingredient-report associations'
    && Number.isSafeInteger(record.analytics.report_count) && record.analytics.report_count >= 0) ?? []
  const labelRecords = labels?.records.filter(record => record.applicability_class === 'EXACT_PRODUCT'
    && record.evidence_scope === 'PRODUCT' && record.selection_status === 'SELECTED_STORED') ?? []
  const requested = [labelSection, recallSection, faersSection].filter((item): item is PublicSection => !!item)
  if (!requested.length) return null

  return <section className="partial-evidence-summary" aria-label="Available evidence summary">
    <h3>Stored evidence for the submitted question</h3>
    <p>Submitted question: {briefing.question}</p>
    <p>This deterministic inventory does not establish that a medical claim in the question is supported.</p>
    {!!recalls?.records.length && <section>
      <h4>Historical recall findings</h4>
      <p>{recalls.records.length} historical recall {recalls.records.length === 1 ? 'record is' : 'records are'} present
        {' '}in this briefing for the confirmed product.</p>
      <ul>{recalls.records.slice(0, 3).map(record => <li key={record.source_record_id}>
        <strong>Recall {record.recall_number}</strong> · Lot scope: {record.lot_scope}
        {record.lot_information && <> · {record.lot_information}</>}
        {isOfficialFdaUrl(record.source_url) && <> · <a href={record.source_url} target="_blank" rel="noopener noreferrer">FDA source</a></>}
      </li>)}</ul>
      <p>Historical links do not establish current recall status or that every package or lot was affected.</p>
      {recalls.results_truncated && <p>Recall results are truncated; this is not the full stored record count.</p>}
      <Coverage coverage={recalls.coverage} />
    </section>}
    {ingredients.length > 0 && <section>
      <h4>FAERS reporting evidence</h4>
      <ul>{ingredients.map(record => <li key={record.ingredient_name}>
        <strong>{record.ingredient_name}</strong> — {record.analytics!.report_count.toLocaleString()}
        {' stored ingredient-report associations within '}{record.analytics!.window_start} to {record.analytics!.window_end}
        {isOfficialFdaUrl(record.source!.source_url) && <> · <a href={record.source!.source_url} target="_blank" rel="noopener noreferrer">FDA dataset source</a></>}
        <Coverage coverage={record.coverage} />
      </li>)}</ul>
      <p>Ingredient-level reporting associations are not verified reactions caused by this NDC.
        Counts are not incidence, patient risk, or proof of causation. Do not sum ingredients into a product total.</p>
      {ingredients.length < faers!.records.length && <p>Some ingredient records lack usable analytics or provenance; only usable records are shown.</p>}
      <Coverage coverage={faers!.coverage} />
    </section>}
    {labelRecords.length > 0 && <section>
      <h4>Drug-label evidence available</h4>
      <p>Selected exact-product label records appear in the label evidence card.
        Their availability does not establish an answer about a warning, contraindication, or interaction.</p>
      <Coverage coverage={labels!.coverage} />
    </section>}
    {requested.filter(item => item.category === 'labels' ? labelRecords.length === 0
      : item.category === 'recalls' ? !recalls?.records.length : ingredients.length === 0).map(item => <section key={item.category}>
      <h4>{item.category === 'labels' ? 'Drug-label evidence unavailable' : `${item.category === 'faers' ? 'FAERS' : 'Recall'} evidence unavailable`}</h4>
      <p>No usable evidence for this category is established in this briefing (section status: {item.status}).
        {item.category === 'labels' ? ' Missing label evidence does not mean that no warnings exist.'
          : item.category === 'recalls' ? ' Missing linked records do not mean the product has never been recalled.'
            : ' Missing analytics do not mean no adverse events were reported.'}</p>
    </section>)}
    <p><strong>Evidence remains incomplete.</strong> Frozen records do not establish overall medication safety
      or provide individualized medical advice. Source links and full provenance appear in the evidence cards below.</p>
  </section>
}
