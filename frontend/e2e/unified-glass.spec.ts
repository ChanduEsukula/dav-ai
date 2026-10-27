import { expect, test } from '@playwright/test'
import evidence from '../src/test/evidence.json' with { type: 'json' }

for (const width of [390, 768, 1440]) {
  test(`symmetric evidence, exact chart units and expandable originals at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 })
    await page.route('http://127.0.0.1:18000/api/**', route => {
      const path = new URL(route.request().url()).pathname
      if (path.endsWith('/safety/labels')) return route.fulfill({ json: { drug_id: evidence.drug.id, records: [], latest_records: [], coverage: evidence.recalls.coverage } })
      return route.fulfill({ json: path.includes('/search') ? { results: [evidence.drug], count: 1 } : evidence })
    })
    await page.goto(`/?q=Ozempic&drug=${encodeURIComponent(evidence.drug.id)}`)
    const panels = page.locator('.evidence-glass-panel')
    await expect(panels).toHaveCount(3)
    await expect(page.getByRole('button', { name: 'Expand Drug labeling' })).toHaveAttribute('aria-expanded', 'false')
    const boxes = await panels.evaluateAll(nodes => nodes.map(node => ({ x: node.getBoundingClientRect().x, y: node.getBoundingClientRect().y, width: node.getBoundingClientRect().width, height: node.getBoundingClientRect().height })))
    expect(Math.max(...boxes.map(box => box.width)) - Math.min(...boxes.map(box => box.width))).toBeLessThan(2)
    if (width > 900) {
      expect(Math.max(...boxes.map(box => box.y)) - Math.min(...boxes.map(box => box.y))).toBeLessThan(2)
      expect(Math.max(...boxes.map(box => box.height)) - Math.min(...boxes.map(box => box.height))).toBeLessThan(2)
    } else expect(boxes[2].y).toBeGreaterThan(boxes[1].y)
    await expect(page.getByRole('group', { name: 'nausea: 3,640 reaction co-report activity' })).toBeVisible()
    await expect(page.getByText(/Not causation, incidence, patient counts or individual risk/)).toBeVisible()
    const expand = page.getByRole('button', { name: 'Expand Reported adverse events' })
    await expand.focus(); await page.keyboard.press('Enter')
    await expect(page.getByRole('button', { name: 'Collapse Reported adverse events' })).toHaveAttribute('aria-expanded', 'true')
    await expect(page.getByText('Monthly reporting trends')).toBeVisible()
    await page.getByRole('button', { name: 'Collapse Reported adverse events' }).click()
    await expect(page.getByText('Monthly reporting trends')).not.toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  })
}

test('Home feedback preserves the current page and search input', async ({ page }) => {
  await page.goto('/home')
  await page.getByRole('searchbox').fill('Xanax')
  await page.getByRole('navigation', { name: 'Workspace navigation' }).getByRole('link', { name: 'Home', exact: true }).click()
  await expect(page.getByRole('status')).toHaveText('You’re on Home')
  await expect(page.getByRole('searchbox')).toHaveValue('Xanax')
})

test('overview nodes animate and disclose safeguards using the keyboard', async ({ page }) => {
  await page.goto('/overview')
  await expect(page.locator('.flow-stage')).toHaveCount(4)
  await page.locator('.flow-nodes').scrollIntoViewIfNeeded()
  await expect(page.locator('.flow-stage.is-active')).toHaveCount(4)
  const summary = page.locator('.flow-stage summary').nth(2)
  await summary.focus(); await page.keyboard.press('Enter')
  await expect(page.getByText(/The sealed SQLite release stores products/)).toBeVisible()
  const moving = await page.locator('.flow-stage').first().evaluate(node => getComputedStyle(node, '::after').animationName)
  expect(moving).toBe('evidence-current')
  await page.emulateMedia({ reducedMotion: 'reduce' })
  expect(await page.locator('.flow-stage').first().evaluate(node => getComputedStyle(node, '::after').animationName)).toBe('none')
})

test('creator action exposes only the supplied email and LinkedIn', async ({ page }) => {
  await page.goto('/home')
  await page.getByRole('link', { name: 'Contact the Creator', exact: true }).click()
  await expect(page).toHaveURL(/\/about#contact-creator$/)
  await expect(page.getByRole('link', { name: /Email Chandu/ })).toHaveAttribute('href', 'mailto:esukulachandu@gmail.com')
  await expect(page.getByRole('link', { name: 'LinkedIn Chandu Esukula' })).toHaveAttribute('href', 'https://www.linkedin.com/in/chandu-esukula-a15454266')
})


test('light homepage controls retain ink contrast within the dark shared theme', async ({ page }) => {
  await page.goto('/home')
  await expect(page.getByRole('link', { name: 'Explore medications', exact: true })).toHaveCSS('color', 'rgb(6, 51, 66)')
  await expect(page.getByRole('searchbox')).toHaveCSS('background-color', 'rgba(0, 0, 0, 0)')
})

for (const width of [390, 1440]) {
  test(`Research Pro palette persists across routes with consistent navigation at ${width}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 })
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('/home')
    const before = await page.locator('.glass-site').evaluate(node => getComputedStyle(node).getPropertyValue('--mode-accent'))
    await page.getByRole('button', { name: 'Research Pro', exact: true }).click()
    const after = await page.locator('.glass-site').evaluate(node => getComputedStyle(node).getPropertyValue('--mode-accent'))
    expect(after).not.toBe(before)
    let geometry: { width: number; height: number } | null = null
    for (const route of ['/home', '/', '/ask', '/overview', '/faq', '/about']) {
      await page.goto(route)
      await expect(page.locator('.glass-site')).toHaveAttribute('data-theme', 'research_pro')
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
      const header = await page.getByRole('banner').boundingBox()
      if (geometry) {
        expect(header!.width).toBe(geometry.width)
        expect(header!.height).toBe(geometry.height)
      } else geometry = header
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    }
  })
}
