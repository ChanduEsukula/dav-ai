import { useEffect, useRef, useState } from 'react'
import { getDrugEvidence, searchCatalog, type CatalogDrug, type Coverage, type DrugEvidence, type Release } from '../api/drugCatalog'
import { generateReport } from '../api/reports'
import { isOfficialFdaUrl } from '../utils/sourceUrl'

const drugName = (drug: CatalogDrug) => drug.brand_names.join(', ') || drug.generic_name || 'Unnamed medication'
const text = (value: string | null | undefined) => value || 'Not supplied'
const number = (value: number) => value.toLocaleString()

function isOfficialSource(url: string | null) {
  return isOfficialFdaUrl(url)
}

function Source({ url, children = 'Official FDA source' }: { url: string | null; children?: React.ReactNode }) {
  return isOfficialSource(url) ? <a href={url!} target="_blank" rel="noopener noreferrer">{children} ↗</a> : <span>Official source link unavailable</span>
}

function SourceList({ sources }: { sources: Release['sources'] }) {
  const groups = new Map<string, Release['sources']>()
  for (const source of sources) {
    const records = groups.get(source.source_name) || []
    records.push(source)
    groups.set(source.source_name, records)
  }
  return <ul>{[...groups].map(([name, records]) => {
    // Summarize the dataset once; retain each stored record and its own URL/date.
    const primary = records.find(record => isOfficialSource(record.source_url)) || records[0]
    return <li key={name}><span>{name}</span> · Source vintage: {primary.export_date || primary.observed_at || 'Not supplied'} · <Source url={primary.source_url} />
      {records.length > 1 && <details><summary>Stored provenance records ({records.length})</summary>
        <ul>{records.map(record => <li key={record.source_id}>
          Exported: {text(record.export_date)} · Observed: {text(record.observed_at)} · {record.source_url
            ? <Source url={record.source_url}>Stored FDA reference</Source>
            : <span>No URL stored for this provenance record.</span>}
        </li>)}</ul>
      </details>}
    </li>
  })}</ul>
}

function CoverageNote({ coverage }: { coverage: Coverage }) {
  return <aside className="coverage">
    <strong>Coverage: {coverage.state}</strong>
    <p>{coverage.empty_message}</p>
    <p>Source date: {text(coverage.source_date)} · As of: {text(coverage.as_of_date)}</p>
    <details><summary>Coverage details and limitations</summary>
      <p>{coverage.scope} · {coverage.reason_code}</p>
      <ul>{coverage.limitations.map((v, i) => <li key={i}>{v}</li>)}</ul>
    </details>
  </aside>
}

type Remote<T> = { key: string; value?: T; error?: string }
function useRemote<T>(key: string, load: (key: string, signal: AbortSignal) => Promise<T>) {
  const [state, setState] = useState<Remote<T>>({ key: '' })
  useEffect(() => {
    if (!key) return
    const controller = new AbortController()
    load(key, controller.signal).then(value => {
      if (!controller.signal.aborted) setState({ key, value })
    }).catch(() => {
      if (!controller.signal.aborted) setState({ key, error: 'Evidence could not be loaded. The release may be unavailable. Please try again.' })
    })
    return () => controller.abort()
  }, [key, load])
  return { value: state.key === key ? state.value : undefined, error: state.key === key ? state.error : undefined,
    loading: !!key && (state.key !== key || (!state.value && !state.error)) }
}
const loadEvidence = (key: string, signal: AbortSignal) => getDrugEvidence(JSON.parse(key).id, signal)
const loadSearch = (key: string, signal: AbortSignal) => {
  const { q, offset } = JSON.parse(key) as { q: string; offset: number }
  return searchCatalog(q, offset, signal)
}

function ReportDialog({ evidence }: { evidence: DrugEvidence }) {
  const dialog = useRef<HTMLDialogElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const abort = useRef(false)
  useEffect(() => { abort.current = false; return () => { abort.current = true } }, [])
  const title = `Dav AI - ${drugName(evidence.drug)} Evidence Report`
  return <>
    <button className="primary" onClick={() => { setError(''); setSuccess(false); dialog.current?.showModal() }}>Generate PDF Report</button>
    <dialog ref={dialog} aria-labelledby="report-heading" onClose={() => { dialog.current?.querySelector("form")?.reset(); setError(''); setSuccess(false) }} onCancel={event => { if (busy) event.preventDefault() }}>
      <h2 id="report-heading">Generate PDF Report</h2>
      <p>Name and age identify this report only. They are not stored or used to estimate medical risk.</p>
      <form onSubmit={async event => {
        event.preventDefault()
        const form = event.currentTarget
        const fields = new FormData(form)
        const name = String(fields.get('name') || '').trim()
        if (!name) { setError('Enter your name.'); return }
        const age = String(fields.get('age') || '')
        setBusy(true); setError(''); setSuccess(false)
        try {
          const blob = await generateReport(evidence.drug.id, name, age === '' ? undefined : Number(age))
          if (abort.current) return
          const url = URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url; link.download = 'dav-ai-evidence-report.pdf'; link.click()
          setTimeout(() => URL.revokeObjectURL(url), 1000)
          form.reset(); setSuccess(true)
        } catch {
          if (!abort.current) setError('The PDF could not be generated. Check your details, then retry. If the report limit was reached, wait one minute.')
        } finally { if (!abort.current) setBusy(false) }
      }}>
        <label>Name (required)<input name="name" required maxLength={100} autoComplete="off" disabled={busy} /></label>
        <label>Age (optional)<input name="age" type="number" min={0} max={120} step={1} autoComplete="off" disabled={busy} /></label>
        <label>Report title<input value={title} readOnly /></label>
        <label>Selected drug<input value={`${drugName(evidence.drug)} · ${evidence.drug.product_ndcs.join(', ')}`} readOnly /></label>
        {error && <p role="alert">{error}</p>}
        {success && <p role="status">Your PDF download is ready.</p>}
        <div className="actions"><button className="primary" disabled={busy}>{busy ? 'Generating…' : 'Generate and download'}</button>
          <button type="button" disabled={busy} onClick={() => { dialog.current?.close(); dialog.current?.querySelector('form')?.reset(); setError(''); setSuccess(false) }}>Close</button></div>
      </form>
    </dialog>
  </>
}

