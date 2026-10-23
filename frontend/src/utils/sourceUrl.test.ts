import { describe, expect, it } from 'vitest'
import { isOfficialFdaUrl, ALLOWED_FDA_HOSTNAMES } from './sourceUrl'

describe('isOfficialFdaUrl', () => {
  it('allows all approved FDA hostnames with HTTPS and default/443 port', () => {
    ALLOWED_FDA_HOSTNAMES.forEach(host => {
      expect(isOfficialFdaUrl(`https://${host}/drug/test`)).toBe(true)
      expect(isOfficialFdaUrl(`https://${host}:443/drug/test`)).toBe(true)
    })
  })

  it('specifically validates download.open.fda.gov recall enforcement URLs', () => {
    const recallDownloadUrl =
      'https://download.open.fda.gov/drug/enforcement/drug-enforcement-0001-of-0001.json.zip'
    expect(isOfficialFdaUrl(recallDownloadUrl)).toBe(true)
  })

  it('rejects HTTP non-secure protocols', () => {
    expect(isOfficialFdaUrl('http://api.fda.gov/drug/test')).toBe(false)
    expect(isOfficialFdaUrl('http://download.open.fda.gov/drug/test')).toBe(false)
  })

  it('rejects malicious phishing domains and subdomains', () => {
    expect(isOfficialFdaUrl('https://api.fda.gov.attacker.com/drug/test')).toBe(false)
    expect(isOfficialFdaUrl('https://download.open.fda.gov.evil.org/pharma')).toBe(false)
    expect(isOfficialFdaUrl('https://evil-api.fda.gov/')).toBe(false)
    expect(isOfficialFdaUrl('https://google.com')).toBe(false)
  })

  it('rejects embedded credentials (user:pass in authority)', () => {
    expect(isOfficialFdaUrl('https://user:pass@api.fda.gov/drug/test')).toBe(false)
    expect(isOfficialFdaUrl('https://admin@download.open.fda.gov/')).toBe(false)
  })

  it('rejects non-standard ports', () => {
    expect(isOfficialFdaUrl('https://api.fda.gov:8080/drug/test')).toBe(false)
    expect(isOfficialFdaUrl('https://download.open.fda.gov:8443/')).toBe(false)
  })

  it('rejects null, undefined, empty, or malformed URLs safely', () => {
    expect(isOfficialFdaUrl(null)).toBe(false)
    expect(isOfficialFdaUrl(undefined)).toBe(false)
    expect(isOfficialFdaUrl('')).toBe(false)
    expect(isOfficialFdaUrl('not-a-url')).toBe(false)
    expect(isOfficialFdaUrl('javascript:alert(1)')).toBe(false)
  })
})
