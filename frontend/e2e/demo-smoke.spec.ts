import { expect, test } from '@playwright/test'

test('demo navigation follows the canonical safety workspaces and evidence pages', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByText('Dav AI').first()).toBeVisible()

  const navItems = [
    'Pharmacy Safety',
    'Food Safety',
    'Cosmetic Safety',
    'Sources',
    'Audit',
    'System',
    'Monitors',
  ]

  for (const item of navItems) {
    await expect(page.getByRole('button', { name: item, exact: true })).toBeVisible()
  }

  await expect(page.getByRole('button', { name: 'Profile', exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Sign Up', exact: true })).toHaveCount(0)

  await expect(page.getByRole('button', { name: 'Ask DAV AI', exact: true })).toHaveCount(0)

  await page.getByRole('button', { name: 'Pharmacy Safety', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Search pharmacy safety records' }),
  ).toBeVisible()
  await expect(page.getByRole('button', { name: 'Pharmacy Safety', exact: true })).toHaveAttribute(
    'aria-current',
    'page',
  )

  await page.getByRole('button', { name: 'Food Safety', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Search food and supplement safety records' }),
  ).toBeVisible()

  await page.getByRole('button', { name: 'Cosmetic Safety', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Search cosmetic-event reports' }),
  ).toBeVisible()

  await page.getByRole('button', { name: 'Sources', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Registered public data sources.' }),
  ).toBeVisible()

  await page.getByRole('button', { name: 'Audit', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Audit History' })).toBeVisible()
})
