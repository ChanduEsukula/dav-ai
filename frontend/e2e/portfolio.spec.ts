import { expect, test } from '@playwright/test'

for (const width of [1440, 768, 390]) {
  test(`restored pages, keyboard navigation and reduced motion at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 })
    await page.emulateMedia({ reducedMotion: 'reduce' })
    const errors: string[] = []
    page.on('pageerror', error => errors.push(error.message))
    for (const route of ['/home', '/overview', '/about', '/faq', '/', '/ask']) {
      await page.goto(route)
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
      await expect(page.getByRole('main')).toHaveAttribute('id', 'main-content')
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
      const motion = await page.getByRole('main').evaluate(element => [...element.querySelectorAll('*')].every(node => getComputedStyle(node).animationName === 'none'))
      expect(motion).toBe(true)
      await page.screenshot({ path: `/tmp/dav-ai-ui-audit/after/verified-${route.slice(1) || 'explorer'}-${width}.png`, fullPage: true })
    }
    await page.goto('/faq')
    const summary = page.locator('summary').filter({ hasText: 'Is Dav AI FDA approved?' })
    await summary.focus()
    await page.keyboard.press('Enter')
    await expect(page.getByText('No. Dav AI is an academic portfolio project', { exact: false })).toBeVisible()
    await page.keyboard.press('Space')
    await expect(summary.locator('..')).not.toHaveAttribute('open')
    if (width < 1050) {
      const menu = page.getByRole('button', { name: /Menu/ })
      await menu.click()
      await expect(menu).toHaveAttribute('aria-expanded', 'true')
      await page.getByRole('navigation', { name: 'Workspace navigation' }).getByRole('link', { name: 'Home', exact: true }).focus()
      await page.keyboard.press('Escape')
      await expect(menu).toBeFocused()
      await expect(menu).toHaveAttribute('aria-expanded', 'false')
      await menu.click()
    }
    await page.getByRole('navigation', { name: 'Workspace navigation' }).getByRole('link', { name: 'Home', exact: true }).click()
    await expect(page).toHaveURL(/\/home$/)
    await page.getByRole('link', { name: /Open Research Pro/ }).click()
    await expect(page.getByRole('heading', { name: 'Pharmaceutical Evidence Workspace' })).toBeVisible()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'research_pro')
    expect(errors).toEqual([])
  })
}

test('normal-motion landing settles, original graphics render and FAQ closes cleanly', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.emulateMedia({ reducedMotion: 'no-preference' })
  await page.goto('/home')
  await expect(page.locator('.hero-copy')).toHaveCSS('opacity', '1')
  await expect(page.locator('.hero-visual')).toHaveCSS('opacity', '1')
  expect(await page.locator('.hero-visual').evaluate(element => element.getAnimations({ subtree: true }).some(animation => animation.effect?.getTiming().iterations === Infinity))).toBe(false)
  await page.locator('.operational-flow').scrollIntoViewIfNeeded()
  await expect(page.locator('.operational-flow')).toHaveCSS('opacity', '1')
  await expect(page.locator('.operational-flow__icon svg')).toHaveCount(6)
  await page.goto('/faq')
  const disclosure = page.locator('details').first()
  await disclosure.locator('summary').click()
  await expect(disclosure).toHaveAttribute('open')
  await expect(disclosure.locator('p')).toBeVisible()
  await disclosure.locator('summary').click()
  await expect(disclosure).not.toHaveAttribute('open')
})
