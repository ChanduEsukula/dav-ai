import { useEffect, useState, type ReactNode } from 'react'
import {
  getStoredDrug,
  searchCatalog,
  type CatalogDrug,
  type Coverage,
  type IngredientCoverage,
} from '../api/drugCatalog'
import '../styles/stored-drug-catalog.css'
import AskStoredDrug from './AskStoredDrug'
import SemaglutideRelease from './SemaglutideRelease'

const tabs = [
  'OVERVIEW',
  'SAFETY',
  'RECALLS',
  'ADVERSE EVENTS',
  'LABEL',
  'TIMELINE',
  'SOURCES',
] as const

type Tab = typeof tabs[number]

type SourceRecord = {
  source: string
  source_record_id: string
  source_url: string | null
  observed_at?: string | null
}

const stamp = (value: string | null | undefined) =>
  value ? new Date(value).toLocaleString() : 'Not supplied'

const officialSource = (url: string | null) =>
  Boolean(
    url &&
      /^https:\/\/(?:api\.fda\.gov|www\.fda\.gov|fda\.gov|download\.open\.fda\.gov)\//.test(
        url,
      ),
  )

function Source({ record }: { record: SourceRecord }) {
  return (
    <p className="stored-source">
      {record.source} · Source ID: {record.source_record_id}
      <br />
      {record.observed_at && <>Observed: {stamp(record.observed_at)}<br /></>}
      {officialSource(record.source_url) ? (
        <a
          href={record.source_url || undefined}
          target="_blank"
          rel="noopener noreferrer"
        >
          Open official source
        </a>
      ) : (
        'Official source link unavailable'
      )}
    </p>
  )
}

