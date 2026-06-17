import { expect, test, type Locator } from '@playwright/test'

type ElementBox = NonNullable<Awaited<ReturnType<Locator['boundingBox']>>>

const demoPages = [
  {
    name: 'Home',
    url: '/',
    heading: /Public safety\s+data\.\s+Made clear\./i,
    nav: 'Home',
  },
  {
    name: 'Pharmacy Safety',
    url: '/?page=pharmacy-safety',
    heading: 'Search pharmacy safety records',
    nav: 'Pharmacy Safety',
  },
  {
    name: 'Food Safety',
    url: '/?page=food-safety',
    heading: 'Search food and supplement safety records',
    nav: 'Food Safety',
  },
  {
    name: 'Cosmetic Safety',
    url: '/?page=cosmetic-safety',
    heading: 'Search cosmetic-event reports',
    nav: 'Cosmetic Safety',
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
    name: 'Saved Monitors',
    url: '/?page=saved-monitors',
    heading: 'Saved Monitors',
    nav: 'Monitors',
  },
  {
    name: 'Help Docs Search',
    url: '/?page=help',
    heading: 'Find cited snippets from Dav AI docs.',
    nav: 'Help',
  },
]

function boxesOverlap(first: ElementBox, second: ElementBox) {
  return !(
    first.x + first.width <= second.x ||
    second.x + second.width <= first.x ||
    first.y + first.height <= second.y ||
    second.y + second.height <= first.y
  )
}

async function expectNoOverlap(floatingCta: Locator, target: Locator, label: string) {
  await expect(floatingCta).toBeVisible()
  await expect(target).toBeVisible()

  const [floatingBox, targetBox] = await Promise.all([
    floatingCta.boundingBox(),
    target.boundingBox(),
  ])

  expect(floatingBox, `${label}: floating CTA should have a bounding box`).not.toBeNull()
  expect(targetBox, `${label}: target should have a bounding box`).not.toBeNull()

  if (!floatingBox || !targetBox) {
    throw new Error(`${label}: missing bounding box`)
  }

  expect(boxesOverlap(floatingBox, targetBox), `${label} should not be covered`).toBe(false)
}

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

test('mobile floating report CTA stays clear of key homepage controls', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')

  const floatingReportCta = page.getByRole('button', {
    name: /open safety report intake/i,
  })
  await expect(floatingReportCta).toBeVisible()

  const productScanButton = page.getByRole('button', { name: /Open ProductScan/i })
  await productScanButton.scrollIntoViewIfNeeded()
  await expectNoOverlap(floatingReportCta, productScanButton, 'ProductScan CTA')

  const safetySearchInput = page.getByLabel(/Safety search/i)
  await safetySearchInput.scrollIntoViewIfNeeded()
  await expectNoOverlap(floatingReportCta, safetySearchInput, 'Universal search input')

  const analyzeButton = page.getByRole('button', { name: 'Analyze' })
  await analyzeButton.scrollIntoViewIfNeeded()
  await expectNoOverlap(floatingReportCta, analyzeButton, 'Universal search Analyze button')
})