export default function StoredDrugCatalog() {
  const [location, setLocation] = useState(() => window.location.search)
  const [retry, setRetry] = useState(0)
  const params = new URLSearchParams(location)
  const query = params.get('q') || ''
  const selected = params.get('drug') || ''
  const offset = Math.min(100000, Math.max(0, Number(params.get('offset')) || 0))
  useEffect(() => {
    const pop = () => setLocation(window.location.search)
    window.addEventListener('popstate', pop)
    return () => window.removeEventListener('popstate', pop)
  }, [])
  function navigate(q: string, drug = '', nextOffset = 0) {
    const url = new URL(window.location.href)
    url.search = ''
    if (q) url.searchParams.set('q', q)
    if (drug) url.searchParams.set('drug', drug)
    if (nextOffset) url.searchParams.set('offset', String(nextOffset))
    window.history.pushState(null, '', url)
    setLocation(url.search)
  }
  const searchKey = query ? JSON.stringify({ q: query, offset, retry }) : ''
  const results = useRemote(searchKey, loadSearch)
  const result = useRemote(selected ? JSON.stringify({ id: selected, retry }) : '', loadEvidence)
  const evidence = result.value
  return <main className="explorer" id="main-content">
    <a className="skip-link" href="#search">Skip to drug search</a>
    <header><a className="brand" href="/">Dav AI<span>Pharmaceutical evidence explorer</span></a><span className="badge">FDA source data</span></header>
    <section className="intro" aria-labelledby="title"><p className="eyebrow">Drug recalls · Reported adverse events</p>
      <h1 id="title">Explore the evidence<br />behind your medication.</h1>
      <p>Find an exact product, review linked recall history and explore ingredient-level reporting. Download a personalized evidence report without an account.</p>
      <form className="search" role="search" onSubmit={event => {
        event.preventDefault()
        const q = String(new FormData(event.currentTarget).get('q') || '').trim()
        if (q) navigate(q)
      }}><label htmlFor="search">Brand, generic name, active ingredient or NDC</label>
        <div><input key={query} id="search" name="q" defaultValue={query} placeholder="e.g. Xanax, alprazolam or an NDC" required maxLength={200} /><button className="primary">Search drugs</button></div>
      </form>
    </section>
    {results.loading && <p role="status">Searching the stored drug catalog…</p>}
    {results.error && <p role="alert">{results.error} <button onClick={() => setRetry(v => v + 1)}>Retry search</button></p>}
    {results.value && <section aria-labelledby="selection-heading" className="selection">
      <h2 id="selection-heading">Select an exact product</h2>
      <p>Verify labeler, formulation and NDC. Similar names can refer to different products.</p>
      {!results.value.results.length && <p>No matching products in this stored release. Try another brand, ingredient or identifier.</p>}
      <ul className="products">{results.value.results.map(drug => <li key={drug.id}>
        <button aria-pressed={selected === drug.id} onClick={() => navigate(query, drug.id, offset)}>
          <strong>{drugName(drug)}</strong><span>{text(drug.generic_name)} · {text(drug.strength)} · {text(drug.dosage_form)}</span>
          <span>Labeler: {drug.manufacturers.join(', ') || 'Not supplied'} · NDC: {drug.product_ndcs.join(', ') || 'Not supplied'}</span>
        </button>
      </li>)}</ul>
      <div className="actions">{offset > 0 && <button onClick={() => navigate(query, '', offset - 20)}>Previous products</button>}
        {results.value.results.length === 20 && <button onClick={() => navigate(query, '', offset + 20)}>More products</button>}</div>
    </section>}
    {result.loading && <p role="status">Loading verified product evidence…</p>}
    {result.error && <p role="alert">{result.error} <button onClick={() => setRetry(v => v + 1)}>Retry evidence</button></p>}
    {evidence && <>
      <section className="identity" aria-labelledby="drug-heading">
        <div><p className="eyebrow">Selected medication</p><h2 id="drug-heading">{drugName(evidence.drug)}</h2>
          <p>{text(evidence.drug.generic_name)} · {text(evidence.drug.strength)} · {text(evidence.drug.dosage_form)} · {evidence.drug.routes.join(', ')}</p>
          <p>Active ingredients: {evidence.drug.active_ingredients.join(', ') || 'Not supplied'}</p>
          <p>NDC-listed labeler: {evidence.drug.manufacturers.join(', ') || 'Not supplied'}. Manufacturer not independently verified.</p>
          <p>Product NDC: {evidence.drug.product_ndcs.join(', ') || 'Not supplied'} · Package NDC: {evidence.drug.package_ndcs.join(', ') || 'Not supplied'}</p>
          {evidence.drug.identity_partial && <p>Identity is partial. Verify the exact package and formulation.</p>}
          <Source url={evidence.drug.provenance.source_url} />
        </div><ReportDialog key={evidence.drug.id} evidence={evidence} />
      </section>
      <div className="evidence-panels">
        <section className="panel" aria-labelledby="recall-heading"><p className="eyebrow">Product-linked evidence</p><h2 id="recall-heading">Recall history</h2>
          <CoverageNote coverage={evidence.recalls.coverage} />
          {!evidence.recalls.records.length && <p>No verified linked records in this release. This does not establish that the drug has never been recalled.</p>}
          {evidence.recalls.records.map(recall => <article key={recall.id} className="record">
            <h3>{recall.recall_number}</h3><p>{recall.product_description}</p><p><strong>Reason:</strong> {recall.reason_for_recall}</p>
            <p>Recalling firm: {text(recall.recalling_firm)} (distinct from the product labeler)</p>
            <p>Classification: {text(recall.classification)} · Source-reported status: {text(recall.reported_status)}</p>
            <p>Initiated: {text(recall.recall_initiation_date)} · Reported: {text(recall.report_date)}</p>
            <p>Lots: {text(recall.lot_information)} · Lot scope: {recall.lot_scope}</p>
            <p>Applicability: {recall.applicability_class} · Matched identifier: {text(recall.matched_value)}</p>
            <p>Source record: {recall.source_record_id}</p><Source url={recall.source_url} />
          </article>)}
        </section>
        <section className="panel" aria-labelledby="ae-heading"><p className="eyebrow">Ingredient-level reporting</p><h2 id="ae-heading">Reported adverse events</h2>
          <CoverageNote coverage={evidence.adverse_events.coverage} />
          <p>{evidence.adverse_events.summary.limitation}</p>
          {evidence.adverse_events.records.map(ingredient => <article key={ingredient.ingredient_id} className="record">
            <h3>{ingredient.ingredient_name}</h3><p>Ingredient coverage: {ingredient.coverage.state}</p>
            {ingredient.analytics ? <>
              <div className="counts"><p><strong>{number(ingredient.analytics.report_count)}</strong>ingredient-report associations</p>
                <p><strong>{number(ingredient.analytics.serious_report_count)}</strong>reports marked serious</p></div>
              <p>Reporting period: {ingredient.analytics.window_start} to {ingredient.analytics.window_end}</p>
              <p>Count unit: {ingredient.analytics.count_unit} · Date basis: {ingredient.analytics.date_basis}</p>
              <h4>Top reported reactions</h4><p>Co-report activity counts are not unique patient counts.</p>
              <table><thead><tr><th scope="col">Reaction</th><th scope="col">Co-report activity</th></tr></thead>
                <tbody>{ingredient.top_reported_reactions.map(reaction => <tr key={reaction.rank}><td>{reaction.reaction}</td><td>{number(reaction.co_report_activity)}</td></tr>)}</tbody></table>
              <details><summary>Monthly reporting trends</summary>
                {ingredient.monthly.length ? <table><thead><tr><th scope="col">Month</th><th scope="col">Reports</th><th scope="col">Serious</th></tr></thead>
                  <tbody>{ingredient.monthly.map(month => <tr key={month.period}><td>{month.period.slice(0, 7)}</td><td>{number(month.report_count)}</td><td>{number(month.serious_report_count)}</td></tr>)}</tbody></table> : <p>No monthly data available.</p>}
              </details>
              <ul>{ingredient.analytics.limitations.map((v, i) => <li key={i}>{v}</li>)}</ul>
            </> : <p>No stored analytics available for this ingredient. Missing data is not a zero count.</p>}
          </article>)}
        </section>
      </div>
      <section className="sources" aria-labelledby="source-heading"><h2 id="source-heading">Sources and data freshness</h2>
        <p>Release: {evidence.release.release_id}</p><p>Built: {evidence.release.build_time_utc} · NDC observed: {evidence.release.ndc_observation_date}</p>
        <p>AE reporting window: {evidence.release.window_start} to {evidence.release.window_end}</p>
        <SourceList sources={evidence.release.sources} />
        <ul>{evidence.limitations.map((v, i) => <li key={i}>{v}</li>)}</ul>
      </section>
    </>}
    <footer>Public FDA source evidence. Not medical advice. Reporting counts do not establish causation or individual risk.</footer>
  </main>
}
