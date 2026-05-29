type FlowItem = {
  number: string
  title: string
  subtitle: string
  detail: string
  icon: 'database' | 'shield' | 'radar' | 'capsule' | 'bookmark' | 'pulse'
  tone: 'teal' | 'blue' | 'purple' | 'green'
}

const flowItems: FlowItem[] = [
  {
    number: '01',
    title: 'openFDA',
    subtitle: 'Public sources',
    detail: 'Recall and adverse-event data from public FDA sources.',
    icon: 'database',
    tone: 'teal',
  },
  {
    number: '02',
    title: 'Provenance',
    subtitle: 'Audit trail',
    detail: 'Source, timestamp, and request ID stay visible.',
    icon: 'shield',
    tone: 'blue',
  },
  {
    number: '03',
    title: 'Risk review',
    subtitle: 'RecallRadar',
    detail: 'Classification-aware recall scoring for safety signals.',
    icon: 'radar',
    tone: 'purple',
  },
  {
    number: '04',
    title: 'Signal scan',
    subtitle: 'DrugSignal',
    detail: 'Explore drug side-effect reporting patterns.',
    icon: 'capsule',
    tone: 'blue',
  },
  {
    number: '05',
    title: 'Watchlists',
    subtitle: 'Saved monitors',
    detail: 'Save monitors and review manual run history.',
    icon: 'bookmark',
    tone: 'green',
  },
  {
    number: '06',
    title: 'Data quality',
    subtitle: 'System status',
    detail: 'Track freshness and operational visibility.',
    icon: 'pulse',
    tone: 'teal',
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

  if (icon === 'bookmark') {
    return (
      <svg viewBox="0 0 48 48" focusable="false">
        <path d="M15 8h18c1.7 0 3 1.3 3 3v29L24 33l-12 7V11c0-1.7 1.3-3 3-3z" />
      </svg>
    )
  }

  return (
    <svg viewBox="0 0 48 48" focusable="false">
      <path d="M6 25h9l4-8 6 17 5-12 4 3h8" />
    </svg>
  )
}

function OperationalOverview() {
  return (
    <section className="operational-flow" aria-labelledby="operational-flow-title">
      <div className="operational-flow__shell">
        <div className="operational-flow__header">
          <div>
            <p className="operational-flow__eyebrow">Operational view</p>
            <h2 id="operational-flow-title">Safety intelligence at a glance</h2>
            <p>
              A source-aware operating layer for public recall, drug-safety, and regional
              signal workflows.
            </p>
          </div>

          <div className="operational-flow__trust" aria-label="Safety and privacy boundaries">
            <span>Public sources only</span>
            <span>No PHI</span>
            <span>Not medical advice</span>
          </div>
        </div>

        <div className="operational-flow__grid" aria-label="DAV AI operational capabilities">
          {flowItems.map((item) => (
            <article
              className={`operational-flow__card operational-flow__card--${item.tone}`}
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

        <div className="operational-flow__bottom">
          <a className="operational-flow__cta" href="#recallradar">
            Start with RecallRadar <span aria-hidden="true">→</span>
          </a>

          <span className="operational-flow__live">
            <i aria-hidden="true"></i>
            Live data flow
          </span>
        </div>
      </div>
    </section>
  )
}

export default OperationalOverview