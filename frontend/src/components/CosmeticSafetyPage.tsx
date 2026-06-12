import { useEffect, useState } from 'react'
import { searchCosmeticEvents, type CosmeticEventSearchResponse } from '../api/cosmeticEvents'

type CosmeticSafetyPageProps = {
  initialQuery: string
  goToCosmeticSignal: () => void
}

function CosmeticSafetyPage({ initialQuery, goToCosmeticSignal }: CosmeticSafetyPageProps) {
  const displayQuery = initialQuery || 'your cosmetic or personal-care product'
  const [data, setData] = useState<CosmeticEventSearchResponse | null>(null)
  const [loading, setLoading] = useState(Boolean(initialQuery))
  const [error, setError] = useState('')

  useEffect(() => {
    const cleanQuery = initialQuery.trim()
    if (!cleanQuery) return

    let isMounted = true

    async function loadCosmeticPreview() {
      setLoading(true)
      setError('')

      try {
        const response = await searchCosmeticEvents(cleanQuery, 5)
        if (isMounted) setData(response)
      } catch {
        if (isMounted) {
          setError('Unable to load cosmetic safety records. Make sure the backend is running.')
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    void loadCosmeticPreview()

    return () => {
      isMounted = false
    }
  }, [initialQuery])

  const topReaction = data?.top_reactions[0] ?? null
  const topRecord = data?.records[0] ?? null
  const topProduct = topRecord?.products[0]

  return (
    <section className="safety-area-page safety-area-page--cosmetic">
      <div className="safety-area-dashboard">
        <div className="safety-area-dashboard__copy">
          <p className="eyebrow">Cosmetic Safety</p>
          <h1>Premium review space for cosmetic-event reports.</h1>
          <p>
            A clean personal-care workspace for reviewing cosmetic reports, reactions, product
            context, and public-data limitations.
          </p>

          <div className="safety-area-dashboard__search-pill">
            <span>Current search</span>
            <strong>{displayQuery}</strong>
          </div>

          <div className="safety-area-dashboard__actions">
            <button type="button" onClick={goToCosmeticSignal}>
              Open CosmeticSignal
            </button>
          </div>
        </div>

        <div className="safety-area-visual safety-area-visual--cosmetic" aria-hidden="true">
          <div className="visual-bottle">
            <span />
            <i />
          </div>
          <div className="visual-drop" />
          <div className="visual-sparkle visual-sparkle--one" />
          <div className="visual-sparkle visual-sparkle--two" />
          <div className="visual-sparkle visual-sparkle--three" />
          <div className="visual-caption">Product report signal map</div>
        </div>
      </div>

      {loading && (
        <p className="safety-area-status" role="status" aria-live="polite">
          Checking cosmetic-event public records...
        </p>
      )}

      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}

      {data && (
        <div className="safety-area-metrics">
          <article>
            <small>Public reports</small>
            <strong>{data.count}</strong>
            <span>Cosmetic-event records</span>
          </article>

          <article>
            <small>Top reaction</small>
            <strong>{topReaction?.reaction ?? 'None'}</strong>
            <span>{topReaction ? `${topReaction.count} mentions` : 'No top reaction'}</span>
          </article>

          <article>
            <small>Review signal</small>
            <strong>{data.signal_score.label}</strong>
            <span>Public reporting pattern</span>
          </article>

          <article>
            <small>Confidence</small>
            <strong>{data.signal_score.data_confidence}</strong>
            <span>Context still required</span>
          </article>
        </div>
      )}

      <div className="safety-area-preview-grid">
        <section className="safety-area-preview-card">
          <div>
            <small>Top report preview</small>
            <h2>
              {topProduct?.brand_name ||
                topProduct?.name_brand ||
                topProduct?.industry_name ||
                'No cosmetic report selected yet'}
            </h2>
          </div>

          <dl>
            <div>
              <dt>Report number</dt>
              <dd>{topRecord?.report_number || 'Not listed'}</dd>
            </div>
            <div>
              <dt>Report date</dt>
              <dd>{topRecord?.report_date || 'Not listed'}</dd>
            </div>
            <div>
              <dt>Reported reactions</dt>
              <dd>{topRecord?.reactions.slice(0, 4).join(', ') || 'Not listed'}</dd>
            </div>
          </dl>
        </section>

        <section className="safety-area-preview-card">
          <div>
            <small>Interpretation boundary</small>
            <h2>Reports are signals, not proof.</h2>
          </div>

          <ul className="safety-area-checklist">
            <li>Cosmetic-event reports may be incomplete or duplicated.</li>
            <li>Reported reactions do not prove product causation.</li>
            <li>Review product, report date, and event context carefully.</li>
          </ul>
        </section>
      </div>

      <p className="safety-area-boundary">
        Public reports only. This is not medical advice, diagnosis, causation, or official safety
        guidance.
      </p>
    </section>
  )
}

export default CosmeticSafetyPage