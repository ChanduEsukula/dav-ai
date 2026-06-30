import {
  getSearchComparisonKey,
  normalizeSafetyQuery,
} from './queryNormalization'
import { PAGE_IDS, type SafetyDetailPage } from '../types/navigation'

export type SafetyArea =
  | 'public_safety'
  | 'pharmacy'
  | 'food'
  | 'cosmetic'
  | 'ambiguous'
export type SafetyDetailArea = Exclude<SafetyArea, 'ambiguous'>

export type SafetyRouteSuggestion = {
  area: SafetyDetailArea
  label: string
  description: string
  page: SafetyDetailPage
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

export {
  areSearchTermsEquivalent,
  getSearchComparisonKey,
  normalizeSearchTerm,
} from './queryNormalization'

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

const publicSafetyTerms = [
  'public safety',
  'recall',
  'recalls',
  'tire',
  'tires',
  'vehicle',
  'vin',
  'toyota',
  'honda',
  'ford',
  'tesla',
  'truck',
  'scooter',
  'electric scooter',
  'air fryer',
  'airfryer',
  'car seat',
  'carseat',
  'battery',
  'power bank',
  'powerbank',
  'glucose meter',
  'blood sugar monitor',
  'blood sugar meter',
  'cpap',
  'insulin pump',
  'ndc',
  'upc',
  'advil',
  'tylonal',
  'tylenol',
  'motrin',
  'benadryl',
  'claritin',
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
  'strawberry',
  'berry',
  'cookie',
  'tomato',
  'potato',
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
  label: 'DrugSignal',
  description: 'Check drug recall records and adverse event reporting patterns.',
  page: PAGE_IDS.PHARMACY_SAFETY,
}

const foodSuggestion: SafetyRouteSuggestion = {
  area: 'food',
  label: 'Food & Supplement Safety',
  description: 'Check food, supplement, meat, poultry, and egg-product safety records.',
  page: PAGE_IDS.FOOD_SAFETY,
}

const cosmeticSuggestion: SafetyRouteSuggestion = {
  area: 'cosmetic',
  label: 'Personal Care Signals',
  description: 'Check cosmetic and personal-care product safety reports.',
  page: PAGE_IDS.COSMETIC_SAFETY,
}

const publicSafetySuggestion: SafetyRouteSuggestion = {
  area: 'public_safety',
  label: 'Public Safety Search',
  description:
    'Check public recall, reference, label, vehicle, device, and consumer-product safety records.',
  page: PAGE_IDS.PUBLIC_SAFETY,
}

const suggestionsByArea: Record<SafetyDetailArea, SafetyRouteSuggestion> = {
  public_safety: publicSafetySuggestion,
  pharmacy: pharmacySuggestion,
  food: foodSuggestion,
  cosmetic: cosmeticSuggestion,
}

const allSuggestions = [
  publicSafetySuggestion,
  pharmacySuggestion,
  foodSuggestion,
  cosmeticSuggestion,
]

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
  const query = normalizeSafetyQuery(rawQuery).normalizedQuery
  const normalizedQuery = getSearchComparisonKey(query)

  if (!query) {
    return {
      query,
      primaryArea: 'ambiguous',
      confidence: 'low',
      reason:
        'Enter a product, drug, brand, food, supplement, cosmetic, or ingredient to search public records.',
      suggestions: allSuggestions,
    }
  }

  const matches = {
    public_safety: includesAnyTerm(normalizedQuery, publicSafetyTerms),
    pharmacy: includesAnyTerm(normalizedQuery, pharmacyTerms),
    food: includesAnyTerm(normalizedQuery, foodTerms),
    cosmetic: includesAnyTerm(normalizedQuery, cosmeticTerms),
  }

  const matchedAreas = (Object.entries(matches) as [SafetyDetailArea, boolean][])
    .filter(([, matched]) => matched)
    .map(([area]) => area)

  if (matchedAreas.length === 1 || matchedAreas.includes('public_safety')) {
    const primaryArea = matchedAreas.includes('public_safety')
      ? 'public_safety'
      : matchedAreas[0]
    const primarySuggestion = suggestionsByArea[primaryArea]

    return {
      query,
      primaryArea,
      confidence: 'high',
      reason:
        primaryArea === 'public_safety'
          ? 'This looks most relevant to public recall, reference, label, vehicle, device, or consumer-product records.'
          : primaryArea === 'pharmacy'
          ? 'This looks most relevant to drug recalls or adverse event reporting.'
          : primaryArea === 'food'
            ? 'This looks most relevant to food or supplement safety records.'
            : 'This looks most relevant to cosmetic or personal-care safety records.',
      suggestions: [
        primarySuggestion,
        ...allSuggestions.filter(
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
        ...allSuggestions.filter(
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
    suggestions: allSuggestions,
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
  const normalization = normalizeSafetyQuery(rawQuery)
  return normalization.correctionApplied ? normalization.normalizedQuery : null
}
