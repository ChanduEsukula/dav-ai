type FlowItem = {
  number: string
  title: string
  subtitle: string
  detail: string
  icon: 'database' | 'shield' | 'radar' | 'capsule' | 'leaf' | 'bottle'
  tone: 'teal' | 'blue' | 'purple' | 'green' | 'pink'
}

const flowItems: FlowItem[] = [
  {
    number: '01',
    title: 'Public sources',
    subtitle: 'FDA + openFDA',
    detail: 'Recall, adverse-event, food, cosmetic, and CAERS data from public sources.',
    icon: 'database',
    tone: 'teal',
  },
  {
    number: '02',
    title: 'Provenance',
    subtitle: 'Audit trail',
    detail: 'Source, timestamp, and request ID stay visible for every review.',
    icon: 'shield',
    tone: 'blue',
  },
  {
    number: '03',
    title: 'DrugSignal',
    subtitle: 'Recalls + event patterns',
    detail: 'Drug recall records and FAERS reporting patterns in one routed workspace.',
    icon: 'radar',
    tone: 'purple',
  },
  {
    number: '04',
    title: 'FoodSignal',
    subtitle: 'Food + supplements',
    detail: 'Review food, supplement, meat, poultry, and egg-product recall records.',
    icon: 'leaf',
    tone: 'green',
  },
  {
    number: '05',
    title: 'Personal Care Signals',
    subtitle: 'Cosmetic events',
    detail: 'Review cosmetic-event public records with source context and limitations.',
    icon: 'bottle',
    tone: 'pink',
  },
  {
    number: '06',
    title: 'Review boundaries',
    subtitle: 'Verification first',
    detail: 'Public records support review and source verification, not clinical decisions.',
    icon: 'shield',
    tone: 'blue',
  },
]

function FlowIcon({ icon }: { icon: FlowItem['icon'] }) {
  if (icon === 'database') {
    return (
      <svg viewBox="0 0 48 48" focusable="false">
        <ellipse cx="24" cy="12" rx="13" ry="6" />
        <path d="M11 12v22c0 3.3 5.8 6 13 6s13-2.7 13-6V12" />
        <path d="M11 23c0 3.3 5.8 6 13 6s13-2.7 13-6" />
      </svg>
    )
  }

  if (icon === 'shield') {
    return (
      <svg viewBox="0 0 48 48" focusable="false">
        <path d="M24 6l14 5v11c0 9-5.6 16.6-14 20-8.4-3.4-14-11-14-20V11l14-5z" />
        <path d="M17 24l5 5 10-12" />
      </svg>
    )
  }

  if (icon === 'radar') {
    return (
      <svg viewBox="0 0 48 48" focusable="false">
        <circle cx="24" cy="24" r="16" />
        <circle cx="24" cy="24" r="9" />
        <circle cx="24" cy="24" r="3" />
        <path d="M24 24l11-11" />
      </svg>
    )
  }

  if (icon === 'capsule') {
    return (
      <svg viewBox="0 0 48 48" focusable="false">
        <rect x="10" y="17" width="28" height="14" rx="7" transform="rotate(-38 24 24)" />
        <path d="M19 16l10 16" />
      </svg>
    )
  }

  if (icon === 'leaf') {
    return (
      <svg viewBox="0 0 48 48" focusable="false">
        <path d="M24 39V22" />
        <path d="M24 29c-8.5 0-14-5.5-14-14 8.5 0 14 5.5 14 14z" />
        <path d="M24 29c8.5 0 14-5.5 14-14-8.5 0-14 5.5-14 14z" />
      </svg>
    )
  }

  return (
    <svg viewBox="0 0 48 48" focusable="false">
      <path d="M19 7h10" />
      <path d="M21 7v8l-5 6v17c0 2 1.6 3.5 3.5 3.5h9c1.9 0 3.5-1.5 3.5-3.5V21l-5-6V7" />
      <path d="M18 27h12" />
    </svg>
  )
}

function OperationalOverview({ goToPharmacySafety }: { goToPharmacySafety: () => void }) {
  return (
    <section className="operational-flow" aria-labelledby="operational-flow-title">
      <div className="operational-flow__shell">
        <div className="operational-flow__header">
          <div>
            <p className="operational-flow__eyebrow">Operational view</p>
            <h2 id="operational-flow-title">Public-data intelligence at a glance</h2>
            <p>
              A source-aware operating layer for recall, adverse-event, food, cosmetic, and
              regional public-data workflows.
            </p>
          </div>

          <div className="operational-flow__trust" aria-label="Safety and privacy boundaries">
            <span>Public sources only</span>
            <span>No PHI</span>
            <span>Not medical advice</span>
          </div>
        </div>

        <div className="operational-flow__grid" aria-label="DAV AI operational capabilities">
          {flowItems.map((item, index) => (
            <div className="operational-flow__step" key={item.number}>
              <article className={`operational-flow__card operational-flow__card--${item.tone}`}>
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

              {index !== 2 && index < flowItems.length - 1 && (
                <span className="operational-flow__arrow" aria-hidden="true">
                  <span>→</span>
                </span>
              )}
            </div>
          ))}
        </div>

        <div className="operational-flow__bottom">
          <button
            type="button"
            className="operational-flow__cta"
            onClick={goToPharmacySafety}
          >
            Open DrugSignal <span aria-hidden="true">→</span>
          </button>

          <span className="operational-flow__live">
            <i aria-hidden="true"></i>
            Saved monitors + system status
          </span>
        </div>
      </div>
    </section>
  )
}

export default OperationalOverview
