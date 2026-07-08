import type { RecallSearchResponse } from '../api/recalls'

type HeroProps = {
  data: RecallSearchResponse | null
  goToPharmacySafety: () => void
  goToFoodSafety: () => void
  goToCosmeticSafety: () => void
  goToAbout: () => void
}

type HeroModule = {
  title: string
  subtitle: string
  key: 'pharmacy' | 'food' | 'cosmetic'
  className: string
  icon: 'recall' | 'drug' | 'health' | 'cosmetic'
}

const heroModules: HeroModule[] = [
  {
    title: 'Drug records',
    subtitle: 'Labels, recalls, and reporting signals',
    key: 'pharmacy',
    className: 'hero-module-recall',
    icon: 'recall',
  },
  {
    title: 'Food records',
    subtitle: 'Recalls and source-backed food notices',
    key: 'food',
    className: 'hero-module-health',
    icon: 'health',
  },
  {
    title: 'Personal care records',
    subtitle: 'Cosmetic and personal-care public records',
    key: 'cosmetic',
    className: 'hero-module-cosmetic',
    icon: 'cosmetic',
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

  if (icon === 'cosmetic') {
    return (
      <span className="hero-module-icon hero-module-icon-health" aria-hidden="true">
        <svg viewBox="0 0 48 48" focusable="false">
          <circle className="pulse-guide" cx="24" cy="24" r="14" />
          <path className="pulse-line" d="M16 24 C18 16 30 16 32 24 C30 32 18 32 16 24 Z" />
          <circle className="pulse-line" cx="24" cy="24" r="3" />
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
  goToPharmacySafety,
  goToFoodSafety,
  goToCosmeticSafety,
  goToAbout,
}: HeroProps) {
  const topResult = data?.results?.[0]

  const moduleActions = {
    pharmacy: goToPharmacySafety,
    food: goToFoodSafety,
    cosmetic: goToCosmeticSafety,
  }

  return (
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow">Safety Record Search</p>

        <h1>
          Search public
          <br />
          safety records.
          <br />
          Verify the source.
        </h1>

        <p className="subtitle">
          Dav AI routes products, drugs, foods, vehicles, devices, supplements,
          and personal-care queries across selected public sources with evidence
          types, source provenance, and clear limitations.
        </p>

        <p className="hero-trust-line">
          Selected public sources • Source provenance • Not a safety verdict
        </p>

        <div className="hero-module-grid" aria-label="Safety record evidence lanes">
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

      <div className="hero-visual" aria-label="Safety Record Search preview">
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
              <p>{topResult ? 'Review priority from latest search' : 'Search public safety records'}</p>
              <h2>{topResult ? topResult.risk_score.score : '—'}</h2>
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
          <small>Evidence type</small>
          <strong>{topResult ? topResult.risk_score.label : 'Record review'}</strong>
        </div>

        <div className="floating-card card-two">
          <small>Source trail</small>
          <strong>{data ? `${data.count} public records` : 'Sources ready'}</strong>
        </div>

        <div className="floating-card card-three">
          <small>Audit context</small>
          <strong>{data ? 'Timestamp available' : 'Provenance visible'}</strong>
        </div>
      </div>
    </section>
  )
}

export default Hero