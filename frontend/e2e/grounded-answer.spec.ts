import { expect, test } from '@playwright/test'
import fixture from '../src/research/briefing.fixture.json' with { type: 'json' }
import type { PublicBriefing } from '../src/research/contracts'

for (const status of ['generated', 'unavailable'] as const) {
  test(`optional grounded answer ${status}, citations and both experiences`, async ({ page }) => {
    const value = structuredClone(fixture) as PublicBriefing
    const product = value.medication
    const labels = value.sections.find(s => s.category === 'labels')!
    if (labels.evidence?.type !== 'drug_label_evidence') throw new Error('Missing label fixture')
    const text = 'Patients with a serious allergy must not use this product.'
    const record = { label_set_id: 'set-one', label_version: '3', effective_date: '2026-01-01',
      applicability_class: 'EXACT_PRODUCT' as const, evidence_scope: 'PRODUCT' as const,
      selection_status: 'SELECTED_STORED' as const, match_method: 'EXACT_NDC', matched_value: product.product_ndcs[0],
      boxed_warning: null, warnings_and_precautions: null, warnings: null, contraindications: text,
      adverse_reactions: null, drug_interactions: null, section_states: {}, source: 'openfda_drug_label',
      source_record_id: 'source-one', source_url: 'https://api.fda.gov/drug/label.json' }
    labels.status = 'incomplete'; labels.evidence.records = [record]
    value.answer = { status, product_ref: product.product_ref, reason: status === 'generated' ? 'validated_extractive_selection' : 'model_unavailable',
      text: status === 'generated' ? `The stored contraindications section states: “${text}” [E1]` : null,
      method: 'local_model_extractive', limitations: ['Citation resolution is not a human support judgment.'],
      citations: status === 'generated' ? [{ evidence_id: 'E1', category: 'labels', product_ref: product.product_ref,
        source_record_id: record.source_record_id, source_url: record.source_url, label_set_id: record.label_set_id,
        label_version: record.label_version, section: 'contraindications', start: 0, end: text.length,
        text_sha256: '0'.repeat(64), source_snapshot_date: '2026-09-25', release_id: 'synthetic-release' }] : [] }
    let enabled = false
    await page.route('**/api/local/research/**', async route => {
      const path = new URL(route.request().url()).pathname
      let body: object = { state: 'closed' }
      if (path.endsWith('/sessions')) body = { session_id: 'opaque-answer', capability: 'synthetic', expires_in: 600, models: [], model_runtime: 'unavailable' }
      if (path.endsWith('/resolve')) body = { state: 'confirmation_required', candidates: [product], results_may_be_incomplete: false }
      if (path.endsWith('/confirm')) body = { state: 'confirmed', medication: product }
      if (path.endsWith('/research')) { enabled = route.request().postDataJSON().synthesize; body = { state: 'running', briefing: null, code: null } }
      if (path.endsWith('/result')) body = { state: 'partial', briefing: value, code: null }
      await route.fulfill({ json: body })
    })
    await page.goto('/ask')
    await page.getByLabel('Local pairing capability').fill('synthetic')
    await page.getByRole('button', { name: 'Create local session' }).click()
    await page.getByLabel('Brand, ingredient or NDC').fill(product.product_ndcs[0])
    await page.getByRole('button', { name: 'Search', exact: true }).click()
    await page.getByRole('button', { name: /Xanax.*Product NDC/ }).click()
    await page.getByRole('button', { name: 'Confirm selected product' }).click()
    const option = page.getByRole('checkbox', { name: /Include a grounded AI answer/ })
    await expect(option).not.toBeChecked(); await option.check()
    await page.getByRole('button', { name: 'Research selected evidence' }).click()
    await expect(page.getByRole('region', { name: 'AI-generated answer' })).toBeVisible()
    expect(enabled).toBe(true)
    if (status === 'generated') {
      await page.getByRole('link', { name: '[E1] Open contraindications source' }).click()
      await expect(page.locator('.everyday-section-accordion[open]').filter({ hasText: text })).toBeVisible()
    } else await expect(page.getByText('AI synthesis is unavailable. The structured evidence remains available below.')).toBeVisible()
    await page.getByRole('button', { name: /research pro/i }).click()
    await page.getByRole('button', { name: /Deep Single-Product Research/ }).click()
    await expect(page.getByRole('region', { name: 'AI-generated answer' })).toBeVisible()
    if (status === 'generated') {
      await page.getByRole('link', { name: '[E1] Open contraindications source' }).click()
      await expect(page.locator('details[open] .label-text').filter({ hasText: text })).toBeVisible()
    }
  })
}
