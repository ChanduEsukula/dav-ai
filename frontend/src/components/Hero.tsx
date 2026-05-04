import type { RecallSearchResponse } from '../api/recalls'

type HeroProps = {
  data: RecallSearchResponse | null
  goToRecallRadar: () => void
  goToAbout: () => void
}

function Hero({ data, goToRecallRadar, goToAbout }: HeroProps) {
  const topResult = data?.results?.[0]

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
          MedTrek AI turns public recall and drug-safety data into clear, source-aware
          intelligence.
        </p>

        <div className="actions">
          <button onClick={goToRecallRadar}>Search RecallRadar</button>
          <button onClick={goToAbout}>How it works</button>
        </div>
      </div>

      <div className="hero-visual" aria-label="Animated product preview">
        <div className="gradient-orb orb-a"></div>
        <div className="gradient-orb orb-b"></div>

        <div className="dashboard-card main-card">
          <div className="card-header">
            <span></span>
            <span></span>
            <span></span>
          </div>

          <div className="signal-score">
            <div>
              <p>{topResult ? 'Live signal score' : 'Signal score'}</p>
              <h2>{topResult ? topResult.risk_score.score : 82}</h2>
            </div>
            <div className="score-ring"></div>
          </div>

          <div className="mini-chart">
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