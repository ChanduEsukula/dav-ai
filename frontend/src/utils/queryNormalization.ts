export type SafetyQueryArea = 'public_safety' | 'pharmacy' | 'food' | 'cosmetic'

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

const suggestionAreas = ['public_safety', 'pharmacy', 'food', 'cosmetic'] as const

const workflowLabels: Record<SafetyQueryArea, string> = {
  public_safety: 'Public Safety Search',
  pharmacy: 'Pharmacy Safety',
  food: 'Food & Supplement Safety',
  cosmetic: 'Cosmetic Safety',
}

const aliasesByArea: Record<SafetyQueryArea, Record<string, string>> = {
  public_safety: {},
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
  public_safety: [
    'tire',
    'scooter',
    'electric scooter',
    'air fryer',
    'car seat',
    'battery',
    'power bank',
    'NDC 66715 6547',
    'Advil',
    'Tylenol',
    'tylonal',
    'blood sugar monitor',
    'glucose meter',
    'insulin pump',
    'CPAP',
    'Toyota Camry',
    'Honda Civic',
  ],
  pharmacy: [
    'ibuprofen',
    'acetaminophen',
    'aspirin',
    'naproxen',
    'diphenhydramine',
    'cetirizine',
    'loratadine',
    'amoxicillin',
    'azithromycin',
    'doxycycline',
    'penicillin',
    'metformin',
    'insulin',
    'ozempic',
    'wegovy',
    'mounjaro',
    'xanax',
    'alprazolam',
    'adderall',
    'lisinopril',
    'atorvastatin',
    'losartan',
    'omeprazole',
    'levothyroxine',
    'prednisone',
    'gabapentin',
    'sertraline',
    'fluoxetine',
    'cough syrup',
    'eye drops',
    'nasal spray',
    'antacid',
  ],
  food: [
    'apple',
    'banana',
    'orange',
    'mango',
    'guava',
    'strawberry',
    'strawberries',
    'blueberry',
    'blueberries',
    'raspberry',
    'grapes',
    'watermelon',
    'pineapple',
    'peach',
    'pear',
    'plum',
    'cherry',
    'kiwi',
    'lemon',
    'lime',
    'avocado',
    'lettuce',
    'spinach',
    'kale',
    'tomato',
    'onion',
    'potato',
    'carrot',
    'broccoli',
    'cauliflower',
    'cucumber',
    'cabbage',
    'celery',
    'mushroom',
    'bell pepper',
    'jalapeno',
    'garlic',
    'ginger',
    'chicken',
    'beef',
    'ground beef',
    'pork',
    'turkey',
    'fish',
    'salmon',
    'tuna',
    'shrimp',
    'eggs',
    'tofu',
    'milk',
    'cheese',
    'yogurt',
    'butter',
    'cream',
    'ice cream',
    'rice',
    'pasta',
    'noodles',
    'bread',
    'cereal',
    'flour',
    'sugar',
    'protein powder',
    'whey protein',
    'creatine',
    'collagen',
    'pre workout',
    'electrolyte powder',
    'peanut butter',
    'almond butter',
    'jam',
    'honey',
    'oats',
    'granola',
    'frozen fruit',
    'frozen vegetables',
    'sprouts',
    'juice',
    'soda',
    'coffee',
    'tea',
    'energy drink',
    'coconut water',
  ],
  cosmetic: [
    'shampoo',
    'conditioner',
    'hair dye',
    'hair color',
    'hair gel',
    'hair spray',
    'sunscreen',
    'lotion',
    'moisturizer',
    'face cream',
    'serum',
    'cleanser',
    'toner',
    'lipstick',
    'lip gloss',
    'mascara',
    'eyeliner',
    'eyeshadow',
    'foundation',
    'concealer',
    'blush',
    'powder',
    'deodorant',
    'perfume',
    'cologne',
    'body wash',
    'soap',
    'toothpaste',
    'nail polish',
    'nail glue',
    'acrylic nails',
    'baby powder',
    'talc',
    'retinol',
    'salicylic acid',
    'benzoyl peroxide',
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
  const areas = area
    ? [area]
    : (['public_safety', 'pharmacy', 'food', 'cosmetic'] as const)

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
  limit = 8,
): QuerySuggestion[] {
  const lookupKey = getSearchComparisonKey(rawQuery)
  if (lookupKey.length < 2) return []

  const areas = area ? [area] : suggestionAreas
  const matches: Array<{
    suggestion: QuerySuggestion
    rank: number
    order: number
  }> = []
  const seen = new Set<string>()
  let order = 0

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
      const matchValueKey = getSearchComparisonKey(candidate.matchValue)
      const queryKey = getSearchComparisonKey(candidate.query)
      const isPrefixMatch =
        matchValueKey.startsWith(lookupKey) || queryKey.startsWith(lookupKey)
      const isContainsMatch =
        matchValueKey.includes(lookupKey) || queryKey.includes(lookupKey)

      if (!isPrefixMatch && !isContainsMatch) {
        order += 1
        continue
      }

      const suggestionKey = `${candidateArea}:${candidate.query}`
      if (seen.has(suggestionKey)) {
        order += 1
        continue
      }

      seen.add(suggestionKey)
      matches.push({
        suggestion: {
          query: candidate.query,
          area: candidateArea,
          workflowLabel: workflowLabels[candidateArea],
        },
        rank: isPrefixMatch ? 0 : 1,
        order,
      })
      order += 1
    }
  }

  return matches
    .sort((first, second) => first.rank - second.rank || first.order - second.order)
    .slice(0, limit)
    .map((match) => match.suggestion)
}
