export type ProductScanCandidateType = 'product' | 'brand' | 'ndc' | 'upc' | 'lot'

export type ProductScanCandidate = {
  id: string
  type: ProductScanCandidateType
  label: string
  value: string
  detail: string
}

const candidateTypeLabels: Record<ProductScanCandidateType, string> = {
  product: 'Possible product name',
  brand: 'Possible brand or manufacturer',
  ndc: 'Possible NDC-like code',
  upc: 'Possible UPC-like code',
  lot: 'Possible lot, code, or date',
}

const noisyProductLinePatterns = [
  /\b(?:nutrition|supplement|drug)\s+facts\b/i,
  /\bingredients?\b/i,
  /\bactive ingredient\b/i,
  /\binactive ingredients?\b/i,
  /\bdirections?\b/i,
  /\bwarnings?\b/i,
  /\buses?\b/i,
  /\bdistributed by\b/i,
  /\bmanufactured by\b/i,
  /\bmade by\b/i,
  /\bmanufacturer\b/i,
  /\bbrand\b/i,
  /\b(?:upc|gtin|barcode|ndc|lot|batch|exp|expires|expiration|best by|use by)\b/i,
  /\b(?:www|http|phone|tel)\b/i,
]

function compactWhitespace(value: string) {
  return value.replace(/\s+/g, ' ').trim()
}

function cleanCandidateValue(value: string) {
  return compactWhitespace(value)
    .replace(/^[#:;,\-.()\s]+/, '')
    .replace(/[#:;,\-.()\s]+$/, '')
}

function candidateId(type: ProductScanCandidateType, value: string) {
  return `${type}:${value.toLocaleLowerCase('en-US')}`
}

function isUsefulPhrase(value: string) {
  const cleaned = cleanCandidateValue(value)
  return cleaned.length >= 3 && /[a-z0-9]/i.test(cleaned)
}

function normalizeIdentifier(value: string) {
  return value.replace(/\s+/g, '').replace(/--+/g, '-').trim()
}

function addCandidate(
  candidates: ProductScanCandidate[],
  seen: Set<string>,
  type: ProductScanCandidateType,
  value: string,
  detail: string,
) {
  const cleaned = cleanCandidateValue(value)
  if (!isUsefulPhrase(cleaned)) return

  const id = candidateId(type, cleaned)
  if (seen.has(id)) return

  seen.add(id)
  candidates.push({
    id,
    type,
    label: candidateTypeLabels[type],
    value: cleaned,
    detail,
  })
}

function extractLineMatches(
  lines: string[],
  patterns: Array<{ type: ProductScanCandidateType; regex: RegExp; detail: string }>,
  candidates: ProductScanCandidate[],
  seen: Set<string>,
) {
  for (const line of lines) {
    for (const pattern of patterns) {
      const match = line.match(pattern.regex)
      if (match?.[1]) {
        addCandidate(candidates, seen, pattern.type, match[1], pattern.detail)
      }
    }
  }
}

function extractRegexMatches(
  text: string,
  regex: RegExp,
  type: ProductScanCandidateType,
  detail: string,
  candidates: ProductScanCandidate[],
  seen: Set<string>,
  transform: (value: string) => string = (value) => value,
) {
  for (const match of text.matchAll(regex)) {
    if (match[1]) {
      addCandidate(candidates, seen, type, transform(match[1]), detail)
    }
  }
}

function looksLikeProductLine(line: string) {
  if (line.length < 4 || line.length > 70) return false
  if (!/[a-z]/i.test(line)) return false
  if (/^\d+[\d\s-]*$/.test(line)) return false
  return !noisyProductLinePatterns.some((pattern) => pattern.test(line))
}

export function extractProductScanCandidates(rawText: string): ProductScanCandidate[] {
  const text = compactWhitespace(rawText.replace(/\r/g, '\n'))
  if (!text) return []

  const lines = rawText
    .split(/\n+/)
    .map((line) => cleanCandidateValue(line))
    .filter(Boolean)
  const candidates: ProductScanCandidate[] = []
  const seen = new Set<string>()

  extractLineMatches(
    lines,
    [
      {
        type: 'product',
        regex: /\b(?:product(?:\s+name)?|item|name)\s*[:-]\s*(.+)$/i,
        detail: 'Found near a product or item label.',
      },
      {
        type: 'brand',
        regex: /\b(?:brand|manufacturer|manufactured by|distributed by|made by|mfg\.?\s+by|company)\s*[:-]?\s*(.+)$/i,
        detail: 'Found near a brand, manufacturer, or distributor label.',
      },
    ],
    candidates,
    seen,
  )

  for (const line of lines) {
    if (candidates.filter((candidate) => candidate.type === 'product').length >= 3) {
      break
    }

    if (looksLikeProductLine(line)) {
      addCandidate(
        candidates,
        seen,
        'product',
        line,
        'Prominent readable label text. Review before searching.',
      )
    }
  }

  extractRegexMatches(
    text,
    /\bNDC(?:\s*(?:No\.?|#|number))?\s*[:#]?\s*([0-9]{4,5}[-\s]?[0-9]{3,4}[-\s]?[0-9]{1,2})\b/gi,
    'ndc',
    'Identifier-looking text only. Existing workflows may not resolve package-level codes.',
    candidates,
    seen,
    normalizeIdentifier,
  )

  extractRegexMatches(
    text,
    /\b(?:UPC|GTIN|barcode)(?:\s*(?:No\.?|#|number))?\s*[:#]?\s*([0-9][0-9\s-]{6,18}[0-9])\b/gi,
    'upc',
    'Identifier-looking text only. Verify against the package label.',
    candidates,
    seen,
    (value) => value.replace(/\D/g, ''),
  )

  extractRegexMatches(
    text,
    /\b([0-9]{12,14})\b/g,
    'upc',
    'Numeric code candidate. Verify before using as search text.',
    candidates,
    seen,
  )

  extractRegexMatches(
    text,
    /\b(?:lot|batch|code)\s*(?:No\.?|#|number)?\s*[:#]?\s*([A-Z0-9][A-Z0-9./-]{2,20})\b/gi,
    'lot',
    'Lot, batch, or code-looking text for manual review.',
    candidates,
    seen,
  )

  extractRegexMatches(
    text,
    /\b(?:exp|expires|expiration|use by|best by)\s*(?:date)?\s*[:#]?\s*([A-Z0-9][A-Z0-9./-]{2,20})\b/gi,
    'lot',
    'Date-looking label text for manual review.',
    candidates,
    seen,
  )

  extractRegexMatches(
    text,
    /\b(\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}[/-]\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4})\b/gi,
    'lot',
    'Date-looking label text for manual review.',
    candidates,
    seen,
  )

  return candidates.slice(0, 18)
}
