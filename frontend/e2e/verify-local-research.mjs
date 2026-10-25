// Real services only. Parent harness supplies credentials in process memory.
import { chromium, expect } from '@playwright/test'
import { writeFile } from 'node:fs/promises'
import { createHash } from 'node:crypto'
import { join } from 'node:path'

const capability = process.env.ASK_DAV_PAIRING
const output = process.env.ASK_DAV_OUTPUT
const model = process.env.ASK_DAV_MODEL || 'llama3.2:3b'
if (!capability || !output) throw new Error('Use scripts/verify_ask_research.py with a new --output directory')
const base = 'http://127.0.0.1:15173'
const root = 'http://127.0.0.1:8001/api/local/research/sessions'
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' })
const sessions = []
const results = []
const pageErrors = []
page.on('pageerror', error => pageErrors.push(error.message))
// Only blocks external navigation; every admitted request reaches the real API.
await page.route('**/*', route => {
  const url = new URL(route.request().url())
  return url.hostname === '127.0.0.1' && ['15173', '8001'].includes(url.port)
    ? route.continue() : route.abort()
})
page.on('response', async response => {
  if (!response.ok() || !response.url().startsWith(root)) return
  const body = await response.json()
  if (response.url() === root) sessions.push(body) // Never serialized or printed.
  if (response.url().endsWith('/result') && body.briefing) results.push(body.briefing)
})
async function screenshot(name) {
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.screenshot({ path: join(output, name + '.png'), fullPage: true, animations: 'disabled' })
}
async function citationCheck(briefing) {
  expect(briefing.answer.status).toBe('generated')
  expect(briefing.answer.product_ref).toBe(briefing.medication.product_ref)
  for (const cite of briefing.answer.citations) {
    const label = briefing.sections.find(section => section.category === 'labels').evidence
    const record = label.records.find(row => row.source_record_id === cite.source_record_id && row.label_set_id === cite.label_set_id && row.label_version === cite.label_version)
    expect(record).toBeTruthy()
    const quote = record[cite.section].slice(cite.start, cite.end)
    expect(createHash('sha256').update(quote).digest('hex')).toBe(cite.text_sha256)
    expect(briefing.answer.text).toContain(quote)
    expect(cite.product_ref).toBe(briefing.medication.product_ref)
  }
  const cite = briefing.answer.citations[0]
  await page.getByRole('link', { name: `[${cite.evidence_id}] Open ${cite.section.replaceAll('_', ' ')} source` }).click()
  const target = page.locator('[id^="label-"]:focus')
  await expect(target).toBeVisible()
  const targetBox = await target.boundingBox()
  const navigation = await page.locator('.workspace-nav').boundingBox()
  expect(targetBox.y).toBeGreaterThanOrEqual(navigation.y + navigation.height)
}
async function latestResult(count) {
  await expect.poll(() => results.length, { timeout: 100_000 }).toBeGreaterThanOrEqual(count)
  return results.at(-1)
}
try {
  await page.goto(base + '/ask')
  await screenshot('connection')
  await page.getByLabel('Local pairing capability').fill(capability)
  await page.getByRole('button', { name: 'Create local session' }).click()
  await page.getByLabel('Brand, ingredient or NDC').fill('0002-0152')
  await page.getByRole('button', { name: 'Search', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Confirm selected product' })).toBeDisabled({ timeout: 25_000 })
  await page.getByRole('button', { name: /Zepbound.*Product NDC/i }).click()
  await page.getByRole('button', { name: 'Confirm selected product' }).click()
  await page.getByLabel('Research question').fill('What serious allergy appears in the Zepbound contraindications?')
  await page.getByRole('checkbox', { name: 'Historical recalls', exact: true }).uncheck()
  await page.getByRole('checkbox', { name: 'FAERS reporting evidence', exact: true }).uncheck()
  await page.getByRole('checkbox', { name: /Include a grounded AI answer/ }).check()
  expect(sessions[0].models, 'Everyday generation uses the installed default local model').toContain('llama3.2:3b')
  await page.getByRole('button', { name: 'Research selected evidence' }).click()
  await expect(page.getByRole('region', { name: 'AI-generated answer' })).toBeVisible({ timeout: 100_000 })
  const first = await latestResult(1)
  expect(first.medication.product_ndcs).toContain('0002-0152')
  await citationCheck(first)
  await screenshot('everyday-generated-desktop')
  await page.setViewportSize({ width: 390, height: 900 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await citationCheck(first)
  await screenshot('everyday-generated-mobile')

  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.getByRole('button', { name: /Research Pro/ }).click()
  await page.getByLabel('Search Product by Name, Ingredient or NDC').fill('58151-155')
  await page.getByRole('button', { name: 'Search Directory' }).click()
  await expect(page.getByLabel('Local pairing capability')).toBeVisible()
  await expect(page.getByRole('region', { name: 'Research briefing' })).toHaveCount(0)
  const old = sessions[0]
  expect((await page.request.get(`${root}/${old.session_id}/result`, { headers: {
    Authorization: `Bearer ${old.capability}`, Origin: base,
  } })).status()).toBe(410)
  await page.getByLabel('Local pairing capability').fill(capability)
  await page.getByRole('button', { name: 'Pair Local Session' }).click()
  await page.getByRole('button', { name: 'Search Directory' }).click()
  await page.getByRole('button', { name: '+ Add to Cohort' }).click()
  await page.getByRole('button', { name: 'Deep Research →' }).click()
  await expect(page.getByRole('region', { name: 'Research briefing' })).toHaveCount(0)
  await expect(page.getByLabel('Search Medication to Confirm:')).toHaveValue('58151-155')
  await expect(page.getByRole('button', { name: 'Execute Deep Evidence Retrieval' })).toBeDisabled()
  await page.getByRole('button', { name: 'Find Candidate' }).click()
  await expect(page.getByRole('button', { name: 'Confirm Exact Product' })).toBeDisabled({ timeout: 25_000 })
  await page.getByRole('button', { name: /Lipitor.*NDC:/i }).click()
  await page.getByRole('button', { name: 'Confirm Exact Product' }).click()
  await page.getByLabel('Research Question / Query Intent:').fill('What do Lipitor drug interactions say about digoxin plasma concentrations?')
  // Research Pro also exposes optional model tool planning.
  await page.getByLabel('Execution Inference Engine:').selectOption(model)
  await page.getByRole('button', { name: 'Execute Deep Evidence Retrieval' }).click()
  await expect(page.getByRole('region', { name: 'AI-generated answer' })).toBeVisible({ timeout: 100_000 })
  const second = await latestResult(2)
  expect(second.medication.product_ndcs).toContain('58151-155')
  expect(second.medication.product_ref).not.toBe(first.medication.product_ref)
  expect(['model', 'deterministic_completion']).toContain(second.routing.mode)
  await citationCheck(second)
  await screenshot('research-pro-generated-desktop')
  await page.setViewportSize({ width: 390, height: 900 })
  await citationCheck(second)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await screenshot('research-pro-generated-mobile')

  // A third real run verifies deterministic evidence survives insufficient scope.
  await page.getByRole('button', { name: 'Reset Session' }).click()
  await page.getByLabel('Local pairing capability').fill(capability)
  await page.getByRole('button', { name: 'Pair Local Session' }).click()
  await page.getByLabel('Search Medication to Confirm:').fill('0009-0029')
  await page.getByRole('button', { name: 'Find Candidate' }).click()
  await page.getByRole('button', { name: /Xanax.*NDC:/i }).click()
  await page.getByRole('button', { name: 'Confirm Exact Product' }).click()
  await page.getByLabel('Research Question / Query Intent:').fill('What are the Xanax contraindications?')
  await page.getByRole('checkbox', { name: 'Historical Enforcement Recalls' }).check()
  await page.getByRole('checkbox', { name: 'FAERS Adverse Event Signals' }).check()
  await page.getByRole('button', { name: 'Execute Deep Evidence Retrieval' }).click()
  await expect(page.getByText('Evidence is insufficient for a grounded answer to this question.', { exact: false })).toBeVisible({ timeout: 100_000 })
  const third = await latestResult(3)
  expect(third.answer.status).toBe('insufficient_evidence')
  expect(third.answer.text).toBeNull()
  expect(third.sections.find(section => section.category === 'recalls').evidence.records.length).toBeGreaterThan(0)
  expect(third.sections.find(section => section.category === 'faers').evidence.records[0].analytics.report_count).toBe(18)
  await screenshot('research-pro-deterministic-fallback')
  await page.getByRole('button', { name: 'Reset Session' }).click()
  await expect(page.getByLabel('Local pairing capability')).toBeVisible()
  expect(pageErrors).toEqual([])
  expect(await page.evaluate(() => sessionStorage.length)).toBe(0)
  const storedKeys = await page.evaluate(() => Object.keys(localStorage))
  expect(storedKeys.every(key => key === 'dav_ai_experience_mode')).toBe(true)
  const summary = { type: 'real-browser-api-frozen-release-ollama', everyday_generation_model: 'llama3.2:3b', research_pro_model: model,
    generated: results.slice(0, 2).map(value => ({ ndcs: value.medication.product_ndcs, status: value.answer.status,
      citations: value.answer.citations.length, routing: value.routing, rag: value.rag?.status,
      rag_reason: value.rag?.reason })),
    fallback: { ndcs: third.medication.product_ndcs, answer: third.answer.status, reason: third.answer.reason,
      source_states: third.sections.map(section => [section.category, section.status]) },
    old_session_after_switch: 410, credentials_in_browser_storage: false, page_errors: pageErrors,
    human_review: 'PENDING; this harness checks source reconstruction, not clinical support' }
  await writeFile(join(output, 'summary.json'), JSON.stringify(summary, null, 2) + '\n', { flag: 'wx' })
  await writeFile(join(output, 'briefings.json'), JSON.stringify(results, null, 2) + '\n', { flag: 'wx' })
  console.log(JSON.stringify(summary))
} finally {
  for (const session of sessions) await page.request.post(`${root}/${session.session_id}/close`, {
    headers: { Authorization: `Bearer ${session.capability}`, Origin: base }, data: {},
  }).catch(() => {})
  await browser.close()
}
