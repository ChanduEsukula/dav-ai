export type SafetyArea = 'pharmacy' | 'food' | 'cosmetic' | 'ambiguous'

export type SafetyRouteSuggestion = {
  area: Exclude<SafetyArea, 'ambiguous'>
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

function includesAnyTerm(normalizedQuery: string, terms: string[]) {
  return terms.some((term) => normalizedQuery.includes(term))
}

export function classifySafetyQuery(rawQuery: string): SafetyRouteClassification {
  const query = rawQuery.trim()
  const normalizedQuery = query.toLowerCase()

  if (!query) {
    return {
      query,
      primaryArea: 'ambiguous',
      confidence: 'low',
      reason: 'Enter a product, brand, drug, food, supplement, cosmetic, UPC, NDC, or lot number.',
      suggestions: [pharmacySuggestion, foodSuggestion, cosmeticSuggestion],
    }
  }

  const matches = {
    pharmacy: includesAnyTerm(normalizedQuery, pharmacyTerms),
    food: includesAnyTerm(normalizedQuery, foodTerms),
    cosmetic: includesAnyTerm(normalizedQuery, cosmeticTerms),
  }

  const matchedAreas = Object.entries(matches)
    .filter(([, matched]) => matched)
    .map(([area]) => area)

  if (matchedAreas.length === 1) {
    if (matches.pharmacy) {
      return {
        query,
        primaryArea: 'pharmacy',
        confidence: 'high',
        reason: 'This looks most relevant to drug recalls or adverse event reporting.',
        suggestions: [pharmacySuggestion, foodSuggestion, cosmeticSuggestion],
      }
    }

    if (matches.food) {
      return {
        query,
        primaryArea: 'food',
        confidence: 'high',
        reason: 'This looks most relevant to food or supplement safety records.',
        suggestions: [foodSuggestion, pharmacySuggestion, cosmeticSuggestion],
      }
    }

    return {
      query,
      primaryArea: 'cosmetic',
      confidence: 'high',
      reason: 'This looks most relevant to cosmetic or personal-care safety records.',
      suggestions: [cosmeticSuggestion, pharmacySuggestion, foodSuggestion],
    }
  }

  if (matchedAreas.length > 1) {
    return {
      query,
      primaryArea: 'ambiguous',
      confidence: 'medium',
      reason: 'This query could match more than one safety area. Choose the best fit below.',
      suggestions: [
        ...(matches.pharmacy ? [pharmacySuggestion] : []),
        ...(matches.food ? [foodSuggestion] : []),
        ...(matches.cosmetic ? [cosmeticSuggestion] : []),
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