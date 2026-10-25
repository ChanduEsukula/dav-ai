import OperationalOverview from './OperationalOverview'
import { saveExperienceModePreference } from '../components/experienceState'

export default function HomePage() {
  return <main id="main-content" className="portfolio-home">
    <section className="hero" aria-labelledby="home-title">
      <div className="hero-copy page-entrance">
        <p className="eyebrow">Pharmaceutical intelligence · An academic AI project</p>
        <h1 id="home-title">Explore the evidence.<br />Keep the source.</h1>
        <p className="subtitle">From an exact medication to a clearer view of its labels, recall history and reported events. Research with local AI, and follow every answer back to the evidence.</p>
        <div className="portfolio-actions"><a className="portfolio-primary" href="/">Explore medications <span aria-hidden="true">↗</span></a><a className="portfolio-secondary" href="/ask">Ask Dav AI <span aria-hidden="true">→</span></a></div>
        <p className="hero-trust-line">Frozen FDA source data · Product confirmation · Not medical advice</p>
        <a className="portfolio-text-link" href="#workflow">See how the research works ↓</a>
      </div>
      <div className="hero-visual" role="img" aria-label="Illustration: confirmed product connects to label, recall and reporting evidence with source provenance. Not live results.">
        <div className="gradient-orb orb-a" aria-hidden="true" /><div className="gradient-orb orb-b" aria-hidden="true" />
        <div className="dashboard-card main-card" aria-hidden="true">
          <div className="card-header"><span /><span /><span /></div>
          <p className="illustration-eyebrow">The evidence trail</p>
          <div className="illustration-product"><svg viewBox="0 0 48 48"><rect x="10" y="17" width="28" height="14" rx="7" transform="rotate(-38 24 24)" /><path d="M19 16l10 16" /></svg><div><small>Start with identity</small><strong>One confirmed product</strong></div></div>
          <div className="illustration-sources"><span>Drug labeling <i>↗</i></span><span>Historical recalls <i>↗</i></span><span>Reporting evidence <i>↗</i></span></div>
          <p className="illustration-caption">Source text · Dates · Limitations</p>
        </div>
        <div className="floating-card card-one" aria-hidden="true"><small>Identity first</small><strong>Exact product + NDC</strong></div>
        <div className="floating-card card-two" aria-hidden="true"><small>Grounded selection</small><strong>Quotes, with citations</strong></div>
        <div className="floating-card card-three" aria-hidden="true"><small>Always traceable</small><strong>Follow the source</strong></div>
      </div>
    </section>
    <section className="portfolio-lanes section-reveal" aria-labelledby="lanes-title">
      <div className="portfolio-section-heading"><p className="eyebrow">Choose your perspective</p><h2 id="lanes-title">The same evidence.<br />A workspace that fits.</h2><p>Two reading experiences, with the same source boundaries.</p></div>
      <div className="portfolio-lane-grid">
        <a href="/ask" onClick={() => saveExperienceModePreference('everyday')} className="portfolio-lane lane-everyday"><span className="lane-symbol" aria-hidden="true">↗</span><small>Everyday</small><h3>A little more clarity.</h3><p>Confirm your medication, ask a focused question and explore evidence one step at a time.</p><strong>Open Everyday <span aria-hidden="true">→</span></strong></a>
        <a href="/ask" onClick={() => saveExperienceModePreference('research_pro')} className="portfolio-lane lane-pro"><span className="lane-symbol" aria-hidden="true">⌘</span><small>Research Pro</small><h3>A closer look at the source.</h3><p>Organize a research cohort and inspect product-specific evidence, provenance and coverage.</p><strong>Open Research Pro <span aria-hidden="true">→</span></strong></a>
      </div>
    </section>
    <OperationalOverview />
    <section className="portfolio-closing section-reveal"><p className="eyebrow">Evidence before conclusions</p><h2>A useful starting point.<br />An open trail back.</h2><p>Exact quotes are a starting point for review. Source completeness, clinical context and relevance still need human judgment.</p><a className="portfolio-text-link" href="/about">Why we built Dav AI →</a></section>
  </main>
}
