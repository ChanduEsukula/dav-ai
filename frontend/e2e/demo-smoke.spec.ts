import { expect, test } from '@playwright/test'

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
