import { expect, test } from '@playwright/test'

// Test-only software rendering; the application retains its performance-caveat fallback.
test.use({ launchOptions: { args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] } })

for (const width of [320, 390, 768, 1366, 1920]) {
  test(`shared navigation, themes and reduced motion at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 })
    await page.emulateMedia({ reducedMotion: 'reduce' })
    const errors: string[] = []
    const sceneRequests: string[] = []
    page.on('pageerror', error => errors.push(error.message))
    page.on('request', request => { if (request.url().includes('/OrbScene')) sceneRequests.push(request.url()) })
    let headerSize: { width: number; height: number } | null = null
    for (const route of ['/home', '/overview', '/about', '/faq', '/', '/ask']) {
      await page.goto(route)
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
      await expect(page.getByRole('main')).toHaveAttribute('id', 'main-content')
      await expect(page.getByRole('group', { name: 'Experience' })).toBeVisible()
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
      const header = await page.getByRole('banner').boundingBox()
      if (headerSize) { expect(header!.width).toBe(headerSize.width); expect(header!.height).toBe(headerSize.height) }
      else headerSize = header
      if (route === '/home') {
        await expect(page.locator('canvas')).toHaveCount(0)
        await expect(page.getByTestId('orb-static')).toBeVisible()
        await page.screenshot({ path: `/tmp/dav-ai-immersive/home-static-${width}.png`, fullPage: true })
      }
    }
    expect(sceneRequests).toEqual([])
    await page.goto('/faq')
    const summary = page.locator('summary').filter({ hasText: 'Is Dav AI FDA approved?' })
    await summary.focus()
    await page.keyboard.press('Enter')
    await expect(page.getByText('No. Dav AI uses stored public FDA/openFDA evidence.', { exact: false })).toBeVisible()
    await page.keyboard.press('Space')
    await expect(summary.locator('..')).not.toHaveAttribute('open')
    if (width <= 1260) {
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
    await page.getByRole('button', { name: 'Research Pro', exact: true }).click()
    await expect(page.getByRole('button', { name: 'Research Pro', exact: true })).toHaveAttribute('aria-pressed', 'true')
    await page.getByRole('link', { name: /Open Research Pro/ }).click()
    await expect(page.getByRole('heading', { name: 'Pharmaceutical Evidence Workspace' })).toBeVisible()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'research_pro')
    expect(errors).toEqual([])
  })
}

test('hero keyboard search reaches the existing Explorer without changing the query', async ({ page }) => {
  await page.route('http://127.0.0.1:18000/api/**', route => route.fulfill({ json: { results: [], count: 0 } }))
  await page.goto('/home')
  await page.getByRole('searchbox', { name: 'Medication name or NDC' }).fill('0009-0029')
  const request = page.waitForRequest(request => request.url().includes('/api/drugs/search'))
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/\?q=0009-0029$/)
  expect(new URL((await request).url()).searchParams.get('q')).toBe('0009-0029')
  await expect(page.getByLabel('Brand, generic name, active ingredient or NDC')).toHaveValue('0009-0029')
})

test('normal-motion orb renders, animates independently, and survives context loss', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.emulateMedia({ reducedMotion: 'no-preference' })
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await page.goto('/home')
  await expect(page.locator('.orb-render canvas')).toBeVisible({ timeout: 20000 })
  await expect(page.locator('.orb-render')).toHaveClass(/is-ready/, { timeout: 20000 })
  const before = await page.locator('.orb-symbol-labels').evaluate(node => getComputedStyle(node).transform)
  await expect.poll(() => page.locator('.orb-symbol-labels').evaluate(node => getComputedStyle(node).transform)).not.toBe(before)
  await page.getByRole('searchbox', { name: 'Medication name or NDC' }).fill('Xanax')
  await expect(page.getByRole('searchbox')).toHaveValue('Xanax')
  await page.screenshot({ path: '/tmp/dav-ai-immersive/home-live-desktop.png', fullPage: true })
  await page.locator('canvas').dispatchEvent('webglcontextlost')
  await expect(page.getByTestId('orb-static')).toBeVisible()
  await expect(page.locator('canvas')).toHaveCount(0)
  await expect(page.getByRole('searchbox')).toHaveValue('Xanax')
  expect(errors).toEqual([])
})

test('unavailable WebGL keeps a static illustration and working controls without loading Three.js', async ({ page }) => {
  await page.addInitScript(() => { Object.defineProperty(window, 'WebGL2RenderingContext', { value: undefined }) })
  await page.emulateMedia({ reducedMotion: 'no-preference' })
  const sceneRequests: string[] = []
  page.on('request', request => { if (request.url().includes('/OrbScene')) sceneRequests.push(request.url()) })
  await page.goto('/home')
  await expect(page.getByTestId('orb-static')).toBeVisible()
  await expect(page.locator('canvas')).toHaveCount(0)
  await page.getByRole('button', { name: 'Research Pro', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Research Pro', exact: true })).toHaveAttribute('aria-pressed', 'true')
  expect(sceneRequests).toEqual([])
})


test('changing reduced-motion preference switches a live scene to the static fallback', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'no-preference' })
  await page.goto('/home')
  await expect(page.locator('canvas')).toBeVisible({ timeout: 20000 })
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await expect(page.locator('canvas')).toHaveCount(0)
  await expect(page.getByTestId('orb-static')).toBeVisible()
  await expect(page.locator('.orb-symbol-labels')).toHaveCSS('transform', 'none')
})
