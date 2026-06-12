import { useMemo, useState } from 'react'
import { searchCosmeticEvents, type CosmeticEventSearchResponse } from '../api/cosmeticEvents'
import { searchDrugEvents, type DrugEventSearchResponse } from '../api/drugEvents'
import {
  searchEverydaySafety,
  type EverydaySafetySearchResponse,
} from '../api/everydaySafety'
import { searchRecalls, type RecallSearchResponse } from '../api/recalls'
import { classifySafetyQuery, type SafetyRouteSuggestion } from '../utils/safetyRouteClassifier'
import type { ActivePage } from '../types/navigation'

type UniversalSafetySearchProps = {
  goToPage: (page: ActivePage, query?: string) => void
}

type UniversalPreview = {
  eyebrow: string
  title: string
  detail: string
  countLabel: string
  checklist: string[]
  disclaimer: string
}

type UniversalSearchData = {
  recall?: RecallSearchResponse
  drug?: DrugEventSearchResponse
  food?: EverydaySafetySearchResponse
  cosmetic?: CosmeticEventSearchResponse
}

const examples = ['Xanax', 'Chicken', 'Sunscreen', 'Protein powder', 'Shampoo']

function formatRecordLabel(count: number) {
  if (count === 1) return '1 possible public record found'
  return `${count} possible public records found`
}

function buildPreview(
  query: string,
  classification: ReturnType<typeof classifySafetyQuery>,
  data: UniversalSearchData,
): UniversalPreview {
  if (classification.primaryArea === 'pharmacy') {
    const recallCount = data.recall?.count ?? 0
    const drugCount = data.drug?.count ?? 0
    const totalCount = recallCount + drugCount

    return {
      eyebrow: 'Dav AI quick preview',
      title: `${query} looks like a drug or medication search.`,
      detail:
        'Dav AI checked for possible drug recall matches and public adverse-event reporting patterns. Use the full pharmacy workflow to review details before interpreting the result.',
      countLabel:
        totalCount > 0
          ? formatRecordLabel(totalCount)
          : 'No matching public records returned in this quick preview',
      checklist: [
        'Review drug recall matches separately from adverse-event reports.',
        'Check product name, strength, label, date, and manufacturer details.',
        'Do not treat public reports as proof of cause, diagnosis, or safety.',
      ],
      disclaimer:
        'This is not medical advice and does not say the drug is safe or unsafe. It only summarizes public-data matches for review.',
    }
  }

  if (classification.primaryArea === 'food') {
    const foodCount = data.food?.count ?? 0

    return {
      eyebrow: 'Dav AI quick preview',
      title: `${query} looks like a food or supplement search.`,
      detail:
        'Dav AI checked food and supplement safety records for possible public matches. Use the full food safety workflow to review product names, firms, dates, and recall reasons.',
      countLabel:
        foodCount > 0
          ? formatRecordLabel(foodCount)
          : 'No matching public records returned in this quick preview',
      checklist: [
        'Check whether the product name and brand actually match your item.',
        'Review firm, recall reason, package size, lot codes, and dates.',
        'No result does not guarantee that a product is safe.',
      ],
      disclaimer:
        'This preview is informational only. Public recall records should be verified against the exact product you have.',
    }
  }

  if (classification.primaryArea === 'cosmetic') {
    const cosmeticCount = data.cosmetic?.count ?? 0

    return {
      eyebrow: 'Dav AI quick preview',
      title: `${query} looks like a cosmetic or personal-care search.`,
      detail:
        'Dav AI checked cosmetic-event records for possible product or brand-related reports. Use the full cosmetic workflow to review report patterns and product context.',
      countLabel:
        cosmeticCount > 0
          ? formatRecordLabel(cosmeticCount)
          : 'No matching public records returned in this quick preview',
      checklist: [
        'Review product or brand names carefully.',
        'Look at reported reactions and event context.',
        'Reports are signals only and do not prove a product defect.',
      ],
      disclaimer:
        'Cosmetic-event reports are public safety signals. They do not prove cause, diagnosis, or product defect.',
    }
  }

  return {
    eyebrow: 'Dav AI needs one more step',
    title: `${query} may fit more than one safety area.`,
    detail:
      'This search could belong to more than one workflow. Choose the closest match so Dav AI can show the right detailed page.',
    countLabel: 'Choose a safety area to continue',
    checklist: [
      'Use Pharmacy Safety for drugs and medications.',
      'Use Food & Supplement Safety for food, supplements, meat, poultry, and egg products.',
      'Use Cosmetic Safety for cosmetics and personal-care products.',
    ],
    disclaimer:
      'This preview is only a routing step and does not make any safety conclusion.',
  }
}

