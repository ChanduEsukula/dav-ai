import { extractProductScanCandidates } from './productScanExtraction'

test('extracts product, brand, NDC, UPC, and lot/date candidates from label text', () => {
  const candidates = extractProductScanCandidates(`
    Product Name: CalmRelief Tablets
    Manufactured by Example Labs
    NDC 12345-678-90
    UPC: 012345678905
    Lot A1B2C3
    EXP 05/2026
  `)

  expect(candidates).toEqual(
    expect.arrayContaining([
      expect.objectContaining({ type: 'product', value: 'CalmRelief Tablets' }),
      expect.objectContaining({ type: 'brand', value: 'Example Labs' }),
      expect.objectContaining({ type: 'ndc', value: '12345-678-90' }),
      expect.objectContaining({ type: 'upc', value: '012345678905' }),
      expect.objectContaining({ type: 'lot', value: 'A1B2C3' }),
      expect.objectContaining({ type: 'lot', value: '05/2026' }),
    ]),
  )
})

test('uses prominent label lines as possible product names and skips noisy lines', () => {
  const candidates = extractProductScanCandidates(`
    Mango Coconut Water
    Nutrition Facts
    Ingredients: coconut water, mango puree
    Best by 2027-04-12
  `)

  expect(candidates[0]).toMatchObject({
    type: 'product',
    value: 'Mango Coconut Water',
  })
  expect(candidates).not.toEqual(
    expect.arrayContaining([
      expect.objectContaining({ value: 'Nutrition Facts' }),
      expect.objectContaining({ value: 'Ingredients: coconut water, mango puree' }),
    ]),
  )
})

