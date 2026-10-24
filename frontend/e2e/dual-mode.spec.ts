import { expect, test } from '@playwright/test'
import fixture from '../src/research/briefing.fixture.json' with { type: 'json' }

const productXanax = {
  product_ref: 'p_xanax',
  brand_names: ['Xanax'],
  generic_name: 'alprazolam',
  strength: '.25 mg/1',
  dosage_form: 'TABLET',
  routes: ['ORAL'],
  active_ingredients: ['alprazolam'],
  product_ndcs: ['0009-0029'],
  package_ndcs: ['0009-0029-01', '0009-0029-02'],
}

const productLipitor = {
  product_ref: 'p_lipitor',
  brand_names: ['Lipitor'],
  generic_name: 'atorvastatin calcium',
  strength: '20 mg/1',
  dosage_form: 'TABLET',
  routes: ['ORAL'],
  active_ingredients: ['atorvastatin calcium'],
  product_ndcs: ['0071-0156'],
  package_ndcs: ['0071-0156-23'],
}

test('dual-mode workflow: Everyday and Research Pro full journeys', async ({ page }, testInfo) => {
  let sessions = 0
  let confirmed: typeof productXanax | null = null
  let sessionProduct: typeof productXanax | null = null
  const executions: string[] = []
  // Mock local research API
  await page.route('http://127.0.0.1:8001/api/local/research/**', async (route) => {
    const path = new URL(route.request().url()).pathname
    if (!path.endsWith('/sessions')) {
      expect(path).toContain(`opaque_session_${sessions}`)
      expect(route.request().headers().authorization).toBe(`Bearer synthetic_cap_${sessions}`)
    }
    let body: object = { state: 'closed' }
    if (path.endsWith('/sessions')) {
      sessions++
      confirmed = null
      sessionProduct = null
      body = {
        session_id: `opaque_session_${sessions}`,
        capability: `synthetic_cap_${sessions}`,
        expires_in: 600,
        models: ['qwen3.5:4b-q4_K_M', 'llama3.2:3b'],
        model_runtime: 'available',
      }
    }
    if (path.endsWith('/resolve')) {
      const query = (route.request().postDataJSON()?.query || '').toLowerCase()
      const candidates = query.includes('lipitor') || query.includes('0071-0156')
        ? [{ ...productLipitor, product_ref: `p_lipitor_${sessions}` }]
        : [productXanax]
      sessionProduct = candidates[0]
      body = {
        state: 'confirmation_required',
        candidates,
        results_may_be_incomplete: false,
      }
    }
    if (path.endsWith('/confirm')) {
      expect(route.request().postDataJSON().product_ref).toBe(sessionProduct?.product_ref)
      confirmed = sessionProduct
      body = { state: 'confirmed', medication: confirmed }
    }
    if (path.endsWith('/research')) {
      expect(confirmed).not.toBeNull()
      executions.push(`${sessions}:${confirmed!.product_ndcs[0]}`)
      body = { state: 'running', briefing: null, code: null }
    }
    if (path.endsWith('/result')) {
      const briefing = { ...fixture, medication: { ...fixture.medication, ...confirmed } }
      if (sessions === 2) briefing.sections = fixture.sections.map(section => ({ ...section,
        status: section.category === 'labels' ? 'available' : section.category === 'recalls' ? 'incomplete' : 'unavailable',
        evidence: null,
      }))
      body = { state: 'partial', briefing, code: null }
    }
    if (path.endsWith('/close')) {
      expect(path).toContain('opaque_session_1')
      confirmed = null
    }
    await route.fulfill({ json: body })
  })

  // 1. Initial Load in Everyday Mode
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('/ask')

  // Check Everyday Headline
  await expect(
    page.getByRole('heading', { name: 'Understand your medication information' })
  ).toBeVisible()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'everyday')

  // Check Experience Selector
  const everydayBtn = page.getByRole('button', { name: /everyday/i })
  const researchProBtn = page.getByRole('button', { name: /research pro/i })
  await expect(everydayBtn).toHaveAttribute('aria-pressed', 'true')
  await expect(researchProBtn).toHaveAttribute('aria-pressed', 'false')

  // Pair Local Session
  await page.getByLabel('Local pairing capability').fill('synthetic-token-123')
  await page.getByRole('button', { name: 'Create local session' }).click()

  // Search & Confirm Product
  await page.getByLabel('Brand, ingredient or NDC').fill('0009-0029')
  await page.getByRole('button', { name: 'Search', exact: true }).click()
  await page.getByRole('button', { name: /Xanax.*Product NDC/ }).click()
  await page.getByRole('button', { name: 'Confirm selected product' }).click()

  // Run Research in Everyday Mode
  await page.getByRole('button', { name: 'Research selected evidence' }).click()
  await expect(page.getByRole('region', { name: 'Research briefing' })).toBeVisible()

  // Verify Consumer-Friendly Cards
  await expect(
    page.getByRole('heading', { name: 'Prescription & Package Insert Information' })
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Historical Recall Actions' })
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Reported Adverse Events (FAERS)' })
  ).toBeVisible()
  await expect(page.getByText('Official FDA Labeling')).toBeVisible()
  await expect(page.getByText('FDA Enforcement')).toBeVisible()
  await expect(page.getByText('Postmarket Signals')).toBeVisible()

  // Screenshot Everyday Desktop
  await page.screenshot({ path: testInfo.outputPath('everyday-desktop.png'), fullPage: true })

  // 2. Responsive Check for Everyday Mobile
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.screenshot({ path: testInfo.outputPath('everyday-mobile.png'), fullPage: true })

  // 3. Switch to Research Pro Experience
  await page.setViewportSize({ width: 1440, height: 900 })
  await researchProBtn.click()

  // Verify Research Pro theme & headline
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'research_pro')
  await expect(
    page.getByRole('heading', { name: 'Pharmaceutical Evidence Workspace' })
  ).toBeVisible()
  await expect(researchProBtn).toHaveAttribute('aria-pressed', 'true')
  await expect(everydayBtn).toHaveAttribute('aria-pressed', 'false')

  // Search in Cohort Builder & Add to Cohort
  await page.getByLabel('Search Product by Name, Ingredient or NDC').fill('Lipitor')
  await page.getByRole('button', { name: 'Search Directory' }).click()

  const addLipitorBtn = page.getByRole('button', { name: '+ Add to Cohort' })
  await expect(addLipitorBtn).toBeVisible()
  await addLipitorBtn.click()

  // Verify Cohort Tray counter & Batch Table
  await expect(page.getByText('1 / 50 selected')).toBeVisible()
  await expect(page.getByLabel('Selected Cohort Tray').getByText('Lipitor')).toBeVisible()
  await expect(page.getByLabel('Batch Evidence Overview').getByText('Lipitor')).toBeVisible()
  await expect(page.getByText('Batch Execution Boundary Notice:')).toBeVisible()
  await expect(page.locator('.badge-status-not-evaluated').first()).toBeVisible()

  // Screenshot Research Pro Desktop
  await page.screenshot({ path: testInfo.outputPath('research-pro-desktop.png'), fullPage: true })

  // 4. Responsive Check for Research Pro Mobile
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  await page.screenshot({ path: testInfo.outputPath('research-pro-mobile.png'), fullPage: true })

  // Switching the cohort product must invalidate A before B can be confirmed.
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.getByRole('button', { name: 'Deep Research →' }).click()
  await expect(page.getByLabel('Local pairing capability')).toBeVisible()
  await expect(page.getByRole('region', { name: 'Research briefing' })).toHaveCount(0)
  await expect(page.getByText('✓ Product Identity Locked')).toHaveCount(0)
  expect(executions).toEqual(['1:0009-0029'])
  await page.getByLabel('Local pairing capability').fill('synthetic-token-123')
  await page.getByRole('button', { name: 'Pair Local Session' }).click()
  await expect(page.getByLabel('Search Medication to Confirm:')).toHaveValue('0071-0156')
  await expect(page.getByRole('button', { name: 'Execute Deep Evidence Retrieval' })).toBeDisabled()
  await page.getByRole('button', { name: 'Find Candidate' }).click()
  await expect(page.getByRole('button', { name: 'Confirm Exact Product' })).toBeDisabled()
  await page.getByRole('button', { name: /Lipitor.*NDC:/ }).click()
  await page.getByRole('button', { name: 'Confirm Exact Product' }).click()
  await expect(page.getByRole('region', { name: 'Product Confirmation' }).getByRole('heading', { name: 'Lipitor' })).toBeVisible()
  await page.getByRole('button', { name: 'Execute Deep Evidence Retrieval' }).click()
  await expect(page.getByRole('region', { name: 'Research briefing' }).getByRole('heading', { name: 'Lipitor' })).toBeVisible()
  expect(executions).toEqual(['1:0009-0029', '2:0071-0156'])
  await page.getByRole('button', { name: /Cohort Investigation & Overview/ }).click()
  const row = page.getByRole('region', { name: 'Batch Evidence Overview' }).getByRole('row', { name: /Lipitor/ })
  await expect(row.getByText('Available', { exact: true })).toBeVisible()
  await expect(row.getByText('Incomplete', { exact: true })).toBeVisible()
  await expect(row.getByText('Unavailable', { exact: true })).toBeVisible()
  await expect(row.getByText('Not evaluated', { exact: true })).toHaveCount(0)
})
