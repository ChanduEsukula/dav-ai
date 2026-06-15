import {
  areSearchTermsEquivalent,
  classifySafetyQuery,
  getTypoSuggestion,
  getWrongCategorySuggestion,
  normalizeSearchTerm,
} from './safetyRouteClassifier'

test('normalizes only whitespace and preserves useful product identifier characters', () => {
  expect(normalizeSearchTerm('  NDC  12345-6789 / 10 mg (XR)  ')).toBe(
    'NDC 12345-6789 / 10 mg (XR)',
  )
})

test('compares normalized search terms case-insensitively', () => {
  expect(areSearchTermsEquivalent('  Xanax   XR ', 'xANAX xr')).toBe(true)
})

test.each([
  ['metformin', 'pharmacy'],
  ['protein powder', 'food'],
  ['sunscreen SPF 50', 'cosmetic'],
] as const)('classifies %s as %s', (query, area) => {
  expect(classifySafetyQuery(query).primaryArea).toBe(area)
})

test('keeps unknown queries ambiguous instead of overclaiming', () => {
  expect(classifySafetyQuery('ACME product 123-ABC').primaryArea).toBe('ambiguous')
})

test('returns calm cross-category suggestions only for clear mismatches', () => {
  expect(getWrongCategorySuggestion('pharmacy', 'chicken')?.message).toBe(
    'This looks more like a Food & Supplement Safety search. Open Food & Supplement Safety for better results?',
  )
  expect(getWrongCategorySuggestion('pharmacy', 'unknown product')).toBeNull()
})

test.each([
  ['metforimn', 'Metformin'],
  ['IBUPROFIN', 'Ibuprofen'],
  ['  protien   powder ', 'Protein powder'],
] as const)('returns the approved typo suggestion for %s', (query, correction) => {
  expect(getTypoSuggestion(query)).toBe(correction.toLocaleLowerCase())
})

test('does not invent typo corrections outside the approved list', () => {
  expect(getTypoSuggestion('metforman')).toBeNull()
})

test.each([
  ['xanex', 'pharmacy'],
  ['strawberries', 'food'],
  ['hairdye', 'cosmetic'],
] as const)('classifies approved aliases such as %s after normalization', (query, area) => {
  expect(classifySafetyQuery(query).primaryArea).toBe(area)
})
