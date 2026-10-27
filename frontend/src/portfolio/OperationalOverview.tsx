import { useState } from 'react'
import { motion } from 'motion/react'
import type { ExperienceMode } from '../components/experienceState'
import { useMotionPreference } from './useMotionPreference'

type Kind = 'api' | 'processing' | 'database' | 'retrieval' | 'document'
export function ArchitectureIcon({ kind }: { kind: Kind }) {
  return <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
    {kind === 'database' ? <><ellipse cx="24" cy="10" rx="15" ry="6" /><path d="M9 10v27c0 4 30 4 30 0V10M9 23c0 8 30 8 30 0M9 35c0 8 30 8 30 0" /></>
      : kind === 'processing' ? <><circle cx="24" cy="24" r="12" /><circle cx="24" cy="24" r="5" />{Array.from({ length: 8 }, (_, i) => <path key={i} d="M24 5v6" transform={`rotate(${i * 45} 24 24)`} />)}</>
        : kind === 'api' ? <><rect x="5" y="8" width="38" height="32" rx="6" /><path d="M5 17h38M11 12h.1M16 12h.1M19 24l-5 5 5 5M29 24l5 5-5 5" /></>
          : kind === 'retrieval' ? <><circle cx="20" cy="20" r="12" /><path d="m29 29 12 12M15 20h10M20 15v10" /></>
            : <><path d="M12 5h16l9 9v29H12V5ZM28 5v10h9M18 23h12M18 29h12M18 35h8" /></>}
  </svg>
}

const technical = [
  { title: 'FDA source snapshots', subtitle: 'FDA / openFDA', kind: 'api' as Kind, detail: 'Preserved NDC directory identities, SPL drug-label text, enforcement recall records and ingredient-level FAERS analytics. Each source has its own vintage; the application is not a live FDA feed.', source: 'scripts/pharma_release/sources.py · app/services/pharma/evidence.py' },
  { title: 'Ingestion and validation', subtitle: 'Offline release pipeline', kind: 'processing' as Kind, detail: 'Offline builders normalize preserved identifiers, extract label sections and validate product/ingredient/formulation applicability, eligibility and source provenance. Packaging creates the frozen release and its manifest. This is separate from serving requests.', source: 'scripts/pharma_release/ · release contract, schema and validation modules' },
  { title: 'Frozen SQLite database', subtitle: 'Read-only evidence store', kind: 'database' as Kind, detail: 'The sealed SQLite release stores products, identifiers, product-to-label/recall links, coverage, source descriptors and ingredient analytics. Runtime reads use immutable/read-only connections, checksum verification and existing serving authorization. No PostgreSQL fallback serves pharmaceutical evidence.', source: 'app/db/pharma/release_connection.py · release_repository.py' },
  { title: 'API and bounded retrieval', subtitle: 'FastAPI · Pydantic · optional RAG', kind: 'retrieval' as Kind, detail: 'FastAPI exposes typed read endpoints. Exact-product research requires an authorized local session and explicit confirmation. A bounded Python workflow retrieves source-scoped evidence. Optional BGE/FAISS retrieval needs external corpus/index artifacts; it is not guaranteed to be configured.', source: 'app/routes/ · app/local_research/ · app/agent/workflow.py · rag_adapter.py' },
  { title: 'Cited outputs and export', subtitle: 'React · TypeScript · optional Ollama', kind: 'document' as Kind, detail: 'React renders structured evidence and conservative partial results. Optional local Ollama synthesis selects admitted statement IDs; Python reconstructs exact quotes and validates citations. Invalid output is discarded. The existing PDF service exports source evidence, dates and limitations.', source: 'app/agent/synthesis.py · app/services/report_pdf.py · frontend/src/research/' },
]
const everyday = [technical[0], technical[1], { ...technical[2], title: 'Evidence application', subtitle: 'Database, search and local research', detail: technical[2].detail + ' ' + technical[3].detail }, { ...technical[4], title: 'Findings you can inspect', subtitle: 'Source links and supported reports' }]

export function ArchitecturePreview() {
  return <div className="architecture-preview" aria-label="FDA data to source-linked outputs">{[
    ['api', 'FDA snapshots'], ['processing', 'Validate'], ['database', 'Frozen SQLite'], ['retrieval', 'Retrieve'], ['document', 'Cited outputs'],
  ].map(([kind, label]) => <div key={label}><ArchitectureIcon kind={kind as Kind} /><span>{label}</span></div>)}</div>
}

function FlowNode({ stage, index, pro }: { stage: typeof technical[number]; index: number; pro: boolean }) {
  const [active, setActive] = useState(false)
  const reduced = useMotionPreference()
  return <motion.article className={`flow-stage architecture-${stage.kind}${active ? ' is-active' : ''}`} initial={false}
    whileInView={{ y: 0, opacity: 1 }} viewport={{ once: true, amount: .4 }} onViewportEnter={() => setActive(true)}>
    <span className="flow-node-icon" style={{ transitionDelay: reduced ? '0s' : `${index * .15}s` }}><ArchitectureIcon kind={stage.kind} /></span>
    <span className="flow-node-number">0{index + 1}</span><h3>{stage.title}</h3><p title={stage.detail}>{stage.subtitle}</p>
    <details><summary>Explore this stage <span aria-hidden="true">+</span></summary><p>{stage.detail}</p>{pro && <code className="architecture-source">{stage.source}</code>}</details>
  </motion.article>
}

export default function OperationalOverview({ mode = 'everyday' }: { mode?: ExperienceMode }) {
  const pro = mode === 'research_pro'
  return <section className={`evidence-flow architecture-flow${pro ? ' is-technical' : ''}`} id="workflow" aria-labelledby="operational-flow-title">
    <div className="flow-introduction"><p className="eyebrow">{pro ? 'Verified repository architecture' : 'How the application is built'}</p><h2 id="operational-flow-title">{pro ? 'Data pipeline, serving layer and research controls.' : 'FDA data → processing → evidence application → cited findings.'}</h2><p>{pro ? 'The offline build path, read-only serving path and optional local AI are distinct components.' : 'Open each stage to see how stored source data becomes evidence you can inspect.'}</p></div>
    <div className="flow-nodes">{(pro ? technical : everyday).map((stage, index) => <FlowNode key={stage.title} stage={stage} index={index} pro={pro} />)}</div>
    <div className="architecture-optionals"><article><ArchitectureIcon kind="retrieval" /><strong>Optional retrieval</strong><p>BGE embeddings and FAISS passage retrieval require a separately configured local corpus and index. Candidate passages do not independently authorize an answer.</p></article><article><ArchitectureIcon kind="processing" /><strong>Optional local synthesis</strong><p>Ollama selects admitted statement IDs. Python restores exact source quotes and citations. Deterministic reads and PDF exports do not require model synthesis.</p></article></div>
    <div className="flow-boundaries"><span>Sealed read-only SQLite</span><span>Capability-authenticated local research</span><span>Source admission and provenance</span><span>Publication not authorized</span></div>
    <p className="flow-footnote">Architecture explanation, not live execution progress. React/TypeScript is the presentation layer; FastAPI/Pydantic and the bounded Python workflow enforce the research contract. This diagram makes no claim that optional artifacts are currently configured.</p>
  </section>
}
