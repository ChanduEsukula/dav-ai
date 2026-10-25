type FlowItem = {
  number: string
  title: string
  subtitle: string
  detail: string
  icon: 'problem' | 'search' | 'route' | 'network' | 'layers' | 'report'
  tone: 'teal' | 'blue' | 'purple' | 'green' | 'pink'
  position: 'top-left' | 'middle-left' | 'bottom-left' | 'top-right' | 'middle-right' | 'bottom-right'
}

type SourceGroup = {
  label: string
  detail: string
}

type BoundaryItem = {
  label: string
  icon: 'records' | 'privacy' | 'advice' | 'verdict'
}

const flowItems: FlowItem[] = [
  { number: '01', title: 'Find the exact product', subtitle: 'Identity first', detail: 'Search a brand, ingredient or NDC. Check strength, dosage form and package identifiers.', icon: 'search', tone: 'teal', position: 'top-left' },
  { number: '02', title: 'Confirm before research', subtitle: 'Human confirmation', detail: 'Explicitly confirm one product. Similar names and different formulations stay separate.', icon: 'route', tone: 'blue', position: 'middle-left' },
  { number: '03', title: 'Retrieve admitted evidence', subtitle: 'SQL + Hybrid RAG', detail: 'Structured source reads and optional BGE/FAISS retrieval stay scoped to the confirmed product.', icon: 'network', tone: 'purple', position: 'bottom-left' },
  { number: '04', title: 'Check evidence boundaries', subtitle: 'Source admission', detail: 'Exact-product labels, package recall scope and ingredient-level reporting retain their distinct limits.', icon: 'layers', tone: 'green', position: 'top-right' },
  { number: '05', title: 'Select source statements', subtitle: 'Optional local AI', detail: 'The local model selects admitted statement IDs. Python restores exact quotes, headings and citations.', icon: 'problem', tone: 'pink', position: 'middle-right' },
  { number: '06', title: 'Follow the source', subtitle: 'Review + provenance', detail: 'Open cited label text, inspect source dates and limitations, or export an Explorer evidence PDF.', icon: 'report', tone: 'blue', position: 'bottom-right' },
]

const sourceGroups: SourceGroup[] = [
  { label: 'Product directory', detail: 'NDC, strength, dosage form and ingredients' },
  { label: 'Drug labeling', detail: 'Admitted exact-product label sections' },
  { label: 'Historical recalls', detail: 'Product/package links with lot limitations' },
  { label: 'FAERS reporting', detail: 'Ingredient associations, never causal risk' },
]

const boundaryItems: BoundaryItem[] = [
  { label: 'Frozen source data', icon: 'records' },
  { label: 'Local research sessions', icon: 'privacy' },
  { label: 'Not medical advice', icon: 'advice' },
  { label: 'Human review required', icon: 'verdict' },
]

function FlowIcon({ icon }: { icon: FlowItem['icon'] }) {
  if (icon === 'problem') {
    return (
      <svg viewBox="0 0 48 48" focusable="false">
        <rect x="8" y="9" width="12" height="12" rx="3" />
        <rect x="28" y="7" width="12" height="12" rx="3" />
        <rect x="10" y="28" width="12" height="12" rx="3" />
        <rect x="30" y="29" width="10" height="10" rx="3" />
        <path d="M20 15h8M16 21v7M22 34h8M34 19v10" />
      </svg>
    )
  }

  if (icon === 'search') {
    return (
      <svg viewBox="0 0 48 48" focusable="false">
        <circle cx="21" cy="21" r="12" />
        <path d="M30 30l10 10" />
        <path d="M16 21h10M21 16v10" />
      </svg>
    )
  }

  if (icon === 'route') {
    return (
      <svg viewBox="0 0 48 48" focusable="false">
        <circle cx="12" cy="24" r="4" />
        <circle cx="36" cy="12" r="4" />
        <circle cx="36" cy="36" r="4" />
        <path d="M16 24h7c5 0 5-12 9-12" />
        <path d="M16 24h7c5 0 5 12 9 12" />
        <path d="M23 24h7" />
      </svg>
    )
  }

  if (icon === 'network') {
    return (
      <svg viewBox="0 0 48 48" focusable="false">
        <ellipse cx="24" cy="12" rx="13" ry="6" />
        <path d="M11 12v22c0 3.3 5.8 6 13 6s13-2.7 13-6V12" />
        <path d="M11 23c0 3.3 5.8 6 13 6s13-2.7 13-6" />
        <path d="M9 36l-4 4M39 36l4 4M24 40v5" />
      </svg>
    )
  }

  if (icon === 'layers') {
    return (
      <svg viewBox="0 0 48 48" focusable="false">
        <path d="M24 7l17 9-17 9-17-9 17-9z" />
        <path d="M7 24l17 9 17-9" />
        <path d="M7 32l17 9 17-9" />
      </svg>
    )
  }

  return (
    <svg viewBox="0 0 48 48" focusable="false">
      <path d="M14 6h15l7 7v29H14V6z" />
      <path d="M29 6v8h7" />
      <path d="M19 22h14M19 29h14M19 36h9" />
      <path d="M9 14h5M9 22h5M9 30h5" />
    </svg>
  )
}

