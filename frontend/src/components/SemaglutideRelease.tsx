import { useEffect, useState } from 'react'
import {
  getSemaglutideRelease,
  type SemaglutideRelease as SemaglutideReleaseData,
} from '../api/drugCatalog'

const tabs = [
  'OVERVIEW',
  'CO-REPORTING ACTIVITY',
  'LABELS',
  'RECALLS / COVERAGE',
  'SOURCES',
] as const

type Tab = typeof tabs[number]

export default function SemaglutideRelease() {
  const [data, setData] = useState<SemaglutideReleaseData | null>(null)
  const [tab, setTab] = useState<Tab>('OVERVIEW')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const controller = new AbortController()

    getSemaglutideRelease(controller.signal)
      .then(setData)
      .catch(() => {
        if (!controller.signal.aborted) {
          setError('Unable to load the Semaglutide release snapshot.')
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      })

    return () => controller.abort()
  }, [])

  if (loading) {
    return <p role="status">Loading Semaglutide safety snapshot…</p>
  }

  if (error || !data) {
    return <p role="alert">{error || 'Semaglutide snapshot unavailable.'}</p>
  }

  return (
    <section className="stored-detail">
      <h2>{data.drug.display_name}</h2>

      <p>
        Public-source pharmaceutical safety intelligence. Not medical advice.
        Co-reporting activity does not establish causality, incidence, or patient risk.
      </p>

      <div role="tablist" aria-label="Semaglutide release information">
        {tabs.map((item) => (
          <button
            key={item}
            role="tab"
            aria-selected={tab === item}
            onClick={() => setTab(item)}
          >
            {item}
          </button>
        ))}
      </div>

      <div role="tabpanel">
        {tab === 'OVERVIEW' && (
          <>
            <h3>Drug overview</h3>

            <dl>
              <div>
                <dt>Canonical ingredient</dt>
                <dd>{data.drug.canonical_name}</dd>
              </div>

              <div>
                <dt>Identity status</dt>
                <dd>{data.drug.identity_status}</dd>
              </div>

              <div>
                <dt>Mapping confidence</dt>
                <dd>{data.drug.mapping_confidence}</dd>
              </div>

              <div>
                <dt>Ingredient ID</dt>
                <dd>{data.drug.ingredient_id}</dd>
              </div>

              <div>
                <dt>Source-associated products</dt>
                <dd>{data.drug.source_product_count}</dd>
              </div>

              <div>
                <dt>Product NDCs</dt>
                <dd>{data.drug.product_ndc_count}</dd>
              </div>

              <div>
                <dt>Associated RxCUIs</dt>
                <dd>{data.drug.associated_rxcui_count}</dd>
              </div>

              <div>
                <dt>Combination concept</dt>
                <dd>{data.drug.is_combination ? 'Yes' : 'No'}</dd>
              </div>
            </dl>
          </>
        )}

        {tab === 'CO-REPORTING ACTIVITY' && (
          <>
            <h3>2020+ co-reporting activity</h3>

            <p>{data.analytics.interpretation}</p>

            <p>
              {data.analytics.start_month} to {data.analytics.end_month}
              {' · '}
              {data.analytics.months} months
              {' · '}
              {data.analytics.distinct_reaction_terms.toLocaleString()} reaction terms
              {' · '}
              {data.analytics.pair_report_activity.toLocaleString()} pair-report activity
            </p>

            <h4>Top reported reaction terms</h4>

            <ol>
              {data.analytics.top_reactions.map((item) => (
                <li key={item.reaction}>
                  <strong>{item.reaction}</strong>
                  {' — '}
                  {item.pair_report_activity.toLocaleString()} pair-report activity
                  {' · '}
                  {item.active_months} active months
                </li>
              ))}
            </ol>

            <details>
              <summary>Monthly co-reporting activity</summary>

              <table>
                <thead>
                  <tr>
                    <th>Month</th>
                    <th>Pair-report activity</th>
                    <th>Active reaction terms</th>
                  </tr>
                </thead>

                <tbody>
                  {data.analytics.monthly.map((item) => (
                    <tr key={item.period}>
                      <td>{item.period}</td>
                      <td>{item.pair_report_activity.toLocaleString()}</td>
                      <td>{item.active_reaction_terms.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          </>
        )}

        {tab === 'LABELS' && (
          <>
            <h3>Verified product-specific FDA labels</h3>

            <p>{data.regulatory_evidence.note}</p>

            {data.regulatory_evidence.labels.map((label) => (
              <article className="stored-record" key={label.label_id}>
                <h4>
                  {label.brand_name || 'Brand not supplied'}
                  {' · '}
                  NDC {label.product_ndcs.join(', ')}
                </h4>

                <p>
                  Label date: {label.label_date || 'Not supplied'}
                  {' · '}
                  Scope: {label.scope}
                  {' · '}
                  Classification: {label.classification}
                </p>

                <p>{label.basis}</p>

                {Object.entries(label.sections).map(([name, section]) => (
                  <details key={name}>
                    <summary>{name.replaceAll('_', ' ')}</summary>
                    <p className="stored-text">{section?.text_excerpt}</p>
                    {section?.truncated && (
                      <p>
                        Stored release excerpt is truncated; consult the full official label
                        for complete context.
                      </p>
                    )}
                  </details>
                ))}
              </article>
            ))}
          </>
        )}

        {tab === 'RECALLS / COVERAGE' && (
          <>
            <h3>Recall coverage</h3>

            <p>
              Coverage status: <strong>{data.recalls.coverage_status}</strong>
            </p>

            <p>{data.recalls.note}</p>

            <h4>Release coverage</h4>

            <dl>
              {Object.entries(data.coverage).map(([key, value]) => (
                <div key={key}>
                  <dt>{key.replaceAll('_', ' ')}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>

            <h4>Limitations</h4>

            <ul>
              {data.limitations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </>
        )}

        {tab === 'SOURCES' && (
          <>
            <h3>Release provenance</h3>

            <p>
              These are the local source artifacts used to build this deterministic release
              snapshot.
            </p>

            <dl>
              <div>
                <dt>Cohort</dt>
                <dd>{data.sources.cohort}</dd>
              </div>

              <div>
                <dt>Analytics</dt>
                <dd>{data.sources.analytics}</dd>
              </div>

              <div>
                <dt>Regulatory audit</dt>
                <dd>{data.sources.regulatory_audit}</dd>
              </div>

              <div>
                <dt>Label bulk cache</dt>
                <dd>{data.sources.label_bulk_cache}</dd>
              </div>

              <div>
                <dt>Schema version</dt>
                <dd>{data.schema_version}</dd>
              </div>

              <div>
                <dt>Artifact version</dt>
                <dd>{data.artifact_version}</dd>
              </div>
            </dl>
          </>
        )}
      </div>
    </section>
  )
}
