import {
  readSafetyQueryFromUrl,
  writeSafetyQueryToUrl,
} from './safetyQueryUrl'

beforeEach(() => {
  window.history.replaceState(null, '', '/')
})

test('writes normalized and original query parameters when they differ', () => {
  writeSafetyQueryToUrl('food-safety', 'strawberry', 'strawberries', 'push')

  const params = new URLSearchParams(window.location.search)
  expect(params.get('page')).toBe('food-safety')
  expect(params.get('q')).toBe('strawberry')
  expect(params.get('raw_q')).toBe('strawberries')
  expect(readSafetyQueryFromUrl()).toEqual({
    query: 'strawberry',
    rawQuery: 'strawberries',
  })
})

test('keeps existing q-only deep links compatible', () => {
  window.history.replaceState(null, '', '/?page=cosmetic-safety&q=Shampoo')

  expect(readSafetyQueryFromUrl()).toEqual({
    query: 'Shampoo',
    rawQuery: 'Shampoo',
  })
})