function CoverageNote({ coverage }: { coverage: Coverage }) {
  return (
    <div className="stored-coverage">
      <p>
        <strong>Coverage state: {coverage.state}</strong> ·{' '}
        {coverage.reason_code}
      </p>

      <p>Scope: {coverage.scope}</p>

      {coverage.measured_count !== null &&
        coverage.measured_count !== undefined && (
          <p>Measured count in release: {coverage.measured_count}</p>
        )}

      <p>
        As of: {coverage.as_of_date || 'Not supplied'} · Source date:{' '}
        {coverage.source_date || 'Not supplied'}
      </p>

      {coverage.limitations.length > 0 && (
        <details>
          <summary>Coverage limitations</summary>
          <ul>
            {coverage.limitations.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}

function IngredientCoverageNote({
  coverage,
}: {
  coverage: IngredientCoverage
}) {
  return (
    <div className="stored-coverage">
      <p>
        <strong>Ingredient coverage: {coverage.state}</strong> ·{' '}
        {coverage.reason_code}
      </p>

      <p>Scope: {coverage.scope}</p>

      <p>
        As of: {coverage.as_of_date || 'Not supplied'} · Source date:{' '}
        {coverage.source_date || 'Not supplied'}
      </p>

      {coverage.limitations.length > 0 && (
        <details>
          <summary>Ingredient analytics limitations</summary>
          <ul>
            {coverage.limitations.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}

function Records<T extends SourceRecord & { id: string }>({
  section,
  children,
}: {
  section: { records: T[]; coverage: Coverage }
  children: (record: T) => ReactNode
}) {
  return (
    <>
      <CoverageNote coverage={section.coverage} />

      {section.records.length === 0 ? (
        <p>{section.coverage.empty_message}</p>
      ) : (
        section.records.map(record => (
          <article className="stored-record" key={record.id}>
            {children(record)}
            <Source record={record} />
          </article>
        ))
      )}
    </>
  )
}

const labelFields = [
  'boxed_warning',
  'warnings_and_precautions',
  'warnings',
  'contraindications',
  'adverse_reactions',
  'drug_interactions',
] as const

export default function StoredDrugCatalog({
  initialQuery,
}: {
  initialQuery: string
}) {
  return <Catalog key={initialQuery} initialQuery={initialQuery} />
}

function Catalog({ initialQuery }: { initialQuery: string }) {
  const [query, setQuery] = useState(initialQuery)
  const [submitted, setSubmitted] = useState(initialQuery)
  const [offset, setOffset] = useState(0)
  const [searchAttempt, setSearchAttempt] = useState(0)
  const [detailAttempt, setDetailAttempt] = useState(0)
  const [results, setResults] = useState<CatalogDrug[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] =
    useState<Awaited<ReturnType<typeof getStoredDrug>> | null>(null)
  const [tab, setTab] = useState<Tab>('OVERVIEW')
  const [loading, setLoading] = useState(Boolean(initialQuery.trim()))
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState('')
  const [detailError, setDetailError] = useState('')

  const releaseQuery = submitted.trim().toLowerCase() === 'semaglutide'

  useEffect(() => {
    if (!submitted.trim()) return

    if (releaseQuery) {
      setResults([])
      setError('')
      setLoading(false)
      return
    }

    const controller = new AbortController()

    searchCatalog(submitted, offset, controller.signal)
      .then(data => {
        setResults(data.results)
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setError(
            'Frozen pharmaceutical release unavailable. No live FDA fallback was used.',
          )
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [submitted, offset, searchAttempt, releaseQuery])

  useEffect(() => {
    if (!selected) return

    const controller = new AbortController()

    getStoredDrug(selected, controller.signal)
      .then(setDetail)
      .catch(() => {
        if (!controller.signal.aborted) {
          setDetailError(
            'Unable to load frozen drug safety information. Please try again.',
          )
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setDetailLoading(false)
      })

    return () => controller.abort()
  }, [selected, detailAttempt])

  function changePage(nextOffset: number) {
    setLoading(true)
    setError('')
    setResults([])
    setOffset(nextOffset)
  }

  function openDrug(id: string) {
    setDetailLoading(true)
    setDetail(null)
    setDetailError('')
    setSelected(id)
    setDetailAttempt(value => value + 1)
    setTab('OVERVIEW')
  }

  return (
    <section className="stored-catalog">
      <header>
        <p>PHARMACEUTICAL CATALOG</p>
        <h1>Search pharmacy safety records</h1>
        <p>
          Search the frozen Dav AI pharmaceutical release by generic name,
          brand, NDC, or RxCUI. Coverage varies by evidence domain.
        </p>
      </header>

      <form
        onSubmit={event => {
          event.preventDefault()
          setLoading(true)
          setError('')
          setSubmitted(query.trim())
          setOffset(0)
          setSelected(null)
          setDetail(null)
          setResults([])
          setSearchAttempt(value => value + 1)
        }}
      >
        <label htmlFor="stored-drug-query">
          Search stored pharmaceutical catalog
        </label>

        <div className="stored-search">
          <input
            id="stored-drug-query"
            value={query}
            onChange={e => setQuery(e.target.value)}
            maxLength={200}
            required
          />
          <button type="submit" disabled={!query.trim() || loading}>
            Search stored data
          </button>
        </div>
      </form>

      {error && <p role="alert">{error}</p>}
      {loading && <p role="status">Searching stored records…</p>}

      {!loading &&
        !error &&
        submitted &&
        !releaseQuery &&
        results.length === 0 && (
          <p>
            No products in this frozen Dav AI release match the query. This is
            not a statement about FDA coverage or product availability.
          </p>
        )}

      {!loading && !error && releaseQuery && <SemaglutideRelease />}

      {results.length > 0 && (
        <details open={!selected}>
          <summary>
            {results.length} matching products on this page — choose a
            formulation
          </summary>

          <ul className="stored-results">
            {results.map(drug => (
              <li key={drug.id}>
                <button type="button" onClick={() => openDrug(drug.id)}>
                  <strong>{drug.generic_name || 'Generic name not supplied'}</strong>{' '}
                  — {drug.brand_names.join(', ') || 'No brand supplied'}
                  <br />
                  {drug.strength || 'Strength not supplied'} ·{' '}
                  {drug.dosage_form || 'Dosage form not supplied'} ·{' '}
                  {drug.manufacturers.join(', ') || 'Labeler not supplied'} ·
                  NDC {drug.product_ndcs.join(', ') || 'not supplied'}
                </button>
              </li>
            ))}
          </ul>

          {submitted && !loading && (
            <div className="stored-paging">
              <button
                disabled={offset === 0}
                onClick={() => changePage(Math.max(0, offset - 20))}
              >
                Previous results
              </button>
              <button
                disabled={results.length < 20}
                onClick={() => changePage(offset + 20)}
              >
                Next results
              </button>
            </div>
          )}
        </details>
      )}

      {detailLoading && (
        <p role="status">Loading stored safety information…</p>
      )}

      {detailError && (
        <div role="alert">
          {detailError}{' '}
          <button onClick={() => selected && openDrug(selected)}>
            Retry details
          </button>
        </div>
      )}

      {detail && (
        <div className="stored-detail">
          <h2>{detail.drug.generic_name || 'Drug product'}</h2>

          <p>
            Public-source information, not medical advice. Dav AI does not
            calculate a safety score or rank drugs by safety.
          </p>

          <div role="tablist" aria-label="Drug information">
            {tabs.map(t => (
              <button
                key={t}
                id={`stored-tab-${t.replaceAll(' ', '-')}`}
                role="tab"
                aria-selected={tab === t}
                aria-controls="stored-panel"
                onClick={() => setTab(t)}
              >
                {t}
              </button>
            ))}
          </div>

          <div
            role="tabpanel"
            id="stored-panel"
            aria-labelledby={`stored-tab-${tab.replaceAll(' ', '-')}`}
          >
            {tab === 'OVERVIEW' && (
              <>
                <h3>Drug overview</h3>

                <dl>
                  {[
                    ['Generic name', detail.drug.generic_name],
                    ['Brands', detail.drug.brand_names.join(', ')],
                    ['Ingredients', detail.drug.active_ingredients.join(', ')],
                    ['Strength', detail.drug.strength],
                    ['Dosage form', detail.drug.dosage_form],
                    ['Routes', detail.drug.routes.join(', ')],
                    [
                      'Manufacturers / labelers',
                      detail.drug.manufacturers.join(', '),
                    ],
                    ['Product NDCs', detail.drug.product_ndcs.join(', ')],
                    ['Package NDCs', detail.drug.package_ndcs.join(', ')],
                    [
                      'Associated RxCUIs',
                      detail.drug.rxcuis.length
                        ? `${detail.drug.rxcuis.length} associated`
                        : null,
                    ],
                    [
                      'Combination product',
                      detail.drug.is_combination ? 'Yes' : 'No',
                    ],
                    [
                      'Identity partial',
                      detail.drug.identity_partial ? 'Yes' : 'No',
                    ],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <dt>{label}</dt>
                      <dd>{value || 'Not supplied'}</dd>
                    </div>
                  ))}
                </dl>

                {detail.drug.rxcuis.length > 0 && (
                  <details>
                    <summary>
                      Associated RxCUIs — not treated as one canonical product
                      identifier
                    </summary>
                    <ul>
                      {detail.drug.rxcuis.map(item => (
                        <li key={item.value}>
                          {item.value} · concept type{' '}
                          {item.concept_type || 'unknown'} ·{' '}
                          {item.has_conflict
                            ? 'conflicted / non-unique mapping'
                            : item.is_unique_product
                              ? 'unique product mapping'
                              : 'not established as unique'}
                        </li>
                      ))}
                    </ul>
                  </details>
                )}

                <Source record={detail.drug.provenance} />
              </>
            )}

            {tab === 'SAFETY' && (
              <>
                <h3>FDA safety communications</h3>
                <p>
                  Communications shown here are ingredient-level context only.
                  A link does not establish applicability to every product,
                  formulation, strength, dose, or indication.
                </p>

                <Records section={detail.safety.communications}>
                  {record => (
                    <>
                      <h4>{record.title || 'Title not supplied'}</h4>
                      <p>
                        Ingredient: {record.ingredient_name} · Published:{' '}
                        {record.published_date || 'Not supplied'}
                      </p>
                      <p>{record.scope_qualifiers}</p>
                      <details>
                        <summary>Read stored official text</summary>
                        <p className="stored-text">{record.body_text}</p>
                      </details>
                    </>
                  )}
                </Records>
              </>
            )}

            {tab === 'RECALLS' && (
              <>
                <h3>Verified linked recalls</h3>
                <p>
                  Recall status is source-reported. Recall discovery and
                  linkage coverage are partial, so an empty result is not proof
                  that no historical recall exists.
                </p>

                <Records section={detail.safety.recalls}>
                  {record => (
                    <>
                      <h4>{record.product_description}</h4>
                      <p>
                        {record.recall_initiation_date ||
                          'Date not supplied'}{' '}
                        · {record.classification || 'Unclassified'}
                      </p>
                      <p>{record.reason_for_recall}</p>
                      <p>
                        Lots: {record.lot_information || 'Not supplied'} · Lot
                        scope: {record.lot_scope}
                      </p>
                      <p>
                        Distribution:{' '}
                        {record.distribution_pattern || 'Not supplied'}
                      </p>
                      <p>
                        Reported status:{' '}
                        {record.reported_status || 'Not supplied'} · Recalling
                        firm: {record.recalling_firm || 'Not supplied'}
                      </p>
                    </>
                  )}
                </Records>
              </>
            )}

            {tab === 'ADVERSE EVENTS' && (
              <>
                <h3>Ingredient-level adverse-event analytics</h3>

                <p>{detail.safety.adverse_events.summary.limitation}</p>

                <CoverageNote
                  coverage={detail.safety.adverse_events.coverage}
                />

                <p>
                  Ingredient components:{' '}
                  {detail.safety.adverse_events.summary.ingredient_count} ·
                  Analytics available:{' '}
                  {
                    detail.safety.adverse_events.summary
                      .ingredients_with_analytics
                  }{' '}
                  · Unavailable:{' '}
                  {
                    detail.safety.adverse_events.summary
                      .ingredients_without_analytics
                  }
                </p>

                {detail.safety.adverse_events.records.map(record => (
                  <article
                    className="stored-record"
                    key={record.ingredient_id}
                  >
                    <h4>{record.ingredient_name}</h4>

                    <p>
                      Scope: ingredient-level FAERS-derived co-reporting
                      analytics
                    </p>

                    <IngredientCoverageNote coverage={record.coverage} />

                    {!record.analytics ? (
                      <p>
                        Ingredient analytics are unavailable in this frozen
                        release. This is not an observed zero and does not mean
                        no reports exist.
                      </p>
                    ) : (
                      <>
                        <p>
                          Window: {record.analytics.window_start} through{' '}
                          {record.analytics.window_end}
                        </p>

                        <p>
                          {record.analytics.report_count} deduplicated
                          ingredient-report associations ·{' '}
                          {record.analytics.serious_report_count} marked
                          serious · {record.analytics.death_report_count} with
                          a death outcome flag ·{' '}
                          {record.analytics.hospitalization_report_count} with
                          a hospitalization outcome flag
                        </p>

                        <p>
                          Reaction co-report activity:{' '}
                          {record.analytics.co_report_activity}. This is
                          distinct from report count.
                        </p>

                        {record.top_reported_reactions.length > 0 && (
                          <>
                            <h5>Top co-reported reaction terms</h5>
                            <ul>
                              {record.top_reported_reactions.map(reaction => (
                                <li key={reaction.reaction}>
                                  {reaction.reaction}: {' '}
                                  {reaction.co_report_activity} co-report
                                  activity · {reaction.active_months} active
                                  months
                                </li>
                              ))}
                            </ul>
                          </>
                        )}
                      </>
                    )}
                  </article>
                ))}
              </>
            )}

            {tab === 'LABEL' && (
              <>
                <h3>Latest verified product-scoped label</h3>

                <Records
                  section={{
                    ...detail.safety.labels,
                    records: detail.safety.labels.latest_records || [],
                  }}
                >
                  {record => (
                    <>
                      <h4>FDA label {record.label_set_id}</h4>
                      <p>
                        Effective: {record.effective_date || 'Not supplied'} ·
                        Version: {record.label_version || 'Not supplied'} ·
                        Applicability: {record.applicability_class}
                      </p>

                      {labelFields.map(field => {
                        const state = record.section_states[field]
                        const text = record[field]

                        return (
                          <details key={field}>
                            <summary>{field.replaceAll('_', ' ')}</summary>

                            {text ? (
                              <p className="stored-text">{text}</p>
                            ) : (
                              <p>
                                No structured text is stored for this field.
                                {state
                                  ? ` State: ${state.state}; reason: ${state.reason_code}.`
                                  : ''}{' '}
                                This is not a clinical absence conclusion.
                              </p>
                            )}
                          </details>
                        )
                      })}
                    </>
                  )}
                </Records>
              </>
            )}

            {tab === 'TIMELINE' && (
              <>
                <h3>Stored safety timeline</h3>

                <p>
                  Only dated evidence from the frozen release appears here.
                  Missing entries do not establish absence. Ingredient-level
                  adverse-event monthly activity is not presented as an
                  individual clinical event.
                </p>

                <details>
                  <summary>Timeline source coverage</summary>
                  {(
                    [
                      'labels',
                      'recalls',
                      'adverse_events',
                      'communications',
                    ] as const
                  ).map(kind => (
                    <CoverageNote
                      key={kind}
                      coverage={detail.safety[kind].coverage}
                    />
                  ))}
                </details>

                {detail.timeline.length === 0 && (
                  <p>No dated linked evidence is stored in this release.</p>
                )}

                <ol>
                  {detail.timeline.map(event => (
                    <li key={`${event.event_type}-${event.record_id}`}>
                      <strong>
                        {event.date} · {event.title || 'Title not supplied'}
                      </strong>

                      <p>
                        {event.date_type.replaceAll('_', ' ')} ·{' '}
                        {event.summary}
                      </p>

                      <p>Source: {event.source}</p>

                      {officialSource(event.source_url) && (
                        <a
                          href={event.source_url || undefined}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Open official source
                        </a>
                      )}
                    </li>
                  ))}
                </ol>
              </>
            )}

            {tab === 'SOURCES' && (
              <>
                <h3>Sources and frozen-release coverage</h3>

                <Source record={detail.drug.provenance} />

                {(
                  [
                    'labels',
                    'recalls',
                    'adverse_events',
                    'communications',
                  ] as const
                ).map(kind => (
                  <section key={kind}>
                    <h4>{kind.replaceAll('_', ' ')}</h4>
                    <CoverageNote
                      coverage={detail.safety[kind].coverage}
                    />
                  </section>
                ))}
              </>
            )}
          </div>

          <AskStoredDrug
            key={detail.drug.id}
            drugId={detail.drug.id}
          />
        </div>
      )}
    </section>
  )
}
