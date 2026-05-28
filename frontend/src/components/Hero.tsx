import type { RecallSearchResponse } from '../api/recalls'

type HeroProps = {
  data: RecallSearchResponse | null
  goToRecallRadar: () => void
  goToDrugSignal: () => void
  goToHealthPulse: () => void
  goToAbout: () => void
}

const heroModules = [
  {
    title: 'RecallRadar',
    description: 'Search public FDA recall records with source-aware review scoring.',
    actionLabel: 'Search recalls',
    key: 'recallradar',
  },
  {
    title: 'DrugSignal',
    description: 'Explore public FAERS adverse-event reporting patterns.',
    actionLabel: 'Explore FAERS',
    key: 'drugsignal',
  },
  {
    title: 'Health Pulse',
    description: 'Preview sample regional public-data signal reviews.',
    actionLabel: 'Review samples',
    key: 'health-pulse',
  },
] as const

function Hero({
  data,
  goToRecallRadar,
  goToDrugSignal,
  goToHealthPulse,
  goToAbout,
}: HeroProps) {
  const topResult = data?.results?.[0]

  const moduleActions = {
    recallradar: goToRecallRadar,
    drugsignal: goToDrugSignal,
    'health-pulse': goToHealthPulse,
  }

  return (
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow">Public health intelligence</p>

        <h1>
          Public safety
          <br />
          data.
          <br />
          Made clear.
        </h1>

        <p className="subtitle">
          Dav AI turns public recall, drug-safety, and regional signal data into
          clear, source-aware intelligence.
        </p>

        <p className="hero-trust-line">
          Public sources only • No PHI • Not medical advice
        </p>

        <div className="hero-module-grid" aria-label="Dav AI intelligence modules">
          {heroModules.map((module) => (
            <button
              key={module.key}
              type="button"
              className="hero-module-card"
              onClick={moduleActions[module.key]}
            >
              <span>{module.title}</span>
              <strong>{module.description}</strong>
              <small>{module.actionLabel}</small>
            </button>
          ))}
        </div>

        <div className="actions hero-secondary-actions">
          <button type="button" onClick={goToAbout}>
            How it works
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