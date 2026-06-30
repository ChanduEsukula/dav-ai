type SafetyWorkspaceProps = {
  goToPharmacySafety: () => void
  goToFoodSafety: () => void
  goToCosmeticSafety: () => void
}

type SafetyModule = {
  title: string
  eyebrow: string
  description: string
  chips: string[]
  actionLabel: string
  variant: 'recall' | 'drug' | 'health' | 'cosmetic'
  onClick: () => void
}

const modules: SafetyModule[] = [
  {
    title: 'DrugSignal',
    eyebrow: 'Drug safety workspace',
    description: 'Review official recall records alongside public FAERS reporting patterns.',
    chips: ['Drug recalls', 'FAERS patterns'],
    actionLabel: 'Open DrugSignal',
    variant: 'recall',
    onClick: () => {},
  },
  {
    title: 'FoodSignal',
    eyebrow: 'Food and supplement workspace',
    description: 'Check food, supplement, meat, poultry, and egg-product recall records.',
    chips: ['FDA food', 'USDA FSIS'],
    actionLabel: 'Open FoodSignal',
    variant: 'health',
    onClick: () => {},
  },
  {
    title: 'Personal Care Signals',
    eyebrow: 'Cosmetic event workspace',
    description: 'Review cosmetic-event public records with source context and careful limitations.',
    chips: ['Cosmetics', 'Source trail'],
    actionLabel: 'Open Personal Care Signals',
    variant: 'cosmetic',
    onClick: () => {},
  },
]

const sourceItems = [
  {
    label: 'FDA',
    variant: 'recall' as const,
  },
  {
    label: 'openFDA',
    variant: 'drug' as const,
  },
  {
    label: 'USDA FSIS',
    variant: 'health' as const,
  },
  {
    label: 'CAERS',
    variant: 'cosmetic' as const,
  },
]

function SafetyModuleIcon({ variant }: { variant: SafetyModule['variant'] }) {
  if (variant === 'recall') {
    return (
      <svg className="safety-radar-icon" viewBox="0 0 48 48" focusable="false">
        <circle className="safety-radar-outer-ring" cx="24" cy="24" r="17" />
        <circle className="safety-radar-inner-ring" cx="24" cy="24" r="9" />
        <path className="safety-radar-sweep" d="M24 24 L24 7" />
        <circle className="safety-radar-dot" cx="24" cy="24" r="3.5" />
        <circle className="safety-radar-target" cx="32" cy="16" r="2.4" />
      </svg>
    )
  }

  if (variant === 'drug') {
    return (
      <svg className="safety-drug-icon" viewBox="0 0 48 48" focusable="false">
        <g className="safety-capsule-motion">
          <rect
            className="safety-capsule-body"
            x="12"
            y="17"
            width="24"
            height="14"
            rx="7"
            transform="rotate(-38 24 24)"
          />
          <path className="safety-capsule-divider" d="M20 16 L28 32" />
        </g>

        <circle className="safety-capsule-dot safety-capsule-dot-one" cx="34" cy="14" r="2" />
        <circle className="safety-capsule-dot safety-capsule-dot-two" cx="14" cy="34" r="1.7" />
      </svg>
    )
  }

  if (variant === 'cosmetic') {
    return (
      <svg className="safety-health-icon" viewBox="0 0 48 48" focusable="false">
        <circle className="safety-pulse-guide" cx="24" cy="24" r="14" />
        <path
          className="safety-pulse-line"
          d="M16 24 C18 16 30 16 32 24 C30 32 18 32 16 24 Z"
        />
        <circle className="safety-pulse-line" cx="24" cy="24" r="3" />
      </svg>
    )
  }

  return (
    <svg className="safety-health-icon" viewBox="0 0 48 48" focusable="false">
      <path className="safety-pulse-guide" d="M6 25 H15 L19 17 L25 34 L30 22 L34 25 H42" />
      <path className="safety-pulse-line" d="M6 25 H15 L19 17 L25 34 L30 22 L34 25 H42" />
    </svg>
  )
}

