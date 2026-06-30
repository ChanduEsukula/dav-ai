import { useMemo, useRef, useState } from 'react'
import { searchCosmeticEvents, type CosmeticEventSearchResponse } from '../api/cosmeticEvents'
import { searchDrugEvents, type DrugEventSearchResponse } from '../api/drugEvents'
import {
  searchEverydaySafety,
  type EverydaySafetySearchResponse,
} from '../api/everydaySafety'
import { searchRecalls, type RecallSearchResponse } from '../api/recalls'
import {
  classifySafetyQuery,
  getSearchComparisonKey,
  type SafetyRouteSuggestion,
} from '../utils/safetyRouteClassifier'
import { normalizeSafetyQuery } from '../utils/queryNormalization'
import type { ActivePage } from '../types/navigation'
import QueryNormalizationNotice from './QueryNormalizationNotice'
import QueryTypeahead from './QueryTypeahead'
import SourceIntegrationBadge from './SourceIntegrationBadge'
import SourceDetailsDisclosure from './SourceDetailsDisclosure'
import { getSourceIntegrationMode } from '../utils/sourceIntegrationMode'

type UniversalSafetySearchProps = {
  goToPage: (page: ActivePage, query?: string, rawQuery?: string) => void
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

type UniversalSourceIdentity = {
  sourceId?: string
  sourceName: string
  sourceType?: string
}

const examples = ['air fryer', 'Advil', 'NDC 66715 6547', 'Toyota Camry', 'sunscreen']

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
      eyebrow: 'Safety record preview',
      title: `${query} looks like a drug or medication search.`,
      detail:
        'Dav AI checked for possible drug recall matches and public adverse-event reporting patterns. Use the full DrugSignal workflow to review details before interpreting the result.',
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

  if (classification.primaryArea === 'public_safety') {
    return {
      eyebrow: 'Safety record handoff',
      title: `${query} belongs in Safety Record Search.`,
      detail:
        'Dav AI can check public recall, reference, label, vehicle, device, and consumer-product safety records with source roles and query-understanding details.',
      countLabel: 'Open full Safety Record Search',
      checklist: [
        'Review recall/enforcement records separately from reference or signal records.',
        'Check exact product, NDC, UPC, VIN, model, lot, and official source links.',
        'No result does not prove that a product is safe.',
      ],
      disclaimer:
        'Public records only. This routing preview does not run the full search or make any safety conclusion.',
    }
  }

  if (classification.primaryArea === 'food') {
    const foodCount = data.food?.count ?? 0

    return {
      eyebrow: 'Safety record preview',
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
        'No result does not prove that a product is safe.',
      ],
      disclaimer:
        'This preview is informational only. Public recall records should be verified against the exact product you have.',
    }
  }

  if (classification.primaryArea === 'cosmetic') {
    const cosmeticCount = data.cosmetic?.count ?? 0

    return {
      eyebrow: 'Safety record preview',
      title: `${query} looks like a cosmetic or personal-care search.`,
      detail:
        'Dav AI checked cosmetic-event records for possible product or brand-related reports. Use the full Personal Care Signals workflow to review report patterns and product context.',
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
        'Cosmetic-event reports are public reporting signals. They do not prove cause, diagnosis, or product defect.',
    }
  }

  return {
    eyebrow: 'Safety record routing',
    title: `${query} may fit more than one safety area.`,
    detail:
      'This search could belong to more than one workflow. Choose the closest match so Dav AI can show the right detailed page.',
    countLabel: 'Choose a safety area to continue',
    checklist: [
      'Use Safety Record Search for vehicles, consumer products, NDC/UPC/VIN, and cross-source checks.',
      'Use DrugSignal for drugs and medications.',
      'Use Food & Supplement Safety for food, supplements, meat, poultry, and egg products.',
      'Use Personal Care Signals for cosmetics and personal-care products.',
    ],
    disclaimer:
      'This preview is only a routing step and does not make any safety conclusion.',
  }
}

