import type { RecallSearchResponse } from '../api/recalls'

type HeroProps = {
  data: RecallSearchResponse | null
  goToRecallRadar: () => void
  goToDrugSignal: () => void
  goToFoodRadar: () => void
  goToAbout: () => void
}

type HeroModule = {
  title: string
  subtitle: string
  key: 'recallradar' | 'drugsignal' | 'foodradar'
  className: string
  icon: 'recall' | 'drug' | 'health'
}

const heroModules: HeroModule[] = [
  {
    title: 'RecallRadar',
    subtitle: 'Find recall records',
    key: 'recallradar',
    className: 'hero-module-recall',
    icon: 'recall',
  },
  {
    title: 'DrugSignal',
    subtitle: 'Side-effect patterns',
    key: 'drugsignal',
    className: 'hero-module-drug',
    icon: 'drug',
  },
  {
    title: 'FoodRadar',
    subtitle: 'Food & supplement recalls',
    key: 'foodradar',
    className: 'hero-module-health',
    icon: 'health',
  },
]

function HeroModuleIcon({ icon }: { icon: HeroModule['icon'] }) {
  if (icon === 'recall') {
    return (
      <span className="hero-module-icon hero-module-icon-recall" aria-hidden="true">
        <svg viewBox="0 0 48 48" focusable="false">
          <circle className="radar-outer-ring" cx="24" cy="24" r="17" />
          <circle className="radar-inner-ring" cx="24" cy="24" r="9" />
          <path className="radar-sweep" d="M24 24 L24 7" />
          <circle className="radar-dot" cx="24" cy="24" r="3.5" />
          <circle className="radar-target" cx="32" cy="16" r="2.4" />
        </svg>
      </span>
    )
  }

  if (icon === 'drug') {
    return (
      <span className="hero-module-icon hero-module-icon-drug" aria-hidden="true">
        <svg viewBox="0 0 48 48" focusable="false">
          <g className="capsule-motion">
            <rect
              className="capsule-body"
              x="12"
              y="17"
              width="24"
              height="14"
              rx="7"
              transform="rotate(-38 24 24)"
            />
            <path className="capsule-divider" d="M20 16 L28 32" />
          </g>
          <circle className="capsule-dot capsule-dot-one" cx="34" cy="14" r="2" />
          <circle className="capsule-dot capsule-dot-two" cx="14" cy="34" r="1.7" />
        </svg>
      </span>
    )
  }

  return (
    <span className="hero-module-icon hero-module-icon-health" aria-hidden="true">
      <svg viewBox="0 0 48 48" focusable="false">
        <path className="pulse-guide" d="M6 25 H15 L19 17 L25 34 L30 22 L34 25 H42" />
        <path className="pulse-line" d="M6 25 H15 L19 17 L25 34 L30 22 L34 25 H42" />
      </svg>
    </span>
  )
}

function Hero({
  data,
  goToRecallRadar,
  goToDrugSignal,
  goToFoodRadar,
  goToAbout,
}: HeroProps) {
  const topResult = data?.results?.[0]

  const moduleActions = {
    recallradar: goToRecallRadar,
    drugsignal: goToDrugSignal,
    foodradar: goToFoodRadar,
  }

  return (
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow">Everyday safety intelligence</p>

        <h1>
          Public safety
          <br />
          data.
          <br />
          Made clear.
        </h1>

        <p className="subtitle">
          Dav AI turns public recall, drug-safety, food, and supplement data into clear,
          source-aware intelligence.
        </p>

        <p className="hero-trust-line">Public sources only • No PHI • Not medical advice</p>

        <div className="hero-module-grid" aria-label="Dav AI intelligence modules">
          {heroModules.map((module) => (
            <button
              key={module.key}
              type="button"
              className={`hero-module-card ${module.className}`}
              onClick={moduleActions[module.key]}
            >
              <HeroModuleIcon icon={module.icon} />

              <span className="hero-module-copy">
                <strong>{module.title}</strong>
                <small>{module.subtitle}</small>
              </span>
            </button>
          ))}
        </div>

        <div className="actions hero-secondary-actions">
          <button type="button" onClick={goToAbout}>
            How it works <span aria-hidden="true">→</span>
          </button>
        </div>
      </div>

      <div className="hero-visual" aria-label="Product preview">
        <div className="gradient-orb orb-a" aria-hidden="true"></div>
        <div className="gradient-orb orb-b" aria-hidden="true"></div>

        <div className="dashboard-card main-card">
          <div className="card-header" aria-hidden="true">
            <span></span>
            <span></span>
            <span></span>
          </div>

          <div className="signal-score">
            <div>
              <p>{topResult ? 'Signal score from latest search' : 'Sample signal score'}</p>
              <h2>{topResult ? topResult.risk_score.score : 82}</h2>
            </div>
            <div className="score-ring" aria-hidden="true"></div>
          </div>

          <div className="mini-chart" aria-hidden="true">
            <i></i>
            <i></i>
            <i></i>
            <i></i>
            <i></i>
            <i></i>
          </div>
        </div>

        <div className="floating-card card-one">
          <small>Recall</small>
          <strong>{topResult ? topResult.risk_score.label : 'Pattern detected'}</strong>
        </div>

        <div className="floating-card card-two">
          <small>Source</small>
          <strong>{data ? `${data.count} FDA records` : 'openFDA ready'}</strong>
        </div>

        <div className="floating-card card-three">
          <small>Audit</small>
          <strong>{data ? 'Timestamp verified' : 'Traceable results'}</strong>
        </div>
      </div>
    </section>
  )
}

export default Hero
