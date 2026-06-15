export type SafetyArea = 'pharmacy' | 'food' | 'cosmetic' | 'ambiguous'
export type SafetyDetailArea = Exclude<SafetyArea, 'ambiguous'>

export type SafetyRouteSuggestion = {
  area: SafetyDetailArea
  label: string
  description: string
  page: 'pharmacy-safety' | 'food-safety' | 'cosmetic-safety'
}

export type SafetyRouteClassification = {
  query: string
  primaryArea: SafetyArea
  confidence: 'high' | 'medium' | 'low'
  reason: string
  suggestions: SafetyRouteSuggestion[]
}

export type WrongCategorySuggestion = SafetyRouteSuggestion & {
  message: string
}

const pharmacyTerms = [
  'drug',
  'medicine',
  'medication',
  'tablet',
  'capsule',
  'pill',
  'injection',
  'ndc',
  'xanax',
  'alprazolam',
  'tylenol',
  'acetaminophen',
  'advil',
  'ibuprofen',
  'metformin',
  'ozempic',
  'amoxicillin',
  'adderall',
  'insulin',
]

const foodTerms = [
  'food',
  'supplement',
  'protein',
  'powder',
  'protein powder',
  'peanut butter',
  'chicken',
  'beef',
  'egg',
  'eggs',
  'milk',
  'cheese',
  'lettuce',
  'spinach',
  'salmon',
  'tuna',
  'peanut',
  'almond',
  'cereal',
  'snack',
  'vitamin',
  'multivitamin',
  'upc',
]

const cosmeticTerms = [
  'cosmetic',
  'sunscreen',
  'shampoo',
  'conditioner',
  'mascara',
  'lipstick',
  'lotion',
  'cream',
  'serum',
  'moisturizer',
  'deodorant',
  'soap',
  'cleanser',
  'foundation',
  'makeup',
  'perfume',
  'fragrance',
  'hair dye',
]

const typoSuggestions: Record<string, string> = {
  metforimn: 'Metformin',
  metfromin: 'Metformin',
  ibruprofen: 'Ibuprofen',
  ibuprofin: 'Ibuprofen',
  xanex: 'Xanax',
  sunscrean: 'Sunscreen',
  'protien powder': 'Protein powder',
}

const pharmacySuggestion: SafetyRouteSuggestion = {
  area: 'pharmacy',
  label: 'Pharmacy Safety',
  description: 'Check drug recall records and adverse event reporting patterns.',
  page: 'pharmacy-safety',
}

const foodSuggestion: SafetyRouteSuggestion = {
  area: 'food',
  label: 'Food & Supplement Safety',
  description: 'Check food, supplement, meat, poultry, and egg-product safety records.',
  page: 'food-safety',
}

const cosmeticSuggestion: SafetyRouteSuggestion = {
  area: 'cosmetic',
  label: 'Cosmetic Safety',
  description: 'Check cosmetic and personal-care product safety reports.',
  page: 'cosmetic-safety',
}

const suggestionsByArea: Record<SafetyDetailArea, SafetyRouteSuggestion> = {
  pharmacy: pharmacySuggestion,
  food: foodSuggestion,
  cosmetic: cosmeticSuggestion,
}

export function normalizeSearchTerm(rawQuery: string) {
  return rawQuery.trim().replace(/\s+/g, ' ')
}

export function getSearchComparisonKey(rawQuery: string) {
  return normalizeSearchTerm(rawQuery).toLocaleLowerCase('en-US')
}

export function areSearchTermsEquivalent(firstQuery: string, secondQuery: string) {
  return getSearchComparisonKey(firstQuery) === getSearchComparisonKey(secondQuery)
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function includesTerm(normalizedQuery: string, term: string) {
  const termPattern = escapeRegExp(term).replace(/\s+/g, '\\s+')
  return new RegExp(`(^|[^a-z0-9])${termPattern}(?=$|[^a-z0-9])`, 'i').test(normalizedQuery)
}

function includesAnyTerm(normalizedQuery: string, terms: string[]) {
  return terms.some((term) => includesTerm(normalizedQuery, term))
}

export function classifySafetyQuery(rawQuery: string): SafetyRouteClassification {
  const query = normalizeSearchTerm(rawQuery)
  const normalizedQuery = getSearchComparisonKey(query)

  if (!query) {
    return {
      query,
      primaryArea: 'ambiguous',
      confidence: 'low',
      reason:
        'Enter a product, drug, brand, food, supplement, cosmetic, or ingredient to search public records.',
      suggestions: [pharmacySuggestion, foodSuggestion, cosmeticSuggestion],
    }
  }

  const matches = {
    pharmacy: includesAnyTerm(normalizedQuery, pharmacyTerms),
    food: includesAnyTerm(normalizedQuery, foodTerms),
    cosmetic: includesAnyTerm(normalizedQuery, cosmeticTerms),
  }

  const matchedAreas = (Object.entries(matches) as [SafetyDetailArea, boolean][])
    .filter(([, matched]) => matched)
    .map(([area]) => area)

  if (matchedAreas.length === 1) {
    const primaryArea = matchedAreas[0]
    const primarySuggestion = suggestionsByArea[primaryArea]

    return {
      query,
      primaryArea,
      confidence: 'high',
      reason:
        primaryArea === 'pharmacy'
          ? 'This looks most relevant to drug recalls or adverse event reporting.'
          : primaryArea === 'food'
            ? 'This looks most relevant to food or supplement safety records.'
            : 'This looks most relevant to cosmetic or personal-care safety records.',
      suggestions: [
        primarySuggestion,
        ...[pharmacySuggestion, foodSuggestion, cosmeticSuggestion].filter(
          (suggestion) => suggestion.area !== primaryArea,
        ),
      ],
    }
  }

  if (matchedAreas.length > 1) {
    return {
      query,
      primaryArea: 'ambiguous',
      confidence: 'medium',
      reason: 'This query could match more than one safety area. Choose the best fit below.',
      suggestions: [
        ...matchedAreas.map((area) => suggestionsByArea[area]),
        ...[pharmacySuggestion, foodSuggestion, cosmeticSuggestion].filter(
          (suggestion) => !matchedAreas.includes(suggestion.area),
        ),
      ],
    }
  }

  return {
    query,
    primaryArea: 'ambiguous',
    confidence: 'low',
    reason: 'Dav AI is not fully sure which safety area fits this search. Choose one to continue.',
    suggestions: [pharmacySuggestion, foodSuggestion, cosmeticSuggestion],
  }
}

export function getWrongCategorySuggestion(
  currentArea: SafetyDetailArea,
  rawQuery: string,
): WrongCategorySuggestion | null {
  const classification = classifySafetyQuery(rawQuery)

  if (
    classification.primaryArea === 'ambiguous' ||
    classification.primaryArea === currentArea
  ) {
    return null
  }

  const suggestion = suggestionsByArea[classification.primaryArea]

  return {
    ...suggestion,
    message: `This looks more like a ${suggestion.label} search. Open ${suggestion.label} for better results?`,
  }
}

export function getTypoSuggestion(rawQuery: string) {
  return typoSuggestions[getSearchComparisonKey(rawQuery)] ?? null
}