function UniversalSafetySearch({ goToPage }: UniversalSafetySearchProps) {
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [searchData, setSearchData] = useState<UniversalSearchData>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const classification = useMemo(() => classifySafetyQuery(submittedQuery), [submittedQuery])

  const hasSubmittedQuery = submittedQuery.trim().length > 0
  const primarySuggestion = classification.suggestions[0]
  const preview = hasSubmittedQuery
    ? buildPreview(submittedQuery, classification, searchData)
    : null

  async function runPreviewSearch(nextQuery: string) {
    const cleanQuery = nextQuery.trim()
    if (!cleanQuery || loading) return

    const nextClassification = classifySafetyQuery(cleanQuery)

    setSubmittedQuery(cleanQuery)
    setSearchData({})
    setError('')
    setLoading(true)

    try {
      if (nextClassification.primaryArea === 'pharmacy') {
        const [recall, drug] = await Promise.all([
          searchRecalls(cleanQuery, 3),
          searchDrugEvents(cleanQuery, 5),
        ])

        setSearchData({ recall, drug })
      } else if (nextClassification.primaryArea === 'food') {
        const food = await searchEverydaySafety(cleanQuery, 5)
        setSearchData({ food })
      } else if (nextClassification.primaryArea === 'cosmetic') {
        const cosmetic = await searchCosmeticEvents(cleanQuery, 5)
        setSearchData({ cosmetic })
      }
    } catch {
      setError(
        'Dav AI could not load public records for this quick preview. You can still continue to the detailed workflow.',
      )
    } finally {
      setLoading(false)
    }
  }

  function handleAnalyze() {
    void runPreviewSearch(query)
  }

  function handleExampleClick(example: string) {
    setQuery(example)
    void runPreviewSearch(example)
  }

  function openSuggestion(suggestion: SafetyRouteSuggestion) {
    goToPage(suggestion.page, classification.query)
  }

  return (
    <section className="universal-safety-search" id="universal-safety-search">
      <div className="section-heading">
        <p className="eyebrow">Universal safety search</p>
        <h2>Search across Dav AI records.</h2>
        <p>
          Enter a product, drug, brand, food, supplement, cosmetic, UPC, NDC, or lot number. Dav AI
          checks the most relevant public-data workflow first.
        </p>
      </div>

      <div className="search-panel">
        <div className="search-box">
          <div className="search-field">
            <label className="field-label" htmlFor="universal-safety-query">
              Safety search
            </label>

            <input
              id="universal-safety-query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  handleAnalyze()
                }
              }}
              placeholder="Search: Xanax, chicken, sunscreen, protein powder, shampoo"
              aria-describedby="universal-safety-helper"
            />

            <p className="field-helper" id="universal-safety-helper">
              Public records only. Not medical advice, clinical advice, or a safety guarantee.
            </p>
          </div>

          <button type="button" onClick={handleAnalyze} disabled={loading}>
            {loading ? 'Checking...' : 'Analyze'}
          </button>
        </div>

        <div className="universal-safety-search__examples" aria-label="Example searches">
          {examples.map((example) => (
            <button key={example} type="button" onClick={() => handleExampleClick(example)}>
              {example}
            </button>
          ))}
        </div>

        {loading && (
          <p className="loading-helper" role="status" aria-live="polite">
            Checking public records for a quick preview...
          </p>
        )}

        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}

        {hasSubmittedQuery && preview && !loading && (
          <div className="universal-safety-search__result" aria-live="polite">
            <div>
              <small>{preview.eyebrow}</small>

              <h3>{preview.title}</h3>

              <p>{preview.detail}</p>

              <strong className="universal-safety-search__count">{preview.countLabel}</strong>

              <ul className="universal-safety-search__checklist">
                {preview.checklist.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>

              <p className="universal-safety-search__disclaimer">{preview.disclaimer}</p>
            </div>

            {classification.primaryArea !== 'ambiguous' ? (
              <button
                type="button"
                className="universal-safety-search__know-more"
                onClick={() => openSuggestion(primarySuggestion)}
              >
                Know more
              </button>
            ) : (
              <div className="universal-safety-search__choices">
                {classification.suggestions.map((suggestion) => (
                  <button
                    key={suggestion.page}
                    type="button"
                    onClick={() => openSuggestion(suggestion)}
                  >
                    {suggestion.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  )
}

export default UniversalSafetySearch