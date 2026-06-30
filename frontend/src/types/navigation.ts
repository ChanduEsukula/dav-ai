export const PAGE_IDS = {
  HOME: 'home',
  PUBLIC_SAFETY: 'public-safety',
  PHARMACY_SAFETY: 'pharmacy-safety',
  FOOD_SAFETY: 'food-safety',
  COSMETIC_SAFETY: 'cosmetic-safety',
  PRODUCT_SCAN: 'productscan',
  REGIONAL_HEALTH: 'regional-health',
  SOURCES: 'sources',
  AUDIT: 'audit',
  SYSTEM: 'system',
  SAVED_MONITORS: 'saved-monitors',
  SIGNUP: 'signup',
  LOGIN: 'login',
  ONBOARDING: 'onboarding',
  PROFILE: 'profile',
  ABOUT: 'about',
  FAQ: 'faq',
  HELP: 'help',
} as const

export type ActivePage = (typeof PAGE_IDS)[keyof typeof PAGE_IDS]
export type UrlPage = Exclude<ActivePage, typeof PAGE_IDS.HOME>
export type SafetyDetailPage =
  | typeof PAGE_IDS.PUBLIC_SAFETY
  | typeof PAGE_IDS.PHARMACY_SAFETY
  | typeof PAGE_IDS.FOOD_SAFETY
  | typeof PAGE_IDS.COSMETIC_SAFETY

type PageMetadata = {
  id: ActivePage
  label: string
}

export const PAGE_METADATA = {
  [PAGE_IDS.HOME]: { id: PAGE_IDS.HOME, label: 'Home' },
  [PAGE_IDS.PUBLIC_SAFETY]: {
    id: PAGE_IDS.PUBLIC_SAFETY,
    label: 'Safety Search',
  },
  [PAGE_IDS.PHARMACY_SAFETY]: {
    id: PAGE_IDS.PHARMACY_SAFETY,
    label: 'DrugSignal',
  },
  [PAGE_IDS.FOOD_SAFETY]: { id: PAGE_IDS.FOOD_SAFETY, label: 'FoodSignal' },
  [PAGE_IDS.COSMETIC_SAFETY]: {
    id: PAGE_IDS.COSMETIC_SAFETY,
    label: 'Personal Care Signals',
  },
  [PAGE_IDS.PRODUCT_SCAN]: { id: PAGE_IDS.PRODUCT_SCAN, label: 'Scan beta' },
  [PAGE_IDS.REGIONAL_HEALTH]: {
    id: PAGE_IDS.REGIONAL_HEALTH,
    label: 'Regional Health Lab',
  },
  [PAGE_IDS.SOURCES]: { id: PAGE_IDS.SOURCES, label: 'Sources' },
  [PAGE_IDS.AUDIT]: { id: PAGE_IDS.AUDIT, label: 'Audit' },
  [PAGE_IDS.SYSTEM]: { id: PAGE_IDS.SYSTEM, label: 'System' },
  [PAGE_IDS.SAVED_MONITORS]: { id: PAGE_IDS.SAVED_MONITORS, label: 'Monitors' },
  [PAGE_IDS.SIGNUP]: { id: PAGE_IDS.SIGNUP, label: 'Sign up' },
  [PAGE_IDS.LOGIN]: { id: PAGE_IDS.LOGIN, label: 'Log in' },
  [PAGE_IDS.ONBOARDING]: { id: PAGE_IDS.ONBOARDING, label: 'Onboarding' },
  [PAGE_IDS.PROFILE]: { id: PAGE_IDS.PROFILE, label: 'Profile' },
  [PAGE_IDS.ABOUT]: { id: PAGE_IDS.ABOUT, label: 'About' },
  [PAGE_IDS.FAQ]: { id: PAGE_IDS.FAQ, label: 'FAQ' },
  [PAGE_IDS.HELP]: { id: PAGE_IDS.HELP, label: 'Help' },
} as const satisfies Record<ActivePage, PageMetadata>

export const URL_PAGE_IDS = [
  PAGE_IDS.PUBLIC_SAFETY,
  PAGE_IDS.PHARMACY_SAFETY,
  PAGE_IDS.FOOD_SAFETY,
  PAGE_IDS.COSMETIC_SAFETY,
  PAGE_IDS.PRODUCT_SCAN,
  PAGE_IDS.REGIONAL_HEALTH,
  PAGE_IDS.SOURCES,
  PAGE_IDS.AUDIT,
  PAGE_IDS.SYSTEM,
  PAGE_IDS.SAVED_MONITORS,
  PAGE_IDS.SIGNUP,
  PAGE_IDS.LOGIN,
  PAGE_IDS.ONBOARDING,
  PAGE_IDS.PROFILE,
  PAGE_IDS.ABOUT,
  PAGE_IDS.FAQ,
  PAGE_IDS.HELP,
] as const satisfies readonly UrlPage[]

export const PRIMARY_NAV_PAGE_IDS = [
  PAGE_IDS.HOME,
  PAGE_IDS.PUBLIC_SAFETY,
  PAGE_IDS.SAVED_MONITORS,
  PAGE_IDS.ABOUT,
] as const satisfies readonly ActivePage[]

export const OPERATIONS_NAV_PAGE_IDS = [
  PAGE_IDS.PHARMACY_SAFETY,
  PAGE_IDS.FOOD_SAFETY,
  PAGE_IDS.COSMETIC_SAFETY,
  PAGE_IDS.AUDIT,
  PAGE_IDS.SOURCES,
  PAGE_IDS.SYSTEM,
] as const satisfies readonly ActivePage[]

export const INFORMATION_NAV_PAGE_IDS = [
  PAGE_IDS.FAQ,
  PAGE_IDS.HELP,
] as const satisfies readonly ActivePage[]

export const ADVANCED_NAV_PAGE_IDS = [
  PAGE_IDS.PHARMACY_SAFETY,
  PAGE_IDS.FOOD_SAFETY,
  PAGE_IDS.COSMETIC_SAFETY,
  PAGE_IDS.PRODUCT_SCAN,
  PAGE_IDS.REGIONAL_HEALTH,
  PAGE_IDS.AUDIT,
  PAGE_IDS.SOURCES,
  PAGE_IDS.SYSTEM,
  PAGE_IDS.FAQ,
  PAGE_IDS.HELP,
] as const satisfies readonly ActivePage[]

const URL_PAGE_ID_SET: ReadonlySet<string> = new Set<string>(URL_PAGE_IDS)

export function isUrlPage(value: string | null): value is UrlPage {
  return value !== null && URL_PAGE_ID_SET.has(value)
}