function SafetyLensCard({ module }: { module: SafetyModule }) {
  return (
    <button
      type="button"
      className={`safety-workspace-card safety-workspace-card--${module.variant}`}
      onClick={module.onClick}
      aria-label={module.actionLabel}
    >
      <span className="safety-workspace-card__icon" aria-hidden="true">
        <SafetyModuleIcon variant={module.variant} />
      </span>

      <span className="safety-workspace-card__content">
        <small>{module.eyebrow}</small>
        <strong>{module.title}</strong>
        <span>{module.description}</span>

        <span
          className="safety-workspace-card__meta"
          role="list"
          aria-label={`${module.title} highlights`}
        >
          {module.chips.map((chip) => (
            <span key={chip} role="listitem">
              {chip}
            </span>
          ))}
        </span>
      </span>

      <span className="safety-workspace-card__arrow" aria-hidden="true">
        →
      </span>
    </button>
  )
}

function SafetySourceIcon({ variant }: { variant: SafetyModule['variant'] }) {
  return (
    <span className={`safety-dashboard-source__icon safety-dashboard-source__icon--${variant}`}>
      <SafetyModuleIcon variant={variant} />
    </span>
  )
}

function SafetyDashboardCore() {
  return (
    <div className="safety-dashboard-core" aria-label="Source-aware intelligence dashboard preview">
      <div className="safety-dashboard-card">
        <div className="safety-dashboard-card__header">
          <small>Source-aware intelligence</small>
          <strong>Live public data overview</strong>
        </div>

        <div className="safety-dashboard-card__metrics" aria-label="Public data boundaries">
          <div className="safety-dashboard-metric safety-dashboard-metric--records">
            <strong>Official</strong>
            <span>Public source records</span>
          </div>

          <div className="safety-dashboard-metric safety-dashboard-metric--weekly">
            <strong>Traceable</strong>
            <span>Source + retrieval context</span>
          </div>

          <div className="safety-dashboard-metric safety-dashboard-metric--traceable">
            <strong>Bounded</strong>
            <span>Not medical advice</span>
          </div>
        </div>

        <div className="safety-dashboard-card__sources">
          <span>Active sources</span>

          <div className="safety-dashboard-source-grid">
            {sourceItems.map((source) => (
              <div className="safety-dashboard-source" key={source.label}>
                <SafetySourceIcon variant={source.variant} />
                <span>{source.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function SafetyWorkspace({
  goToPharmacySafety,
  goToFoodSafety,
  goToCosmeticSafety,
}: SafetyWorkspaceProps) {
  const wiredModules: SafetyModule[] = [
    { ...modules[0], onClick: goToPharmacySafety },
    { ...modules[1], onClick: goToFoodSafety },
    { ...modules[2], onClick: goToCosmeticSafety },
  ]

  const pharmacyModule = wiredModules[0]
  const foodModule = wiredModules[1]
  const cosmeticModule = wiredModules[2]

  return (
    <section className="safety-workspace" aria-label="Safety intelligence workspace">
      <div className="safety-workspace__header">
        <div>
          <p className="eyebrow">Safety intelligence workspace</p>
          <h2>Choose a safety lens.</h2>
        </div>

        <p>
          Three public-data workspaces connect to one source-aware intelligence dashboard for faster
          search, comparison, and source verification.
        </p>
      </div>

      <div className="safety-workspace__dashboard-layout">
        <div className="safety-workspace__module-stack">
          <SafetyLensCard module={pharmacyModule} />
          <SafetyLensCard module={foodModule} />
        </div>

        <SafetyDashboardCore />

        <div className="safety-workspace__module-stack">
          <SafetyLensCard module={cosmeticModule} />
        </div>
      </div>

      <div className="safety-workspace__bridge">
        <strong>Recommended workflow:</strong>
        <span>
          Choose the product area, review returned records, then verify the source and audit
          context before acting.
        </span>
      </div>
    </section>
  )
}

export default SafetyWorkspace
