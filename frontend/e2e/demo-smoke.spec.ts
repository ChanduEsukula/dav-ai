import { expect, test } from '@playwright/test'

test('demo navigation exposes implemented modules without account placeholders', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByText('MedTrek AI').first()).toBeVisible()

  const navItems = ['RecallRadar', 'DrugSignal', 'Sources', 'Audit', 'System', 'Monitors']

  for (const item of navItems) {
    await expect(page.getByRole('button', { name: item, exact: true })).toBeVisible()
  }

  await expect(page.getByRole('button', { name: 'Profile', exact: true })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Sign Up', exact: true })).toHaveCount(0)

  await page.getByRole('button', { name: 'RecallRadar', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Search public FDA recall signals.' }),
  ).toBeVisible()

  await page.getByRole('button', { name: 'DrugSignal', exact: true }).click()
  await expect(
    page.getByRole('heading', {
      name: 'Explore public FAERS adverse-event reporting patterns.',
    }),
  ).toBeVisible()

  await page.getByRole('button', { name: 'Sources', exact: true }).click()
  await expect(
    page.getByRole('heading', { name: 'Registered public data sources.' }),
  ).toBeVisible()

  await page.getByRole('button', { name: 'Audit', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Audit History' })).toBeVisible()

  await page.getByRole('button', { name: 'System', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'System Status' })).toBeVisible()

  await page.getByRole('button', { name: 'Monitors', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Saved Monitors' })).toBeVisible()
})