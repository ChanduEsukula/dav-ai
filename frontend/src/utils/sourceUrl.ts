/**
 * Validates whether a source URL is an official, verified FDA source.
 * Aligns strictly with backend policy in backend/app/services/pharma/evidence.py.
 */
export const ALLOWED_FDA_HOSTNAMES = Object.freeze([
  'api.fda.gov',
  'www.fda.gov',
  'fda.gov',
  'open.fda.gov',
  'download.open.fda.gov',
])

export function isOfficialFdaUrl(url: string | null | undefined): boolean {
  if (!url || typeof url !== 'string') return false
  try {
    const parsed = new URL(url)
    return (
      parsed.protocol === 'https:' &&
      ALLOWED_FDA_HOSTNAMES.includes(parsed.hostname) &&
      !parsed.username &&
      !parsed.password &&
      (!parsed.port || parsed.port === '443')
    )
  } catch {
    return false
  }
}
