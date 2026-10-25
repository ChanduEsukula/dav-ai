import { useEffect, useRef, useState } from 'react'
import type { Candidate, PublicBriefing } from './contracts'
import { researchApi } from './client'
import type { Session } from './client'
import type { ExperienceMode } from '../components/experienceState'
import EverydayWorkspace from './EverydayWorkspace'
import ResearchProWorkspace from './ResearchProWorkspace'
import { type CohortItem, updateCohortItemWithBriefing } from './cohort'
import './workspace.css'

const categories = {
  labels: 'Drug labeling',
  recalls: 'Historical recalls',
  faers: 'FAERS reporting evidence',
}

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

interface WorkspaceProps {
  mode?: ExperienceMode
}

export default function Workspace({ mode = 'everyday' }: WorkspaceProps) {
  const [pairing, setPairing] = useState('')
  const [session, setSession] = useState<Session | null>(null)
  const owned = useRef<Session | null>(null)
  const [query, setQuery] = useState('')
  const [candidates, setCandidates] = useState<Candidate[] | null>(null)
  const [incomplete, setIncomplete] = useState(false)
  const [choice, setChoice] = useState('')
  const [product, setProduct] = useState<Candidate | null>(null)
  const [question, setQuestion] = useState(
    'What historical recalls, drug-label warnings, and adverse-event reports are available for this medication?'
  )
  const [selected, setSelected] = useState<string[]>(Object.keys(categories))
  const [model, setModel] = useState('')
  const [synthesize, setSynthesize] = useState(false)
  const [busy, setBusy] = useState('')
  const [running, setRunning] = useState(false)
  const [attempted, setAttempted] = useState(false)
  const [result, setResult] = useState<PublicBriefing | null>(null)
  const [error, setError] = useState('')
  const [cohort, setCohort] = useState<CohortItem[]>([])

  const gate = useRef(false)
  const generation = useRef(0)

  const showError = (err: unknown) => {
    const code = err instanceof Error ? err.message : 'api_unavailable'
    setError(
      messages[code] ??
        `Research stopped (${code.replaceAll('_', ' ')}). Start a new session if needed.`
    )
  }

  async function action(label: string, fn: () => Promise<void>) {
    if (gate.current) return
    gate.current = true
    setBusy(label)
    setError('')
    try {
      await fn()
    } catch (err) {
      showError(err)
    } finally {
      gate.current = false
      setBusy('')
    }
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
        if (outcome.state === 'running') {
          timer = setTimeout(() => {
            void poll()
          }, 750)
        } else {
          setRunning(false)
          if (outcome.briefing) {
            const medication = outcome.briefing.medication
            if (!product || medication.product_ref !== product.product_ref
                || medication.product_ndcs.length !== product.product_ndcs.length
                || !product.product_ndcs.every(ndc => medication.product_ndcs.includes(ndc))) {
              showError(new Error('product_binding_changed'))
              return
            }
            setResult(outcome.briefing)
            // Update matching cohort items
            if (product) {
              setCohort((prev) =>
                prev.map((item) =>
                  product.product_ndcs.some((ndc) => item.product_ndcs.includes(ndc))
                    ? updateCohortItemWithBriefing(item, outcome.briefing!)
                    : item
                )
              )
            }
          } else {
            showError(new Error(outcome.code ?? 'research_stopped'))
          }
        }
      } catch (err) {
        if (!stopped && current === generation.current) {
          setRunning(false)
          showError(err)
        }
      }
    }

    timer = setTimeout(() => {
      void poll()
    }, 300)

    return () => {
      stopped = true
      clearTimeout(timer)
    }
  }, [running, session, product])

  async function connect() {
    const next = await researchApi.create(pairing.trim())
    owned.current = next
    setSession(next)
    setPairing('')
    setModel('')
  }

  async function reset() {
    const previous = owned.current
    generation.current++
    owned.current = null
    setSession(null)
    setProduct(null)
    setCandidates(null)
    setChoice('')
    setIncomplete(false)
    setModel('')
    setResult(null)
    setRunning(false)
    setAttempted(false)
    setError('')
    if (previous) await researchApi.close(previous).catch(() => {})
  }

  const handleSelectForDeepResearch = (item: CohortItem) => {
    void action('Preparing selected product…', async () => {
      const ndc = item.product_ndcs[0]
      if (!ndc) return
      if (product?.product_ndcs.includes(ndc)) return
      setQuery(ndc)
      if (product || attempted || running) {
        await reset()
      } else {
        setChoice('')
        setCandidates(null)
        setResult(null)
      }
    })
  }

  const handleSearch = () => {
    if (!session) return
    void action('Searching frozen product records…', async () => {
      if (product) {
        await reset()
        setError('The previous product session was closed. Pair a new local session, then search again to select another product.')
        return
      }
      setChoice('')
      setCandidates(null)
      const found = await researchApi.search(session, query.trim())
      setCandidates(found.candidates)
      setIncomplete(found.results_may_be_incomplete)
    })
  }

  const handleConfirm = () => {
    if (!session || !choice || !candidates?.some(candidate => candidate.product_ref === choice)) return
    void action('Verifying exact product…', async () => {
      const confirmed = await researchApi.confirm(session, choice)
      setProduct(confirmed.medication)
      setCandidates(null)
    })
  }

  const handleRunResearch = () => {
    if (!session || !product || attempted || running) return
    void action('Starting bounded research…', async () => {
      setAttempted(true)
      await researchApi.run(session, question, selected, model || null, synthesize)
      setRunning(true)
    })
  }

  const handleCancelResearch = () => {
    if (!session) return
    void action('Cancelling and closing session…', async () => {
      await researchApi.cancel(session)
      generation.current++
      owned.current = null
      setSession(null)
      setRunning(false)
      setProduct(null)
      setCandidates(null)
      setAttempted(false)
      setError(messages.cancelled)
    })
  }

  const toggleCategory = (cat: string) => {
    setSelected((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    )
  }

  const sharedProps = {
    session,
    pairing,
    setPairing,
    onConnect: () => void action('Connecting to local API…', connect),
    query,
    setQuery,
    onSearch: handleSearch,
    candidates,
    incomplete,
    choice,
    setChoice,
    onConfirm: handleConfirm,
    product,
    question,
    setQuestion,
    selectedCategories: selected,
    toggleCategory,
    model,
    setModel,
    synthesize,
    setSynthesize,
    models: session ? session.models : [],
    onRunResearch: handleRunResearch,
    onCancelResearch: handleCancelResearch,
    onResetSession: () => void action('Closing session…', reset),
    running,
    attempted,
    result,
    busy,
    error,
  }

  return (
    <main className="research-workspace" id="main-content">
      {mode === 'everyday' ? (
        <EverydayWorkspace {...sharedProps} />
      ) : (
        <ResearchProWorkspace
          {...sharedProps}
          cohort={cohort}
          setCohort={setCohort}
          onSelectForDeepResearch={handleSelectForDeepResearch}
        />
      )}
    </main>
  )
}
