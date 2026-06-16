import {
  getQuerySuggestions,
  normalizeSafetyQuery,
} from './queryNormalization'

test.each([
  ['food', 'strawberries', 'strawberry'],
  ['food', 'berries', 'berry'],
  ['food', 'eggs', 'egg'],
  ['food', 'vitamins', 'vitamin'],
  ['food', 'cookies', 'cookie'],
  ['food', 'tomatoes', 'tomato'],
  ['food', 'potatoes', 'potato'],
  ['food', 'proteinpowder', 'protein powder'],
  ['food', 'peanutbutters', 'peanut butter'],
  ['food', 'chickenbreast', 'chicken breast'],
  ['cosmetic', 'hairdye', 'hair dye'],
  ['cosmetic', 'hairdyes', 'hair dye'],
  ['cosmetic', 'sunscrean', 'sunscreen'],
  ['cosmetic', 'sun screen', 'sunscreen'],
  ['cosmetic', 'sunscreens', 'sunscreen'],
  ['cosmetic', 'moisturizers', 'moisturizer'],
  ['cosmetic', 'lipsticks', 'lipstick'],
  ['cosmetic', 'shampoos', 'shampoo'],
  ['cosmetic', 'conditioners', 'conditioner'],
  ['pharmacy', 'xanex', 'xanax'],
  ['pharmacy', 'metforimn', 'metformin'],
  ['pharmacy', 'metformins', 'metformin'],
  ['pharmacy', 'ibuprofens', 'ibuprofen'],
  ['pharmacy', 'amoxycillin', 'amoxicillin'],
  ['pharmacy', 'acetaminophin', 'acetaminophen'],
  ['pharmacy', 'aspirins', 'aspirin'],
] as const)('normalizes bounded %s alias %s', (area, rawQuery, normalizedQuery) => {
  expect(normalizeSafetyQuery(rawQuery, area)).toEqual({
    rawQuery,
    normalizedQuery,
    correctionApplied: true,
  })
})

test('does not apply broad plural stemming to unknown words', () => {
  expect(normalizeSafetyQuery('glasses', 'cosmetic')).toEqual({
    rawQuery: 'glasses',
    normalizedQuery: 'glasses',
    correctionApplied: false,
  })
})

test('preserves user casing and compacts whitespace when no alias applies', () => {
  expect(normalizeSafetyQuery('  Xanax   XR  ', 'pharmacy')).toEqual({
    rawQuery: 'Xanax XR',
    normalizedQuery: 'Xanax XR',
    correctionApplied: false,
  })
})

test('suggests approved canonical queries after two characters', () => {
  expect(getQuerySuggestions('stra', 'food')[0]).toMatchObject({
    query: 'strawberry',
    area: 'food',
  })
  expect(getQuerySuggestions('haird', 'cosmetic')[0]).toMatchObject({
    query: 'hair dye',
    area: 'cosmetic',
  })
  expect(getQuerySuggestions('xan', 'pharmacy')[0]).toMatchObject({
    query: 'xanax',
    area: 'pharmacy',
  })
  expect(getQuerySuggestions('x', 'pharmacy')).toEqual([])
})

test('includes expanded curated workflow suggestions', () => {
  expect(getQuerySuggestions('gua', 'food')).toEqual([
    expect.objectContaining({ query: 'guava', area: 'food' }),
  ])
  expect(getQuerySuggestions('man', 'food')).toEqual([
    expect.objectContaining({ query: 'mango', area: 'food' }),
  ])
  expect(getQuerySuggestions('sun', 'cosmetic')).toEqual([
    expect.objectContaining({ query: 'sunscreen', area: 'cosmetic' }),
  ])
  expect(getQuerySuggestions('ibu', 'pharmacy')).toEqual([
    expect.objectContaining({ query: 'ibuprofen', area: 'pharmacy' }),
  ])
})

test('ranks prefix matches above contains matches', () => {
  const suggestions = getQuerySuggestions('but', 'food')

  expect(suggestions[0]).toMatchObject({ query: 'butter', area: 'food' })
  expect(
    suggestions.findIndex((suggestion) => suggestion.query === 'peanut butter'),
  ).toBeGreaterThan(0)
})

test('caps visible suggestions by default', () => {
  expect(getQuerySuggestions('er')).toHaveLength(8)
})
