import { useId, useState, type ReactNode } from 'react'
import { EvidenceIcon, type EvidenceKind } from '../portfolio/EvidenceIcon'

export function EvidencePanel({ kind, title, scope, summary, children }: {
  kind: EvidenceKind; title: string; scope: string; summary: ReactNode; children: ReactNode
}) {
  const [expanded, setExpanded] = useState(false)
  const id = useId()
  return <section className={`panel evidence-glass-panel evidence-${kind}${expanded ? ' is-expanded' : ''}`} aria-labelledby={`${id}-title`}>
    <div className="evidence-panel-heading"><span className="immersive-icon"><EvidenceIcon kind={kind} /></span>
      <div><p className="eyebrow">{scope}</p><h2 id={`${id}-title`}>{title}</h2></div></div>
    <div className="evidence-panel-summary">{summary}</div>
    <button className="evidence-expand" aria-expanded={expanded} aria-controls={`${id}-records`} onClick={() => setExpanded(value => !value)}>
      {expanded ? 'Collapse' : 'Expand'} {title}<span aria-hidden="true">{expanded ? '−' : '+'}</span>
    </button>
    <div className="evidence-panel-records" id={`${id}-records`} hidden={!expanded}>{children}</div>
  </section>
}

export function EvidenceBar({ label, value, max, unit }: { label: string; value: number; max: number; unit: string }) {
  if (!Number.isSafeInteger(value) || value < 0 || !Number.isSafeInteger(max) || max < value) return null
  return <div className="evidence-bar" role="group" aria-label={`${label}: ${value.toLocaleString()} ${unit}`}>
    <div><span>{label}</span><strong>{value.toLocaleString()}</strong></div>
    <div className="evidence-bar-track" aria-hidden="true"><span style={{ width: `${max > 0 ? value / max * 100 : 0}%` }} /></div>
  </div>
}
