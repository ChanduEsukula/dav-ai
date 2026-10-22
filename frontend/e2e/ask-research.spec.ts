import { expect, test } from '@playwright/test'
import fixture from '../src/research/briefing.fixture.json' with { type: 'json' }

const product = { product_ref: 'p_mock', brand_names: ['Xanax'], generic_name: 'alprazolam', strength: '.25 mg/1', dosage_form: 'TABLET', routes: ['ORAL'], active_ingredients: ['alprazolam'], product_ndcs: ['0009-0029'], package_ndcs: ['0009-0029-01'] }
test('explicit product confirmation leads to scoped, transparent partial evidence', async ({ page }) => {
  let executions = 0
  await page.route('http://127.0.0.1:8001/api/local/research/**', async route => {
    const path = new URL(route.request().url()).pathname
    let body: object = { state: 'closed' }
    if (path.endsWith('/sessions')) body = { session_id: 'opaque', capability: 'synthetic', expires_in: 600, models: [], model_runtime: 'unavailable' }
    if (path.endsWith('/resolve')) body = { state: 'confirmation_required', candidates: [product], results_may_be_incomplete: false }
    if (path.endsWith('/confirm')) body = { state: 'confirmed', medication: product }
    if (path.endsWith('/research')) { executions++; body = { state: 'running', briefing: null, code: null } }
    if (path.endsWith('/result')) body = { state: 'partial', briefing: fixture, code: null }
    await route.fulfill({ json: body })
  })
  await page.goto('/ask')
  await expect(page.getByRole('heading', { name: 'Ask Dav AI', exact: true })).toBeVisible()
  await page.getByLabel('Local pairing capability').fill('synthetic-local-pairing')
  await page.getByRole('button', { name: 'Create local session' }).click()
  await page.getByLabel('Brand, ingredient or NDC').fill('0009-0029')
  await page.getByRole('button', { name: 'Search', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Confirm selected product' })).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Research selected evidence' })).toBeDisabled()
  await page.getByRole('button', { name: /Xanax.*Product NDC/ }).click()
  await page.getByRole('button', { name: 'Confirm selected product' }).click()
  await page.getByRole('button', { name: 'Research selected evidence' }).dblclick()
  await expect(page.getByRole('region', { name: 'Research briefing' })).toBeVisible()
  await expect(page.getByText('No admitted exact-product label is available in this frozen evidence release.')).toBeVisible()
  await expect(page.getByText(/They do not establish causation, incidence/)).toBeVisible()
  await page.getByText('Research execution details').click()
  await expect(page.getByText('Explicit deterministic execution · no model planning')).toBeVisible()
  expect(executions).toBe(1)
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
})
