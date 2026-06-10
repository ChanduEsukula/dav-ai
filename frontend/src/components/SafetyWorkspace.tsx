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

function SafetyWorkspace({
  goToRecallRadar,
  goToDrugSignal,
  goToFoodRadar,
  goToCosmeticSignal,
}: SafetyWorkspaceProps) {
  const modules: SafetyModule[] = [
    {
      title: 'RecallRadar',
      eyebrow: 'Official recall lens',
      description: 'Search recall records with review priority, status, and source trail.',
      chips: ['Review priority', 'FDA class', 'Audit trail'],
      actionLabel: 'Open RecallRadar',
      variant: 'recall',
      onClick: goToRecallRadar,
    },
    {
      title: 'DrugSignal',
      eyebrow: 'Adverse-event lens',
      description: 'Compare public FAERS reporting patterns without treating reports as proof.',
      chips: ['Review signal', 'Top reactions', 'Trend snapshot'],
      actionLabel: 'Open DrugSignal',
      variant: 'drug',
      onClick: goToDrugSignal,
    },
    {
      title: 'FoodRadar',
      eyebrow: 'Food and supplement lens',
      description: 'Check food, supplement, meat, poultry, and egg-product recall records.',
      chips: ['FDA food', 'USDA FSIS', 'Source trail'],
      actionLabel: 'Open FoodRadar',
      variant: 'health',
      onClick: goToFoodRadar,
    },
    {
      title: 'CosmeticSignal',
      eyebrow: 'Cosmetic source lens',
      description: 'Review cosmetic-event public records with source context and careful limitations.',
      chips: ['Cosmetics', 'Public records', 'Source trail'],
      actionLabel: 'Open CosmeticSignal',
      variant: 'cosmetic',
      onClick: goToCosmeticSignal,
    },
  ]

  return (
    <section className="safety-workspace" aria-label="Safety intelligence workspace">
      <div className="safety-workspace__header">
        <div>
          <p className="eyebrow">Safety intelligence workspace</p>
          <h2>Choose a safety lens.</h2>
        </div>

        <p>
          Start with recalls, compare public adverse-event patterns, then check food,
          supplement, and cosmetic records — all with source context preserved.
        </p>
      </div>

      <div className="safety-workspace__grid">
        {modules.map((module) => (
          <button
            key={module.title}
            type="button"
            className={`safety-workspace-card safety-workspace-card--${module.variant}`}
            onClick={module.onClick}
            aria-label={module.actionLabel}
          >
            <span className="safety-workspace-card__icon" aria-hidden="true">
              {module.variant === 'recall' && (
                <svg className="safety-radar-icon" viewBox="0 0 48 48" focusable="false">
                  <circle className="safety-radar-outer-ring" cx="24" cy="24" r="17" />
                  <circle className="safety-radar-inner-ring" cx="24" cy="24" r="9" />
                  <path className="safety-radar-sweep" d="M24 24 L24 7" />
                  <circle className="safety-radar-dot" cx="24" cy="24" r="3.5" />
                  <circle className="safety-radar-target" cx="32" cy="16" r="2.4" />
                </svg>
              )}

              {module.variant === 'drug' && (
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

                  <circle
                    className="safety-capsule-dot safety-capsule-dot-one"
                    cx="34"
                    cy="14"
                    r="2"
                  />
                  <circle
                    className="safety-capsule-dot safety-capsule-dot-two"
                    cx="14"
                    cy="34"
                    r="1.7"
                  />
                </svg>
              )}

              {module.variant === 'health' && (
                <svg className="safety-health-icon" viewBox="0 0 48 48" focusable="false">
                  <path
                    className="safety-pulse-guide"
                    d="M6 25 H15 L19 17 L25 34 L30 22 L34 25 H42"
                  />
                  <path
                    className="safety-pulse-line"
                    d="M6 25 H15 L19 17 L25 34 L30 22 L34 25 H42"
                  />
                </svg>
              )}

              {module.variant === 'cosmetic' && (
                <svg className="safety-health-icon" viewBox="0 0 48 48" focusable="false">
                  <circle className="safety-pulse-guide" cx="24" cy="24" r="14" />
                  <path
                    className="safety-pulse-line"
                    d="M16 24 C18 16 30 16 32 24 C30 32 18 32 16 24 Z"
                  />
                  <circle className="safety-pulse-line" cx="24" cy="24" r="3" />
                </svg>
              )}
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
        ))}
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