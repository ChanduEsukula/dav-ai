import { useEffect, useState } from 'react'
import { searchEverydaySafety, type EverydaySafetySearchResponse } from '../api/everydaySafety'
import type { ActivePage } from '../types/navigation'
import {
  getTypoSuggestion,
  getWrongCategorySuggestion,
  normalizeSearchTerm,
} from '../utils/safetyRouteClassifier'

type FoodSafetyPageProps = {
  initialQuery: string
  goToFoodRadar: () => void
  goToPage: (page: ActivePage, query?: string) => void
}

function FoodSafetyPage({ initialQuery, goToFoodRadar, goToPage }: FoodSafetyPageProps) {
  const normalizedQuery = normalizeSearchTerm(initialQuery)
  const displayQuery = normalizedQuery || 'your food, supplement, ingredient, or brand'
  const [data, setData] = useState<EverydaySafetySearchResponse | null>(null)
  const [loading, setLoading] = useState(Boolean(normalizedQuery))
  const [error, setError] = useState('')

  useEffect(() => {
    const cleanQuery = normalizeSearchTerm(initialQuery)
    let isMounted = true

    async function loadFoodPreview() {
      if (!cleanQuery) {
        await Promise.resolve()
        if (!isMounted) return

        setData(null)
        setLoading(false)
        setError('')
        return
      }

      setData(null)
      setLoading(true)
      setError('')

      try {
        const response = await searchEverydaySafety(cleanQuery, 5)
        if (isMounted) setData(response)
      } catch {
        if (isMounted) {
          setError('Unable to load public records. Check backend/source availability.')
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    void loadFoodPreview()

    return () => {
      isMounted = false
    }
  }, [initialQuery])

  const topResult = data?.results[0] ?? null
  const wrongCategorySuggestion = getWrongCategorySuggestion('food', normalizedQuery)
  const typoSuggestion = data?.count === 0 ? getTypoSuggestion(normalizedQuery) : null

  return (
    <section className="safety-area-page safety-area-page--food">
      <div className="safety-area-dashboard">
        <div className="safety-area-dashboard__copy">
          <p className="eyebrow">Food & Supplement Safety</p>
          <h1>Fast product checks for food and supplement records.</h1>
          <p>
            A fresh, consumer-friendly workspace for reviewing public food, supplement, meat,
            poultry, and egg-product safety records.
          </p>

          <div className="safety-area-dashboard__search-pill">
            <span>Current search</span>
            <strong>{displayQuery}</strong>
          </div>

          <div className="safety-area-dashboard__actions">
            <button type="button" onClick={goToFoodRadar}>
              Open FoodRadar
            </button>
          </div>
        </div>

        <div className="safety-area-visual safety-area-visual--food" aria-hidden="true">
          <div className="visual-package">
            <span />
            <i />
          </div>
          <div className="visual-leaf visual-leaf--one" />
          <div className="visual-leaf visual-leaf--two" />
          <div className="visual-timeline">
            <b />
            <b />
            <b />
          </div>
          <div className="visual-caption">Product → firm → recall detail</div>
        </div>
      </div>

      {loading && (
        <p className="safety-area-status" role="status" aria-live="polite">
          Checking food and supplement public records...
        </p>
      )}

      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}

      {wrongCategorySuggestion && !loading && (
        <aside className="safety-route-suggestion" aria-live="polite">
          <span>{wrongCategorySuggestion.message}</span>
          <button
            type="button"
            onClick={() => goToPage(wrongCategorySuggestion.page, normalizedQuery)}
          >
            Open {wrongCategorySuggestion.label}
          </button>
        </aside>
      )}

      {data?.count === 0 && !loading && (
        <aside className="safety-search-guidance" aria-live="polite">
          <span>
            No public records returned for this exact search. Check spelling or try a
            simpler/generic term.
          </span>
          {typoSuggestion && (
            <button
              type="button"
              onClick={() => goToPage('food-safety', typoSuggestion)}
            >
              Did you mean {typoSuggestion}?
            </button>
          )}
        </aside>
      )}

      {data && (
        <div className="safety-area-metrics">
          <article>
            <small>Possible matches</small>
            <strong>{data.count}</strong>
            <span>Public records returned</span>
          </article>

          <article>
            <small>Sources checked</small>
            <strong>{data.sources_checked.length}</strong>
            <span>FDA / USDA-style coverage</span>
          </article>

          <article>
            <small>Review focus</small>
            <strong>{topResult?.risk_score.label ?? 'Verify'}</strong>
            <span>Use exact product details</span>
          </article>

          <article>
            <small>Search strategy</small>
            <strong>{data.search_strategy_used}</strong>
            <span>Backend matched query path</span>
          </article>
        </div>
      )}

      <div className="safety-area-preview-grid">
        <section className="safety-area-preview-card">
          <div>
            <small>Top record preview</small>
            <h2>{topResult?.product_description || 'No food record selected yet'}</h2>
          </div>

          <dl>
            <div>
              <dt>Firm</dt>
              <dd>{topResult?.recalling_firm || 'Not listed'}</dd>
            </div>
            <div>
              <dt>Reason</dt>
              <dd>{topResult?.reason_for_recall || 'Not listed'}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{topResult?.status || 'Not listed'}</dd>
            </div>
          </dl>
        </section>

        <section className="safety-area-preview-card">
          <div>
            <small>Verification checklist</small>
            <h2>Compare your item before acting.</h2>
          </div>

          <ul className="safety-area-checklist">
            <li>Match brand, product name, package size, and lot/code details.</li>
            <li>Review firm, date, recall reason, and distribution pattern.</li>
            <li>No result does not prove a food or supplement is safe.</li>
          </ul>
        </section>
      </div>

      <p className="safety-area-boundary">
        Public records only. This is not official recall instruction or a safety guarantee.
      </p>
    </section>
  )
}

export default FoodSafetyPage
