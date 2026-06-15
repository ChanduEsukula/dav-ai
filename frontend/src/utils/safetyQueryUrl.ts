import type { ActivePage } from '../types/navigation'
import {
  getSearchComparisonKey,
  normalizeSearchTerm,
} from './queryNormalization'

export type SafetyQueryState = {
  query: string
  rawQuery: string
}

export function readSafetyQueryFromUrl(): SafetyQueryState {
  const params = new URLSearchParams(window.location.search)
  const query = normalizeSearchTerm(params.get('q') ?? '')
  const rawQuery = normalizeSearchTerm(params.get('raw_q') ?? query)

  return { query, rawQuery }
}

export function writeSafetyQueryToUrl(
  page: ActivePage,
  query: string,
  rawQuery: string,
  mode: 'push' | 'replace',
) {
  const url = new URL(window.location.href)
  const cleanQuery = normalizeSearchTerm(query)
  const cleanRawQuery = normalizeSearchTerm(rawQuery)
  const shouldPreserveRawQuery =
    Boolean(cleanRawQuery) &&
    getSearchComparisonKey(cleanRawQuery) !== getSearchComparisonKey(cleanQuery)

  url.searchParams.set('page', page)

  if (cleanQuery) {
    url.searchParams.set('q', cleanQuery)
  } else {
    url.searchParams.delete('q')
  }

  if (shouldPreserveRawQuery) {
    url.searchParams.set('raw_q', cleanRawQuery)
  } else {
    url.searchParams.delete('raw_q')
  }

  const nextUrl = url.toString()
  if (nextUrl === window.location.href) return

  if (mode === 'push') {
    window.history.pushState(null, '', nextUrl)
  } else {
    window.history.replaceState(null, '', nextUrl)
  }
}

