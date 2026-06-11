type SafetyWorkspaceProps = {
  goToRecallRadar: () => void
  goToDrugSignal: () => void
  goToFoodRadar: () => void
  goToCosmeticSignal: () => void
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
    title: 'RecallRadar',
    eyebrow: 'Official recall lens',
    description: 'Search recall records with review priority, status, and source trail.',
    chips: ['Review priority', 'FDA class'],
    actionLabel: 'Open RecallRadar',
    variant: 'recall',
    onClick: () => {},
  },
  {
    title: 'DrugSignal',
    eyebrow: 'Adverse-event lens',
    description: 'Compare public FAERS reporting patterns without treating reports as proof.',
    chips: ['Review signal', 'Top reactions'],
    actionLabel: 'Open DrugSignal',
    variant: 'drug',
    onClick: () => {},
  },
  {
    title: 'FoodRadar',
    eyebrow: 'Food and supplement lens',
    description: 'Check food, supplement, meat, poultry, and egg-product recall records.',
    chips: ['FDA food', 'USDA FSIS'],
    actionLabel: 'Open FoodRadar',
    variant: 'health',
    onClick: () => {},
  },
  {
    title: 'CosmeticSignal',
    eyebrow: 'Cosmetic source lens',
    description: 'Review cosmetic-event public records with source context and careful limitations.',
    chips: ['Cosmetics', 'Source trail'],
    actionLabel: 'Open CosmeticSignal',
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

        <div className="safety-dashboard-card__metrics" aria-label="Public data metrics">
          <div className="safety-dashboard-metric safety-dashboard-metric--records">
            <strong>24.6K</strong>
            <span>Records scanned</span>
          </div>

          <div className="safety-dashboard-metric safety-dashboard-metric--weekly">
            <strong>1.2K</strong>
            <span>New this week</span>
          </div>

          <div className="safety-dashboard-metric safety-dashboard-metric--traceable">
            <strong>98%</strong>
            <span>Traceable</span>
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
  goToRecallRadar,
  goToDrugSignal,
  goToFoodRadar,
  goToCosmeticSignal,
}: SafetyWorkspaceProps) {
  const wiredModules: SafetyModule[] = [
    { ...modules[0], onClick: goToRecallRadar },
    { ...modules[1], onClick: goToDrugSignal },
    { ...modules[2], onClick: goToFoodRadar },
    { ...modules[3], onClick: goToCosmeticSignal },
  ]

  const recallModule = wiredModules[0]
  const drugModule = wiredModules[1]
  const foodModule = wiredModules[2]
  const cosmeticModule = wiredModules[3]

  return (
    <section className="safety-workspace" aria-label="Safety intelligence workspace">
      <div className="safety-workspace__header">
        <div>
          <p className="eyebrow">Safety intelligence workspace</p>
          <h2>Choose a safety lens.</h2>
        </div>

        <p>
          Four public-data lenses connect to one source-aware intelligence dashboard for faster
          search, comparison, and source verification.
        </p>
      </div>

      <div className="safety-workspace__dashboard-layout">
        <div className="safety-workspace__module-stack">
          <SafetyLensCard module={recallModule} />
          <SafetyLensCard module={foodModule} />
        </div>

        <SafetyDashboardCore />

        <div className="safety-workspace__module-stack">
          <SafetyLensCard module={drugModule} />
          <SafetyLensCard module={cosmeticModule} />
        </div>
      </div>

      <div className="safety-workspace__bridge">
        <strong>Recommended workflow:</strong>
        <span>
          Start with RecallRadar, compare with DrugSignal, then verify FoodRadar or CosmeticSignal
          source records.
        </span>
      </div>
    </section>
  )
}

export default SafetyWorkspace