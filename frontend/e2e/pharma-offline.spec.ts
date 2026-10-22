import { expect, test } from '@playwright/test'

test('real frozen release search-to-PDF works with outbound network disabled', async ({ page, request, baseURL }) => {
  expect(process.env.PHARMA_OFFLINE_SMOKE, 'Required release journey must be explicitly enabled; it cannot skip').toBe('1')
  const api = process.env.PHARMA_API_URL || 'http://127.0.0.1:18000'
  const origin = new URL(baseURL!).origin
  const cors = await request.get(`${api}/health`, { headers: { Origin: origin } })
  expect(cors.headers()['access-control-allow-origin'], 'Offline harness must admit the exact Playwright origin').toBe(origin)
  const untrusted = await request.get(`${api}/health`, { headers: { Origin: 'https://untrusted.example' } })
  expect(untrusted.headers()['access-control-allow-origin']).toBeUndefined()
  expect((await request.get(`${api}/ready`)).status(), 'Required artifact is unavailable or unauthorized; release journey is BLOCKED').toBe(200)
  const results = await request.get(`${api}/api/drugs/search?q=Xanax`)
  expect(results.ok()).toBe(true)
  const products = (await results.json()).results
  expect(products.length, 'The actual frozen catalog must contain Xanax').toBeGreaterThan(0)
  const selected = products[0]
  await page.goto('/?q=Xanax')
  await page.getByRole('button').filter({ hasText: selected.product_ndcs[0] }).first().click()
  await expect(page.getByRole('heading', { name: 'Recall history', exact: true })).toBeVisible()
  const sources = page.getByRole('region', { name: 'Sources and data freshness' })
  await expect(sources.getByText('openfda_ndc_directory', { exact: true })).toHaveCount(1)
  await sources.getByText('Stored provenance records (2)').click()
  await expect(sources.getByText('No URL stored for this provenance record.')).toBeVisible()
  await page.getByRole('button', { name: 'Generate PDF Report', exact: true }).click()
  await page.getByLabel('Name (required)').fill('Offline Regression Reader')
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Generate and download' }).click()
  const result = await download
  expect(await result.failure()).toBeNull()
  expect(result.suggestedFilename()).toBe('dav-ai-evidence-report.pdf')
  await expect(page.getByRole('status')).toHaveText('Your PDF download is ready.')
})
