import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { PublicBriefing } from './contracts'
import fixture from './briefing.fixture.json'
import { Briefing } from './Evidence'
import { EverydayBriefing } from './EverydayEvidence'
import { labelAnchor } from './evidenceAnchors'
import { SynthesisOption } from './SynthesisOption'

function briefing(): PublicBriefing {
  const value = structuredClone(fixture) as PublicBriefing
  const section = value.sections.find(s => s.category === 'labels')!
  if (section.evidence?.type !== 'drug_label_evidence') throw new Error('Label fixture required')
  section.status = 'available'
  const text = 'Patients with a serious allergy must not use this product.'
  const record = { label_set_id: 'set:one', label_version: '3', effective_date: '2026-01-01',
    applicability_class: 'EXACT_PRODUCT' as const, evidence_scope: 'PRODUCT' as const,
    selection_status: 'SELECTED_STORED' as const, match_method: 'EXACT_NDC', matched_value: '0009-0029',
    boxed_warning: null, warnings_and_precautions: null, warnings: null, contraindications: text,
    adverse_reactions: null, drug_interactions: null, section_states: {}, source: 'openfda_drug_label',
    source_record_id: 'source:one', source_url: 'https://api.fda.gov/drug/label.json' }
  section.evidence.product_ref = value.medication.product_ref
  section.evidence.records = [record]
  value.answer = { status: 'generated', reason: 'validated_extractive_selection', product_ref: value.medication.product_ref,
    method: 'local_model_extractive', text: `The stored contraindications section states: “${text}” [E1]`,
    citations: [{ evidence_id: 'E1', category: 'labels', product_ref: value.medication.product_ref,
      source_record_id: record.source_record_id, source_url: record.source_url, label_set_id: record.label_set_id,
      label_version: record.label_version, section: 'contraindications', start: 0, end: text.length,
      text_sha256: '0'.repeat(64), source_snapshot_date: '2026-09-25', release_id: 'synthetic-release' }],
    limitations: ['Human claim-support review remains necessary.'] }
  return value
}

for (const mode of ['Everyday', 'Research Pro']) {
  describe(`${mode} grounded answer`, () => {
    const display = (value: PublicBriefing) => render(mode === 'Everyday'
      ? <EverydayBriefing briefing={value} /> : <Briefing value={value} />)
    it('shows answer before evidence and opens the precise cited source section', () => {
      const value = briefing()
      display(value)
      const answer = screen.getByRole('region', { name: 'AI-generated answer' })
      const link = screen.getByRole('link', { name: '[E1] Open contraindications source' })
      const cite = value.answer!.citations[0]
      const target = document.getElementById(labelAnchor(cite, cite.section))!
      expect(answer.compareDocumentPosition(target) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
      const details = target.closest('details')!
      expect(details.open).toBe(false)
      fireEvent.click(link)
      expect(link).toHaveAttribute('href', `#${target.id}`)
      expect(details.open).toBe(true)
      expect(target).toHaveFocus()
      expect(screen.getByText(/separate from the original FDA source cards/)).toBeInTheDocument()
    })
    for (const status of ['insufficient_evidence', 'unavailable', 'invalid_output'] as const) {
      it(`preserves source cards and explains ${status}`, () => {
        const value = briefing()
        value.answer = { ...value.answer!, status, text: null, citations: [] }
        display(value)
        expect(screen.getByRole('status')).toHaveTextContent(/structured evidence/i)
        expect(screen.queryByRole('link', { name: /Open contraindications source/ })).not.toBeInTheDocument()
        expect(screen.getByText('Patients with a serious allergy must not use this product.')).toBeInTheDocument()
      })
    }
    it('discards a stale product answer and unresolved citations', () => {
      const value = briefing()
      value.answer!.product_ref = 'different-confirmation'
      display(value)
      expect(screen.getByRole('status')).toHaveTextContent('failed validation')
      expect(screen.queryByText(/The stored contraindications section states/)).not.toBeInTheDocument()
    })
    it('supports older briefings without an answer field', () => {
      const value = briefing(); delete value.answer
      display(value)
      expect(screen.queryByRole('region', { name: 'AI-generated answer' })).not.toBeInTheDocument()
    })
  })
}

it('synthesis is an explicit opt-in and cannot change during execution', () => {
  const change = vi.fn()
  const view = render(<SynthesisOption onChange={change} disabled={false} />)
  const checkbox = screen.getByRole('checkbox', { name: /Include a grounded AI answer/ })
  expect(checkbox).not.toBeChecked()
  fireEvent.click(checkbox)
  expect(change).toHaveBeenCalledWith(true)
  view.rerender(<SynthesisOption enabled onChange={change} disabled />)
  expect(checkbox).toBeDisabled()
})
