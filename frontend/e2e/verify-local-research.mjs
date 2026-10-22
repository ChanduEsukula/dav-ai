// Invoked only by scripts/verify_ask_research.py against real local services.
import { chromium, expect } from '@playwright/test'
import { mkdir } from 'node:fs/promises'

const capability = process.env.ASK_DAV_PAIRING
if (!capability) throw new Error('Local verification pairing capability required')
const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } })
const evidence = []
await page.route('**/*', route => {
  const url = new URL(route.request().url())
  return url.hostname === '127.0.0.1' && ['15173', '8001'].includes(url.port)
    ? route.continue() : route.abort()
})
page.on('response', async response => {
  if (response.url().endsWith('/result') && response.ok()) {
    const result = await response.json()
    if (result.briefing) evidence.push(result.briefing)
  }
})
try {
  await page.goto('http://127.0.0.1:15173/ask')
  await mkdir('../docs/ai/screenshots', { recursive: true })
  await page.screenshot({ path: '../docs/ai/screenshots/ask-local-connect.png', fullPage: true })
  await page.getByLabel('Local pairing capability').fill(capability)
  await page.getByRole('button', { name: 'Create local session' }).click()
  await page.getByLabel('Brand, ingredient or NDC').fill('0009-0029')
  await page.getByRole('button', { name: 'Search', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Confirm selected product' })).toBeDisabled({ timeout: 25_000 })
  await page.getByRole('button', { name: /Xanax.*Product NDC/ }).click()
  await page.getByRole('button', { name: 'Confirm selected product' }).click()
  const options = await page.getByLabel('Execution mode').locator('option').evaluateAll(rows => rows.map(row => row.value))
  // Exercise actual model planning when an approved installed model is present.
  const model = options.includes('qwen3.5:4b-q4_K_M') ? 'qwen3.5:4b-q4_K_M' : options.find(Boolean)
  if (model) await page.getByLabel('Execution mode').selectOption(model)
  await page.getByRole('button', { name: 'Research selected evidence' }).click()
  await expect(page.getByRole('region', { name: 'Research briefing' })).toBeVisible({ timeout: 100_000 })
  await expect(page.getByText('No admitted exact-product label is available in this frozen evidence release.')).toBeVisible()
  await expect(page.getByRole('heading', { name: /D-0161-2016/ })).toBeVisible()
  await expect(page.getByText(/They do not establish causation, incidence/)).toBeVisible()
  await page.getByText('Research execution details').click()
  await page.screenshot({ path: '../docs/ai/screenshots/ask-local-results-desktop.png', fullPage: true })
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.screenshot({ path: '../docs/ai/screenshots/ask-local-results-mobile.png', fullPage: true })
  await expect.poll(() => evidence.length).toBeGreaterThan(0)
  const result = evidence[0]
  const faers = result.sections.find(row => row.category === 'faers').evidence
  expect(faers.records[0].analytics.report_count).toBe(18)
  expect(faers.summary.product_report_total).toBeNull()
  expect(result.sections.every(row => !row.evidence || row.evidence.release.publication_authorized === false)).toBe(true)
  console.log(JSON.stringify({ workflow: 'real-browser-to-Agent-v2-frozen-release', model: model ?? null,
    status: result.status, categories: result.requested_categories, routing: result.routing,
    source_states: result.sections.map(row => [row.category, row.status]),
    ingredient_associations: faers.records[0].analytics.report_count,
    capabilities_in_storage: await page.evaluate(() => localStorage.length + sessionStorage.length),
    screenshots: 3 }))
  await page.getByRole('button', { name: 'New research session' }).click()
  await expect(page.getByLabel('Local pairing capability')).toBeVisible()
} finally { await browser.close() }
