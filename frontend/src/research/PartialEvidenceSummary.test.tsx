import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import fixture from './briefing.fixture.json'
import type { PublicBriefing } from './contracts'
import { PartialEvidenceSummary } from './PartialEvidenceSummary'

function briefing(question: string): PublicBriefing {
  const value = structuredClone(fixture) as PublicBriefing
  value.question = question
  return value
}
function summary(question: string) {
  render(<PartialEvidenceSummary briefing={briefing(question)} />)
  return screen.queryByRole('region', { name: 'Available evidence summary' })
}

describe('question-bound deterministic evidence inventory', () => {
  it('supports the workspace default inventory question', () => {
    const panel = summary('What historical recalls, drug-label warnings, and adverse-event reports are available for this medication?')!
    expect(within(panel).getByText(/D-TEST-2016/)).toBeInTheDocument()
    expect(within(panel).getByText(/stored ingredient-report/)).toBeInTheDocument()
  })
  it('displays recalls only for a recall inventory question', () => {
    const panel = summary('What historical recalls are available?')!
    expect(within(panel).getByText(/Recall D-TEST-2016/)).toBeInTheDocument()
    expect(within(panel).queryByText(/stored ingredient-report/)).not.toBeInTheDocument()
    expect(within(panel).queryByText('Drug-label evidence unavailable')).not.toBeInTheDocument()
    expect(within(panel).getByText(/current recall status/)).toBeInTheDocument()
    expect(within(panel).getByText(/Lot scope: UNKNOWN/)).toBeInTheDocument()
  })
  it('displays ingredient-level reports only for a FAERS inventory question', () => {
    const panel = summary('What FAERS adverse-event reports are available?')!
    expect(within(panel).getByText(/2 stored ingredient-report associations/)).toBeInTheDocument()
    expect(within(panel).queryByText(/D-TEST-2016/)).not.toBeInTheDocument()
    expect(within(panel).getByText(/not incidence, patient risk, or proof of causation/)).toBeInTheDocument()
  })
  it('supports mixed evidence inventory requests without adding unrelated FAERS', () => {
    const panel = summary('What recalls and warnings are available?')!
    expect(within(panel).getByText(/D-TEST-2016/)).toBeInTheDocument()
    expect(within(panel).getByText('Drug-label evidence unavailable')).toBeInTheDocument()
    expect(within(panel).getByText(/does not mean that no warnings exist/)).toBeInTheDocument()
    expect(within(panel).queryByText(/stored ingredient-report/)).not.toBeInTheDocument()
  })
  it.each(['Is this medication safe for me?', 'What contraindications are for me?', 'What about this?', 'What recalls caused liver failure?',
    'What recalls and warnings apply during pregnancy?', 'What recalls are current?',
    'Compare recalls for Xanax and Ozempic', 'Are there no warnings?', 'What FAERS reactions prove causation?'])('abstains on ambiguous or clinical scope: %s', question => {
    expect(summary(question)).toBeNull()
  })
  it.each([null, undefined, ''])('requires a completed-briefing question: %s', question => {
    const value = briefing('recalls'); value.question = question
    render(<PartialEvidenceSummary briefing={value} />)
    expect(screen.queryByRole('region')).not.toBeInTheDocument()
  })
  it('rejects evidence bound to another confirmed product', () => {
    const value = briefing('What recalls and FAERS reports are available?')
    for (const section of value.sections) if (section.evidence) section.evidence.product_ref = 'foreign'
    render(<PartialEvidenceSummary briefing={value} />)
    expect(screen.queryByText(/D-TEST-2016/)).not.toBeInTheDocument()
    expect(screen.queryByText(/stored ingredient-report/)).not.toBeInTheDocument()
  })
  it('rejects inconsistent nested recall product identity', () => {
    const value = briefing('recalls')
    const evidence = value.sections[1].evidence
    if (evidence?.type !== 'historical_recall_evidence') throw Error('fixture')
    evidence.product.product_ref = 'foreign'
    render(<PartialEvidenceSummary briefing={value} />)
    expect(screen.queryByText(/D-TEST-2016/)).not.toBeInTheDocument()
  })
  it.each(['not-a-url', 'javascript:alert(1)', 'https://evil-api.fda.gov/',
    'https://api.fda.gov:8443/', 'https://user:pass@api.fda.gov/', 'https://api.fda.gov.evil.com/'])('does not link malformed or unapproved sources: %s', url => {
    const value = briefing('recalls and FAERS')
    const recalls = value.sections[1].evidence, faers = value.sections[2].evidence
    if (recalls?.type !== 'historical_recall_evidence' || faers?.type !== 'faers_reporting_evidence') throw Error('fixture')
    recalls.records[0].source_url = url; faers.records[0].source!.source_url = url
    render(<PartialEvidenceSummary briefing={value} />)
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
  it.each(['failed', 'unavailable', 'not_requested'] as const)('honors section status %s', status => {
    const value = briefing('recalls and FAERS')
    value.sections.forEach(item => { item.status = status })
    render(<PartialEvidenceSummary briefing={value} />)
    expect(screen.queryByText(/D-TEST-2016/)).not.toBeInTheDocument()
    expect(screen.queryByText(/stored ingredient-report/)).not.toBeInTheDocument()
  })
  it('honors submitted category selection even if leftover evidence is present', () => {
    const value = briefing('recalls and FAERS'); value.requested_categories = ['recalls']
    render(<PartialEvidenceSummary briefing={value} />)
    expect(screen.queryByText(/stored ingredient-report/)).not.toBeInTheDocument()
  })
  it('uses present recall records rather than an inflated returned count and keeps coverage limits', () => {
    const value = briefing('recalls'), evidence = value.sections[1].evidence
    if (evidence?.type !== 'historical_recall_evidence') throw Error('fixture')
    evidence.returned_count = 100; evidence.results_truncated = true
    evidence.coverage.state = 'PARTIAL'; evidence.coverage.bounded = true; evidence.coverage.truncated = true
    value.sections[1].status = 'incomplete'
    render(<PartialEvidenceSummary briefing={value} />)
    expect(screen.getByText(/1 historical recall record is/)).toBeInTheDocument()
    expect(screen.queryByText(/100 historical/)).not.toBeInTheDocument()
    expect(screen.getByText(/Coverage: PARTIAL/)).toHaveTextContent('Bounded evidence. Stored results are truncated.')
  })
  it.each(['analytics', 'source', 'identity', 'unit'] as const)('does not summarize FAERS with missing or unmatched %s', missing => {
    const value = briefing('FAERS'), evidence = value.sections[2].evidence
    if (evidence?.type !== 'faers_reporting_evidence') throw Error('fixture')
    const record = evidence.records[0]
    if (missing === 'analytics') record.analytics = null
    if (missing === 'source') record.source = null
    if (missing === 'identity') record.ingredient_name = 'foreign-ingredient'
    if (missing === 'unit') record.analytics!.count_unit = 'reaction counts' as never
    render(<PartialEvidenceSummary briefing={value} />)
    expect(screen.queryByText(/stored ingredient-report/)).not.toBeInTheDocument()
  })
  it('identifies available selected labels without inventing a warning summary', () => {
    const value = briefing('warnings'), evidence = value.sections[0].evidence
    if (evidence?.type !== 'drug_label_evidence') throw Error('fixture')
    value.sections[0].status = 'incomplete'
    evidence.records = [{ applicability_class: 'EXACT_PRODUCT', evidence_scope: 'PRODUCT',
      selection_status: 'SELECTED_STORED' } as never]
    render(<PartialEvidenceSummary briefing={value} />)
    expect(screen.getByText('Drug-label evidence available')).toBeInTheDocument()
    expect(screen.getByText(/availability does not establish an answer/)).toBeInTheDocument()
  })
  it('handles absent sections without inventing findings', () => {
    const value = briefing('recalls and warnings'); value.sections = []
    render(<PartialEvidenceSummary briefing={value} />)
    expect(screen.queryByRole('region')).not.toBeInTheDocument()
  })
  it('replaces evidence across sequential runs and ignores edits outside the briefing', () => {
    const first = briefing('recalls')
    const view = render(<><input aria-label="Live question" defaultValue="FAERS" /><PartialEvidenceSummary briefing={first} /></>)
    expect(screen.getByText(/D-TEST-2016/)).toBeInTheDocument()
    expect(screen.queryByText(/stored ingredient-report/)).not.toBeInTheDocument()
    view.rerender(<PartialEvidenceSummary briefing={briefing('FAERS')} />)
    expect(screen.queryByText(/D-TEST-2016/)).not.toBeInTheDocument()
    expect(screen.getByText(/stored ingredient-report/)).toBeInTheDocument()
  })
})