function getIntegrationSources(data: UniversalSearchData): UniversalSourceIdentity[] {
  const sources: UniversalSourceIdentity[] = [
    ...(data.recall?.sources_checked?.map((source) => ({
      sourceId: source.source_id,
      sourceName: source.source_name,
      sourceType: source.source_type,
    })) ?? []),
    ...(data.food?.sources_checked.map((source) => ({
      sourceId: source.source_id,
      sourceName: source.source_name,
      sourceType: source.source_type,
    })) ?? []),
    ...(data.cosmetic?.recall_notices?.map((notice) => ({
      sourceName: notice.source_name,
      sourceType: notice.source_type,
    })) ?? []),
  ]

  const seen = new Set<string>()

  return sources.filter((source) => {
    if (!getSourceIntegrationMode(source)) return false
    const key = `${source.sourceId ?? ''}:${source.sourceName}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function UniversalSafetySearch({ goToPage }: UniversalSafetySearchProps) {
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [submittedRawQuery, setSubmittedRawQuery] = useState('')
  const [searchData, setSearchData] = useState<UniversalSearchData>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [helper, setHelper] = useState('')
  const [notice, setNotice] = useState('')
  const requestIdRef = useRef(0)
  const inFlightKeyRef = useRef('')
  const completedKeyRef = useRef('')

  const classification = useMemo(() => classifySafetyQuery(submittedQuery), [submittedQuery])

  const hasSubmittedQuery = submittedQuery.trim().length > 0
  const primarySuggestion = classification.suggestions[0]
  const preview = hasSubmittedQuery
    ? buildPreview(submittedQuery, classification, searchData)
    : null
  const integrationSources = getIntegrationSources(searchData)

  async function runPreviewSearch(nextQuery: string) {
    const normalization = normalizeSafetyQuery(nextQuery)
    const cleanQuery = normalization.normalizedQuery

    if (!cleanQuery) {
      setError('')
      setNotice('')
      setHelper(
        'Enter a product, drug, food, vehicle, device, brand, identifier, or ingredient to search selected public records.',
      )
      return
    }

    const requestKey = getSearchComparisonKey(cleanQuery)
    if (inFlightKeyRef.current === requestKey) return
    if (completedKeyRef.current === requestKey) {
      setQuery(normalization.rawQuery)
      setSubmittedQuery(cleanQuery)
      setSubmittedRawQuery(normalization.rawQuery)
      setError('')
      setHelper('')
      setNotice('')
      return
    }

    const nextClassification = classifySafetyQuery(cleanQuery)
    const requestId = requestIdRef.current + 1
    requestIdRef.current = requestId
    inFlightKeyRef.current = requestKey
    completedKeyRef.current = ''

    setQuery(normalization.rawQuery)
    setSubmittedQuery(cleanQuery)
    setSubmittedRawQuery(normalization.rawQuery)
    setSearchData({})
    setError('')
    setHelper('')
    setNotice('')
    setLoading(true)

    try {
      let nextSearchData: UniversalSearchData = {}
      let nextNotice = ''

      if (nextClassification.primaryArea === 'pharmacy') {
        const [recallResult, drugResult] = await Promise.allSettled([
          searchRecalls(cleanQuery, 3),
          searchDrugEvents(cleanQuery, 5),
        ])

        if (recallResult.status === 'rejected' && drugResult.status === 'rejected') {
          throw new Error('Both pharmacy preview sources failed.')
        }

        nextSearchData = {
          recall: recallResult.status === 'fulfilled' ? recallResult.value : undefined,
          drug: drugResult.status === 'fulfilled' ? drugResult.value : undefined,
        }

        if (recallResult.status === 'rejected' || drugResult.status === 'rejected') {
          nextNotice =
            'Some public sources were unavailable. Showing the preview that loaded successfully.'
        }
      } else if (nextClassification.primaryArea === 'food') {
        const food = await searchEverydaySafety(cleanQuery, 5)
        nextSearchData = { food }
      } else if (nextClassification.primaryArea === 'cosmetic') {
        const cosmetic = await searchCosmeticEvents(cleanQuery, 5)
        nextSearchData = { cosmetic }
      } else if (nextClassification.primaryArea === 'public_safety') {
        nextSearchData = {}
      }

      if (requestId !== requestIdRef.current) return

      setSearchData(nextSearchData)
      setNotice(nextNotice)
      completedKeyRef.current = requestKey
    } catch {
      if (requestId === requestIdRef.current) {
        setError(
          'Unable to load public records. Check backend/source availability. You can still continue to the detailed workflow.',
        )
      }
    } finally {
      if (requestId === requestIdRef.current) {
        inFlightKeyRef.current = ''
        setLoading(false)
      }
    }
  }

  function handleAnalyze() {
    void runPreviewSearch(query)
  }

  function handleExampleClick(example: string) {
    setQuery(example)
    setError('')
    setHelper('')
    setNotice('')
    void runPreviewSearch(example)
  }

  function openSuggestion(suggestion: SafetyRouteSuggestion) {
    if (
      getSearchComparisonKey(classification.query) !==
      getSearchComparisonKey(submittedRawQuery)
    ) {
      goToPage(suggestion.page, classification.query, submittedRawQuery)
      return
    }

    goToPage(suggestion.page, classification.query)
  }

  return (
    <section className="universal-safety-search" id="universal-safety-search">
      <div className="section-heading">
        <p className="eyebrow">Safety Record Search</p>
        <h2>Safety Record Search.</h2>
        <p>
          Enter a product, vehicle, drug, brand, food, supplement, cosmetic, identifier, or
          ingredient. Dav AI routes to the most relevant public-data workflow first.
        </p>
      </div>

      <div className="search-panel">
        <form
          className="search-box"
          onSubmit={(event) => {
            event.preventDefault()
            handleAnalyze()
          }}
        >
          <div className="search-field">
            <label className="field-label" htmlFor="universal-safety-query">
              Safety search
            </label>

            <QueryTypeahead
              id="universal-safety-query"
              value={query}
              onChange={(nextQuery) => {
                setQuery(nextQuery)
                if (helper) setHelper('')
              }}
              placeholder="Search: air fryer, Advil, NDC 66715 6547, Toyota Camry, sunscreen"
              ariaDescribedBy="universal-safety-helper"
              showWorkflow
            />

            <p className="field-helper" id="universal-safety-helper">
              Public records only. Not medical advice, clinical advice, or a safety guarantee.
            </p>
          </div>

          <button type="submit" disabled={loading}>
            {loading ? 'Checking...' : 'Search records'}
          </button>
        </form>

        <QueryNormalizationNotice
          rawQuery={submittedRawQuery}
          normalizedQuery={submittedQuery}
        />

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

        {helper && (
          <p className="safety-search-guidance" role="status">
            {helper}
          </p>
        )}

        {notice && (
          <p className="safety-search-guidance" role="status">
            {notice}
          </p>
        )}

        {hasSubmittedQuery && preview && !loading && (
          <div className="universal-safety-search__result" aria-live="polite">
            <div>
              <small>{preview.eyebrow}</small>

              <h3>{preview.title}</h3>

              <p>{preview.detail}</p>

              <strong className="universal-safety-search__count">{preview.countLabel}</strong>

              {integrationSources.length > 0 && (
                <div
                  className="universal-safety-search__source-modes"
                  aria-label="Source integration modes"
                >
                  {integrationSources.map((source) => (
                    <span
                      className="universal-safety-search__source-mode"
                      key={`${source.sourceId ?? ''}-${source.sourceName}`}
                    >
                      <span>{source.sourceName}</span>
                      <SourceIntegrationBadge
                        sourceId={source.sourceId}
                        sourceName={source.sourceName}
                        sourceType={source.sourceType}
                      />
                      <SourceDetailsDisclosure
                        sourceId={source.sourceId}
                        sourceName={source.sourceName}
                        sourceType={source.sourceType}
                      />
                    </span>
                  ))}
                </div>
              )}

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
                Open {primarySuggestion.label === 'Public Safety Search'
                  ? 'Safety Record Search'
                  : primarySuggestion.label}
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
