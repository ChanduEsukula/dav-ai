import { expect, test } from '@playwright/test'

const demoPages = [
  {
    name: 'Home',
    url: '/',
    heading: /Public safety\s+data\.\s+Made clear\./i,
    nav: 'Home',
  },
  {
    name: 'DrugSignal',
    url: '/?page=pharmacy-safety',
    heading: 'Search pharmacy safety records',
    nav: 'DrugSignal',
  },
  {
    name: 'FoodSignal',
    url: '/?page=food-safety',
    heading: 'Search food and supplement safety records',
    nav: 'FoodSignal',
  },
  {
    name: 'Personal Care Signals',
    url: '/?page=cosmetic-safety',
    heading: 'Search cosmetic safety records',
    nav: 'Personal Care Signals',
  },
  {
    name: 'ProductScan',
    url: '/?page=productscan',
    heading: 'Review label text before searching public records.',
  },
  {
    name: 'Sources',
    url: '/?page=sources',
    heading: 'Registered public data sources.',
    nav: 'Sources',
  },
  {
    name: 'System Status',
    url: '/?page=system',
    heading: 'System Status',
    nav: 'System',
  },
  {
    name: 'Monitors',
    url: '/?page=saved-monitors',
    heading: 'Saved Searches',
    nav: 'Monitors',
  },
  {
    name: 'Help Docs Search',
    url: '/?page=help',
    heading: 'Find cited snippets from Dav AI docs.',
    nav: 'Help',
  },
]

test('demo-critical pages render without crashing', async ({ page }) => {
  for (const demoPage of demoPages) {
    await test.step(demoPage.name, async () => {
      await page.goto(demoPage.url)

      await expect(page.getByRole('heading', { name: demoPage.heading })).toBeVisible()

      if (demoPage.nav) {
        await expect(
          page.getByRole('button', { name: demoPage.nav, exact: true }),
        ).toHaveAttribute('aria-current', 'page')
      }
    })
  }
})

test('pwa installability metadata is served', async ({ page, request }) => {
  await page.goto('/')

  await expect(page.locator('link[rel="manifest"]')).toHaveAttribute(
    'href',
    '/manifest.webmanifest',
  )
  await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute(
    'content',
    '#0b4f71',
  )

  const manifestResponse = await request.get('/manifest.webmanifest')
  expect(manifestResponse.ok()).toBeTruthy()

  const manifest = await manifestResponse.json()
  expect(manifest).toMatchObject({
    name: 'Dav AI',
    short_name: 'Dav AI',
    start_url: '/',
    display: 'standalone',
  })

  const serviceWorkerResponse = await request.get('/sw.js')
  expect(serviceWorkerResponse.ok()).toBeTruthy()
  expect(await serviceWorkerResponse.text()).toContain("url.pathname.startsWith('/api/')")
})

test('mobile homepage controls remain reachable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')

  const productScanButton = page.getByRole('button', { name: /Open Scan beta/i })
  await productScanButton.scrollIntoViewIfNeeded()
  await expect(productScanButton).toBeVisible()

  const safetySearchInput = page.getByLabel(/Safety search/i)
  await safetySearchInput.scrollIntoViewIfNeeded()
  await expect(safetySearchInput).toBeVisible()

  const searchButton = page.getByRole('button', { name: 'Search records' })
  await searchButton.scrollIntoViewIfNeeded()
  await expect(searchButton).toBeVisible()
})
