import { expect, test } from '@playwright/test'
import evidence from '../src/test/evidence.json' with { type: 'json' }

for (const width of [1440, 390]) {
  test(`search, select and download an evidence report at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 })
    const personalRequests: string[] = []
    await page.route('http://127.0.0.1:18000/api/**', async route => {
      const request = route.request()
      if (request.url().includes('/search')) return route.fulfill({ json: { results: [evidence.drug], count: 1 } })
      if (request.url().endsWith('/evidence')) return route.fulfill({ json: evidence })
      if (request.url().endsWith('/pharmaceutical')) {
        expect(request.method()).toBe('POST')
        expect(request.postDataJSON()).toEqual({ product_id: evidence.drug.id, name: 'Browser Reader', age: 37 })
        personalRequests.push(request.url())
        return route.fulfill({ contentType: 'application/pdf', body: '%PDF-1.4\n%%EOF', headers: { 'Cache-Control': 'no-store' } })
      }
      return route.abort()
    })
    await page.goto('/')
    await page.getByLabel('Brand, generic name, active ingredient or NDC').fill('Ozempic')
    await page.getByRole('button', { name: 'Search drugs' }).click()
    await page.getByRole('button', { name: /OZEMPIC/i }).click()
    await expect(page.getByRole('heading', { name: 'Recall history', exact: true })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Reported adverse events', exact: true })).toBeVisible()
    const recall = await page.getByRole('region', { name: 'Recall history', exact: true }).boundingBox()
    const ae = await page.getByRole('region', { name: 'Reported adverse events', exact: true }).boundingBox()
    if (width > 760) expect(Math.abs(recall!.y - ae!.y)).toBeLessThan(2)
    else expect(ae!.y).toBeGreaterThan(recall!.y)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    await page.getByRole('button', { name: 'Generate PDF Report', exact: true }).click()
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    await expect(dialog.getByLabel('Name (required)')).toBeFocused()
    await dialog.getByLabel('Name (required)').fill('Browser Reader')
    await dialog.getByLabel('Age (optional)').fill('37')
    const download = page.waitForEvent('download')
    await dialog.getByRole('button', { name: 'Generate and download' }).click()
    expect((await download).suggestedFilename()).toBe('dav-ai-evidence-report.pdf')
    await expect(dialog.getByRole('status')).toHaveText('Your PDF download is ready.')
    expect(personalRequests).toHaveLength(1)
    expect(page.url()).not.toContain('Reader')
    await dialog.getByRole('button', { name: 'Close', exact: true }).click()
    await page.reload()
    await expect(page.getByRole('heading', { name: 'Recall history', exact: true })).toBeVisible()
    await page.screenshot({ path: `/tmp/davai-explorer-${width}.png`, fullPage: true })
  })
}

test('keyboard dialog cancellation clears report details and restores focus', async ({ page }) => {
  await page.route('http://127.0.0.1:18000/api/**', route => route.fulfill({ json: route.request().url().includes('/search') ? { results: [evidence.drug], count: 1 } : evidence }))
  await page.goto(`/?q=Ozempic&drug=${encodeURIComponent(evidence.drug.id)}`)
  const generate = page.getByRole('button', { name: 'Generate PDF Report', exact: true })
  await generate.click()
  await page.getByLabel('Name (required)').fill('Transient Reader')
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).not.toBeVisible()
  await expect(generate).toBeFocused()
  await generate.click()
  await expect(page.getByLabel('Name (required)')).toHaveValue('')
})
