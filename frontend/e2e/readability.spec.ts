import { expect, test } from '@playwright/test'
import inventory from '../src/test/data-inventory.fixture.json' with { type: 'json' }
import overview from '../src/test/medication-overview.fixture.json' with { type: 'json' }

for (const width of [390, 1440]) {
  test(`readable typography, halo brand and safe anchor offsets at ${width}`, async ({ page }) => {
    await page.setViewportSize({width,height:1000})
    await page.emulateMedia({reducedMotion:'reduce'})
    await page.route('**/api/coverage/inventory', route => route.fulfill({json:inventory}))
    await page.route('**/api/medications/overview?*', route => route.fulfill({json:overview}))
    await page.route('**/api/drugs/search?*', route => route.fulfill({json:{results:overview.products,count:9}}))
    for (const mode of ['Everyday','Research Pro']) {
      await page.goto('/home')
      await page.getByRole('button',{name:mode,exact:true}).click()
      await expect(page.locator('.immersive-intro')).toHaveCSS('font-size', mode === 'Everyday' ? '16px' : '15px')
      await expect(page.locator('.immersive-trust')).toHaveCSS('font-size', '13px')
      await expect(page.getByRole('button', {name:mode,exact:true})).toHaveCSS('font-size', '14px')
      const emblem=page.locator('.brand-emblem')
      expect(await emblem.evaluate(node=>getComputedStyle(node).color)).toBe(mode==='Everyday'?'rgb(167, 247, 243)':'rgb(201, 185, 255)')
      expect(await emblem.evaluate(node=>getComputedStyle(node,'::after').animationName)).toBe('none')
      await page.getByRole('link',{name:'Dav AI home'}).focus()
      await page.keyboard.press('Tab')
      await page.keyboard.press('Shift+Tab')
      expect(await page.getByRole('link',{name:'Dav AI home'}).evaluate(node=>getComputedStyle(node).outlineStyle)).toBe('solid')
      let height=0
      for(const path of ['/home','/?q=Xanax','/ask','/overview','/faq','/about']) {
        await page.goto(path)
        await expect(page.getByRole('heading',{level:1})).toBeVisible()
        const box=await page.getByRole('banner').boundingBox()
        if(height) expect(box!.height).toBe(height)
        height=box!.height
        expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
        if(path.includes('Xanax')) {
          const rows=page.locator(mode==='Everyday'?'.compact-product-row':'.technical-products-table tbody tr:not(.product-provenance-row)')
          await expect(rows).toHaveCount(9)
          const cell=page.locator(mode==='Everyday'?'.compact-product-row strong':'.technical-products-table tbody th').first()
          expect(await cell.evaluate(node=>getComputedStyle(node).fontSize)).toBe('15px')
          for(const select of await page.locator('.product-filters select').all()) expect((await select.boundingBox())!.width).toBeGreaterThan(100)
        }
      }
      await page.goto('/home#explore-data')
      await expect(page.locator('.inventory-value')).toHaveCount(3)
      await page.locator('#explore-data').evaluate(node=>node.scrollIntoView({block:'start'}))
      const header=await page.getByRole('banner').boundingBox(), section=await page.locator('#explore-data').boundingBox()
      expect(section!.y).toBeGreaterThanOrEqual(header!.y+header!.height+12)
      await page.goto('/about#contact-creator')
      const contact=await page.locator('#contact-creator').boundingBox(), nav=await page.getByRole('banner').boundingBox()
      expect(contact!.y).toBeGreaterThanOrEqual(nav!.y+nav!.height+12)
    }
  })
}

test('brand sweep is finite and disabled when motion is reduced',async({page})=>{
  await page.goto('/faq')
  const timing=await page.locator('.brand-emblem').evaluate(node=>({name:getComputedStyle(node,'::after').animationName,iterations:getComputedStyle(node,'::after').animationIterationCount}))
  expect(timing).toEqual({name:'brand-light-sweep',iterations:'1'})
  await page.emulateMedia({reducedMotion:'reduce'})
  expect(await page.locator('.brand-emblem').evaluate(node=>getComputedStyle(node,'::after').animationName)).toBe('none')
})

test('old local API uses verified metadata; integrity failures and malformed values never fall back',async({page})=>{
  await page.route('**/api/coverage/inventory',route=>route.fulfill({status:404,json:{detail:'Not Found'}}))
  await page.goto('/home')
  await expect(page.locator('.inventory-value')).toHaveCount(3)
  await expect(page.getByText(/Verified development snapshot metadata/)).toBeVisible()
  await page.unroute('**/api/coverage/inventory')
  await page.route('**/api/coverage/inventory',route=>route.fulfill({status:503,json:{detail:'Unavailable'}}))
  await page.reload()
  await expect(page.getByRole('button',{name:'Retry dataset metrics'})).toBeVisible()
  await expect(page.locator('.inventory-value')).toHaveCount(0)
  await page.unroute('**/api/coverage/inventory')
  await page.route('**/api/coverage/inventory',route=>route.fulfill({json:{...inventory,metrics:[]}}))
  await page.getByRole('button',{name:'Retry dataset metrics'}).click()
  await expect(page.getByRole('alert')).toContainText('Dataset metrics could not be loaded')
  await expect(page.locator('.inventory-value')).toHaveCount(0)
})
