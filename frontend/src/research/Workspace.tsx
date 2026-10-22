import { useEffect, useRef, useState } from 'react'
import type { Candidate, PublicBriefing } from './contracts'
import { researchApi } from './client'
import type { Session } from './client'
import { Briefing } from './Evidence'
import './workspace.css'

const categories = { labels: 'Drug labeling', recalls: 'Historical recalls', faers: 'FAERS reporting evidence' }
const modelNames: Record<string, string> = { 'llama3.2:3b': 'Llama 3.2 3B', 'qwen3.5:4b-q4_K_M': 'Qwen 3.5 4B' }
const messages: Record<string, string> = {
  session_expired: 'This session expired. Start a new session and confirm the product again.',
  session_forbidden: 'This session is invalid. Start a new session.',
  api_unavailable: 'The local API is unavailable. Start the loopback research server and retry.',
  timeout: 'The request timed out. Cancel or start a new session before retrying.',
  model_unavailable: 'The selected model is unavailable. Start a new session to use deterministic execution.',
  research_busy: 'The local research server is busy. Retry when the active operation finishes.',
  pairing_forbidden: 'The pairing capability is invalid. Copy the current capability from the local launcher.',
  product_binding_changed: 'The stored product binding changed. Start a new session; this result cannot be used.',
  unknown_product_reference: 'This selection is invalid or stale. Search again and explicitly confirm a candidate.',
  cancelled: 'Research cancelled. Start a new session to continue.',
}
function Product({ value }: { value: Candidate }) {
  return <><strong>{value.brand_names.join(', ') || value.generic_name}</strong><span>{value.strength ?? 'Strength unavailable'} · {value.dosage_form ?? 'Form unavailable'} · {value.routes.join(', ')}</span><span>Product NDC: {value.product_ndcs.join(', ')}</span><span>Packages: {value.package_ndcs.join(', ') || 'unavailable'}</span><span>Ingredients: {value.active_ingredients.join(', ')}</span></>
}
export default function Workspace() {
  const [pairing, setPairing] = useState('')
  const [session, setSession] = useState<Session | null>(null)
  const owned = useRef<Session | null>(null)
  const [query, setQuery] = useState('')
  const [candidates, setCandidates] = useState<Candidate[] | null>(null)
  const [incomplete, setIncomplete] = useState(false)
  const [choice, setChoice] = useState('')
  const [product, setProduct] = useState<Candidate | null>(null)
  const [question, setQuestion] = useState('What historical recalls, drug-label warnings, and adverse-event reports are available for this medication?')
  const [selected, setSelected] = useState<string[]>(Object.keys(categories))
  const [model, setModel] = useState('')
  const [busy, setBusy] = useState('')
  const [running, setRunning] = useState(false)
  const [attempted, setAttempted] = useState(false)
  const [result, setResult] = useState<PublicBriefing | null>(null)
  const [error, setError] = useState('')
  const gate = useRef(false)
  const generation = useRef(0)
  const showError = (error: unknown) => {
    const code = error instanceof Error ? error.message : 'api_unavailable'
    setError(messages[code] ?? `Research stopped (${code.replaceAll('_', ' ')}). Start a new session if needed.`)
  }
  async function action(label: string, fn: () => Promise<void>) {
    if (gate.current) return
    gate.current = true; setBusy(label); setError('')
    try { await fn() } catch (error) { showError(error) }
    finally { gate.current = false; setBusy('') }
  }
  useEffect(() => () => {
    generation.current++
    if (owned.current) void researchApi.close(owned.current).catch(() => {})
  }, [])
  useEffect(() => {
    if (!running || !session) return
    let stopped = false
    let timer: ReturnType<typeof setTimeout>
    const current = generation.current
    const poll = async () => {
      try {
        const outcome = await researchApi.result(session)
        if (stopped || current !== generation.current) return
        if (outcome.state === 'running') timer = setTimeout(() => { void poll() }, 750)
        else {
          setRunning(false)
          if (outcome.briefing) setResult(outcome.briefing)
          else showError(new Error(outcome.code ?? 'research_stopped'))
        }
      } catch (error) { if (!stopped) { setRunning(false); showError(error) } }
    }
    timer = setTimeout(() => { void poll() }, 300)
    return () => { stopped = true; clearTimeout(timer) }
  }, [running, session])
  async function connect() {
    const next = await researchApi.create(pairing.trim())
    owned.current = next; setSession(next); setPairing(''); setModel('')
  }
  async function reset() {
    generation.current++
    if (session) await researchApi.close(session).catch(() => {})
    owned.current = null; setSession(null); setProduct(null); setCandidates(null); setChoice('')
    setResult(null); setRunning(false); setAttempted(false); setError('')
  }
  return <main className="research-workspace"><header className="research-header"><a className="brand" href="/">Dav AI<span>Evidence research workspace</span></a><span className="local-indicator">Local research · Frozen evidence snapshot</span></header>
    <section className="research-intro"><p className="eyebrow">Human confirmation. Verified sources.</p><h1>Ask Dav AI</h1><p>Explore pharmaceutical evidence with verified sources and transparent limitations.</p><p className="research-subtle">Choose an exact product. Define your evidence scope. Inspect what the frozen release supports.</p></section>
    {error && <div role="alert">{error}</div>}{busy && <p role="status">{busy}</p>}
    {!session ? <section className="panel research-connect"><div><p className="eyebrow">Local connection</p><h2>Connect to your research session</h2><p>The local launcher issues a pairing capability. It is used once to create this session and stays out of browser storage.</p><details><summary>Start the local demonstration</summary><p>From the repository root:</p><code>PYTHONPATH=backend .venv/bin/python -m app.local_research</code><p>Paste the capability printed in your terminal. Only approved loopback development origins are accepted.</p></details></div><form onSubmit={event => { event.preventDefault(); void action('Connecting to local API…', connect) }}><label htmlFor="pairing">Local pairing capability</label><input id="pairing" type="password" autoComplete="off" spellCheck={false} value={pairing} onChange={event => setPairing(event.target.value)} required /><button className="primary" disabled={!!busy || !pairing.trim()}>Create local session</button></form></section> : <>
      <div className="research-session-bar"><span>Session lifetime: {Math.round(session.expires_in / 60)} minutes from creation · memory only</span><button onClick={() => { void action('Closing session…', reset) }} disabled={!!busy}>New research session</button></div>
      <div className="research-layout"><aside><section className="panel research-step"><p className="eyebrow">01 / Medication</p><h2>{product ? 'Confirmed product' : 'Find the exact product'}</h2>{product ? <div className="confirmed-product"><Product value={product} /><p>Confirmed and locked. Changing products requires a new session.</p></div> : <><form role="search" onSubmit={event => { event.preventDefault(); void action('Searching frozen product records…', async () => { setChoice(''); setCandidates(null); const found = await researchApi.search(session, query.trim()); setCandidates(found.candidates); setIncomplete(found.results_may_be_incomplete) }) }}><label htmlFor="medication">Brand, ingredient or NDC</label><div className="research-search"><input id="medication" maxLength={200} value={query} onChange={event => setQuery(event.target.value)} placeholder="e.g. Xanax or 0009-0029" required /><button className="primary" disabled={!!busy || !query.trim()}>Search</button></div></form>{candidates && <><p role="status">{candidates.length ? `${candidates.length} candidate${candidates.length === 1 ? '' : 's'} · explicit confirmation required` : 'No matching products in this frozen release.'}</p>{incomplete && <p>Search results may be incomplete. Refine by NDC or exact strength.</p>}<div className="research-candidates">{candidates.map(value => <button key={value.product_ref} aria-pressed={choice === value.product_ref} disabled={!!busy} onClick={() => setChoice(value.product_ref)}><Product value={value} /></button>)}</div>{candidates.length > 0 && <button className="primary confirm-button" disabled={!choice || !!busy} onClick={() => { void action('Verifying exact product…', async () => { const confirmed = await researchApi.confirm(session, choice); setProduct(confirmed.medication); setCandidates(null) }) }}>Confirm selected product</button>}</>}</>}</section></aside>
      <section className="panel research-step"><p className="eyebrow">02 / Research scope</p><h2>What would you like to investigate?</h2><form onSubmit={event => { event.preventDefault(); void action('Starting bounded research…', async () => { setAttempted(true); await researchApi.run(session, question, selected, model || null); setRunning(true) }) }}><label htmlFor="question">Research question</label><textarea id="question" rows={4} maxLength={2000} value={question} disabled={running || attempted} onChange={event => setQuestion(event.target.value)} /><fieldset disabled={running || attempted}><legend>Evidence categories</legend>{Object.entries(categories).map(([key, label]) => <label className="research-check" key={key}><input type="checkbox" checked={selected.includes(key)} onChange={event => setSelected(previous => event.target.checked ? [...previous, key] : previous.filter(value => value !== key))} />{label}</label>)}</fieldset><label htmlFor="model">Execution mode</label><select id="model" value={model} disabled={running || attempted} onChange={event => setModel(event.target.value)}><option value="">Explicit deterministic execution</option>{session.models.map(value => <option key={value} value={value}>{modelNames[value] ?? value} · local model planning</option>)}</select>{session.model_runtime === 'unavailable' && <p className="research-subtle">Ollama is offline or no approved model is installed. Deterministic evidence retrieval remains available.</p>}<button className="primary research-run" disabled={!product || !selected.length || !question.trim() || !!busy || running || attempted}>Research selected evidence</button>{!product && <p className="research-subtle">Confirm an exact product to enable research.</p>}</form>{running && <div role="status"><strong>Research is running locally</strong><p>One bounded workflow is executing. Evidence will appear when verification finishes.</p></div>}{(running || attempted && !result) && <button onClick={() => { void action('Cancelling and closing session…', async () => { await researchApi.cancel(session); generation.current++; owned.current = null; setSession(null); setRunning(false); setProduct(null); setCandidates(null); setAttempted(false); setError(messages.cancelled) }) }} disabled={!!busy}>Cancel and close session</button>}</section></div>
      {result && <Briefing value={result} />}
    </>}
    <footer>Research evidence only. Not medical advice, an individualized safety assessment or FDA endorsement. Frozen data is not live FDA data.</footer></main>
}
