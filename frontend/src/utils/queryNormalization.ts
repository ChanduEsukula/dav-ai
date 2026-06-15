export type SafetyQueryArea = 'pharmacy' | 'food' | 'cosmetic'

export type QueryNormalization = {
  rawQuery: string
  normalizedQuery: string
  correctionApplied: boolean
}

export type QuerySuggestion = {
  query: string
  area: SafetyQueryArea
  workflowLabel: string
}

const workflowLabels: Record<SafetyQueryArea, string> = {
  pharmacy: 'Pharmacy Safety',
  food: 'Food & Supplement Safety',
  cosmetic: 'Cosmetic Safety',
}

const aliasesByArea: Record<SafetyQueryArea, Record<string, string>> = {
  food: {
    strawberries: 'strawberry',
    berries: 'berry',
    eggs: 'egg',
    vitamins: 'vitamin',
    multivitamin: 'vitamin',
    cookies: 'cookie',
    tomatoes: 'tomato',
    potatoes: 'potato',
    proteinpowder: 'protein powder',
    'protein-powder': 'protein powder',
    'protien powder': 'protein powder',
    peanutbutter: 'peanut butter',
    peanutbutters: 'peanut butter',
    'peanut-butter': 'peanut butter',
    chickenbreast: 'chicken breast',
    chiken: 'chicken',
    'e coli': 'e. coli',
    'e-coli': 'e. coli',
    'e.coli': 'e. coli',
    ecoli: 'e. coli',
    preworkout: 'pre workout',
    'pre-workout': 'pre workout',
  },
  cosmetic: {
    hairdye: 'hair dye',
    hairdyes: 'hair dye',
    sunscrean: 'sunscreen',
    'sun screen': 'sunscreen',
    sunscreens: 'sunscreen',
    moisturizers: 'moisturizer',
    lipsticks: 'lipstick',
    shampoos: 'shampoo',
    conditioners: 'conditioner',
  },
  pharmacy: {
    xanex: 'xanax',
    metforimn: 'metformin',
    metfromin: 'metformin',
    metformins: 'metformin',
    ibruprofen: 'ibuprofen',
    ibuprofin: 'ibuprofen',
    ibuprofens: 'ibuprofen',
    amoxycillin: 'amoxicillin',
    acetaminophin: 'acetaminophen',
    aspirins: 'aspirin',
  },
}

const extraSuggestionsByArea: Record<SafetyQueryArea, string[]> = {
  pharmacy: ['xanax', 'metformin', 'ibuprofen', 'amoxicillin', 'acetaminophen', 'aspirin'],
  food: [
    'strawberry',
    'berry',
    'egg',
    'vitamin',
    'cookie',
    'tomato',
    'potato',
    'protein powder',
    'peanut butter',
    'chicken breast',
  ],
  cosmetic: [
    'hair dye',
    'sunscreen',
    'moisturizer',
    'lipstick',
    'shampoo',
    'conditioner',
  ],
}

export function normalizeSearchTerm(rawQuery: string) {
  return rawQuery.trim().replace(/\s+/g, ' ')
}

function stripSurroundingPunctuation(value: string) {
  return value.replace(/^[!"#$%&'()*+,/:;<=>?@[\\\]^_`{|}~]+/, '').replace(
    /[!"#$%&'()*+,/:;<=>?@[\\\]^_`{|}~]+$/,
    '',
  )
}

export function getSearchComparisonKey(rawQuery: string) {
  return stripSurroundingPunctuation(normalizeSearchTerm(rawQuery))
    .toLocaleLowerCase('en-US')
}

export function areSearchTermsEquivalent(firstQuery: string, secondQuery: string) {
  return getSearchComparisonKey(firstQuery) === getSearchComparisonKey(secondQuery)
}

export function normalizeSafetyQuery(
  rawQuery: string,
  area?: SafetyQueryArea,
): QueryNormalization {
  const rawQueryValue = normalizeSearchTerm(rawQuery)
  const lookupKey = getSearchComparisonKey(rawQueryValue)
  const areas = area ? [area] : (['pharmacy', 'food', 'cosmetic'] as const)

  let normalizedQuery = stripSurroundingPunctuation(rawQueryValue)

  for (const candidateArea of areas) {
    const alias = aliasesByArea[candidateArea][lookupKey]
    if (alias) {
      normalizedQuery = alias
      break
    }
  }

  return {
    rawQuery: rawQueryValue,
    normalizedQuery,
    correctionApplied:
      Boolean(rawQueryValue) &&
      getSearchComparisonKey(rawQueryValue) !== getSearchComparisonKey(normalizedQuery),
  }
}

export function getQuerySuggestions(
  rawQuery: string,
  area?: SafetyQueryArea,
  limit = 5,
): QuerySuggestion[] {
  const lookupKey = getSearchComparisonKey(rawQuery)
  if (lookupKey.length < 2) return []

  const areas = area ? [area] : (['pharmacy', 'food', 'cosmetic'] as const)
  const suggestions: QuerySuggestion[] = []
  const seen = new Set<string>()

  for (const candidateArea of areas) {
    const candidates = [
      ...Object.entries(aliasesByArea[candidateArea]).flatMap(([alias, canonical]) => [
        { matchValue: alias, query: canonical },
        { matchValue: canonical, query: canonical },
      ]),
      ...extraSuggestionsByArea[candidateArea].map((query) => ({
        matchValue: query,
        query,
      })),
    ]

    for (const candidate of candidates) {
      if (
        !candidate.matchValue.startsWith(lookupKey) &&
        !candidate.query.startsWith(lookupKey)
      ) {
        continue
      }

      const suggestionKey = `${candidateArea}:${candidate.query}`
      if (seen.has(suggestionKey)) continue

      seen.add(suggestionKey)
      suggestions.push({
        query: candidate.query,
        area: candidateArea,
        workflowLabel: workflowLabels[candidateArea],
      })
    }
  }

  return suggestions.slice(0, limit)
}