function BoundaryIcon({ icon }: { icon: BoundaryItem['icon'] }) {
  if (icon === 'records') {
    return (
      <svg viewBox="0 0 24 24" focusable="false">
        <path d="M7 3.5h7l4 4v13H7v-17z" />
        <path d="M14 3.5v4.5h4" />
        <path d="M10 12h5M10 16h4" />
      </svg>
    )
  }

  if (icon === 'privacy') {
    return (
      <svg viewBox="0 0 24 24" focusable="false">
        <path d="M12 3.5l7 3v5.3c0 4-2.8 7.2-7 8.7-4.2-1.5-7-4.7-7-8.7V6.5l7-3z" />
        <rect x="8.75" y="11" width="6.5" height="5.25" rx="1.4" />
        <path d="M10.5 11V9.8a1.5 1.5 0 0 1 3 0V11" />
      </svg>
    )
  }

  if (icon === 'advice') {
    return (
      <svg viewBox="0 0 24 24" focusable="false">
        <path d="M5.5 5.5h13v9h-7l-4 3.5v-3.5h-2v-9z" />
        <path d="M8.5 9h7M8.5 12h4.5" />
      </svg>
    )
  }

  return (
    <svg viewBox="0 0 24 24" focusable="false">
      <path d="M6 5.5h12v13H6v-13z" />
      <path d="M9 9h6M9 12h4" />
      <path d="M8.5 16.2l2 1.8 5-5" />
      <path d="M5 19l14-14" />
    </svg>
  )
}

function OperationalOverview() {
  return (
    <section id="workflow" className="operational-flow section-reveal" aria-labelledby="operational-flow-title">
      <div className="operational-flow__shell">
        <div className="operational-flow__header">
          <div>
            <p className="operational-flow__eyebrow">Operational view</p>
            <h2 id="operational-flow-title">From product identity to traceable evidence</h2>
            <p>
              Pharmaceutical information is spread across labels, recall records and
              reporting datasets. Dav AI brings those sources into one bounded research
              workflow, keeping product identity and evidence limitations visible.
            </p>
          </div>

          <div className="operational-flow__trust" aria-label="Safety and privacy boundaries">
            {boundaryItems.map((item) => (
              <span className="operational-flow__trust-item" key={item.label}>
                <span className="operational-flow__trust-icon" aria-hidden="true">
                  <BoundaryIcon icon={item.icon} />
                </span>
                {item.label}
              </span>
            ))}
          </div>
        </div>

        <div
          className="operational-flow__architecture"
          aria-label="Dav AI pharmaceutical research workflow"
        >
          <div className="operational-flow__core" aria-hidden="true">
            <span className="operational-flow__core-ring"></span>
            <span className="operational-flow__core-label">DavAI</span>
            <span className="operational-flow__core-subtitle">evidence workflow</span>
          </div>

          {flowItems.map((item) => (
            <article
              className={`operational-flow__card operational-flow__card--${item.tone} operational-flow__card--${item.position}`}
              key={item.number}
            >
              <span className="operational-flow__number">{item.number}</span>

              <span className="operational-flow__icon" aria-hidden="true">
                <FlowIcon icon={item.icon} />
              </span>

              <div className="operational-flow__copy">
                <span>{item.subtitle}</span>
                <strong>{item.title}</strong>
                <p>{item.detail}</p>
              </div>
            </article>
          ))}
        </div>

        <div className="operational-flow__source-fabric" aria-label="Evidence sources">
          <div className="operational-flow__source-header">
            <span>Evidence sources</span>
            <p>Stored FDA/openFDA sources; not a live safety feed.</p>
          </div>

          <div className="operational-flow__source-grid">
            {sourceGroups.map((source) => (
              <article key={source.label}>
                <strong>{source.label}</strong>
                <p>{source.detail}</p>
              </article>
            ))}
          </div>
        </div>

        <div className="operational-flow__bottom">
          <span className="operational-flow__live">
            <i aria-hidden="true"></i>
            Exact product · scoped evidence · traceable citations
          </span>

          <span className="operational-flow__boundary-note">
            Verify with original sources. Public records support review, not advice or verdicts.
          </span>
        </div>
      </div>
    </section>
  )
}

export default OperationalOverview
