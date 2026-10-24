import type { PublicBriefing } from './contracts'
import { labelAnchor } from './evidenceAnchors'

function openSource(id: string) {
  const target = document.getElementById(id)
  if (!target) return
  const details = target.closest('details')
  if (details) details.open = true
  target.focus()
  target.scrollIntoView?.({ block: 'center', behavior: 'smooth' })
}

export function GroundedAnswerPanel({ briefing }: { briefing: PublicBriefing }) {
  const answer = briefing.answer
  if (!answer) return null
  const citations = new Map(answer.citations.map(c => [c.evidence_id, c]))
  const labels = briefing.sections.find(s => s.category === 'labels' && s.evidence?.type === 'drug_label_evidence')?.evidence
  const valid = answer.product_ref === briefing.medication.product_ref && answer.citations.length > 0
    && answer.citations.every(c => c.category === 'labels' && c.product_ref === answer.product_ref
      && labels?.type === 'drug_label_evidence' && labels.product_ref === answer.product_ref
      && labels.records.some(r => r.source_record_id === c.source_record_id && r.label_set_id === c.label_set_id
        && r.label_version === c.label_version && r.source_url === c.source_url))
    && (answer.text?.match(/\[E\d+\]/g) ?? []).length >= answer.citations.length
    && (answer.text?.match(/\[E\d+\]/g) ?? []).every(tag => citations.has(tag.slice(1, -1)))
  const generated = answer.status === 'generated' && valid && !!answer.text
  const fallback = answer.status === 'insufficient_evidence'
    ? 'Evidence is insufficient for a grounded answer to this question. Review the structured evidence below.'
    : answer.status === 'unavailable'
      ? 'AI synthesis is unavailable. The structured evidence remains available below.'
      : 'AI output failed validation and was discarded. Review the structured evidence below.'
  return <section className="panel everyday-card grounded-answer" aria-label="AI-generated answer">
    <h2>AI-generated answer</h2>
    {generated ? <>
      <p>AI-selected summary using quoted label statements. This is separate from the original FDA source cards.</p>
      <p>{answer.text!.split(/(\[E\d+\])/).map((part, index) => {
        const citation = citations.get(part.slice(1, -1))
        if (!/^\[E\d+\]$/.test(part) || !citation) return <span key={index}>{part}</span>
        const target = labelAnchor(citation, citation.section)
        return <a key={index} href={`#${target}`} onClick={() => openSource(target)}
          aria-label={`${part} Open ${citation.section.replaceAll('_', ' ')} source`}>{part}</a>
      })}</p>
    </> : <p role="status">{fallback}</p>}
    <p>Citation checks do not establish factual support or clinical completeness. Not individualized medical advice.</p>
    <details><summary>Answer provenance and limitations</summary>
      {generated && <ul>{answer.citations.map(c => <li key={c.evidence_id}>
        [{c.evidence_id}] {c.source_record_id} · Label {c.label_version} · Snapshot {c.source_snapshot_date} · Release {c.release_id}
      </li>)}</ul>}
      <ul>{answer.limitations.map(item => <li key={item}>{item}</li>)}</ul>
    </details>
  </section>
}
