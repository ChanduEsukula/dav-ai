export default function AboutPage() {
  return <main id="main-content" className="portfolio-page about-page">
    <section className="about-hero page-entrance">
      <p className="eyebrow">About Dav AI</p>
      <h1>Better questions.<br />Traceable evidence.</h1>
      <p>A graduate AI portfolio project exploring how pharmaceutical research can become easier to inspect, without losing the source or its limitations.</p>
    </section>
    <div className="about-grid">
      {[
        ['01', 'Why it exists', 'A drug name is only a starting point. Formulations, package identifiers, label versions and reporting scopes can differ. Dav AI makes those distinctions visible before presenting evidence.'],
        ['02', 'What it explores', 'A full-stack research workflow combining structured SQLite evidence, BGE embeddings, FAISS semantic retrieval and a bounded local AI agent. Product confirmation comes before research.'],
        ['03', 'How answers stay grounded', 'Optional extractive answers use admitted label statements. The model selects statement IDs; Python reconstructs exact source text and attaches citations. If validation fails, structured evidence remains available.'],
        ['04', 'What remains uncertain', 'Exact quotes and resolved citations do not establish clinical completeness or question relevance. Independent claim-support reviews remain pending. The data is frozen, and missing evidence is not proof of safety.'],
      ].map(([number, title, description]) => <article className="section-reveal" key={number}><span>{number}</span><h2>{title}</h2><p>{description}</p></article>)}
    </div>
    <section className="about-section section-reveal">
      <div><p className="eyebrow">Built to be inspected</p><h2>One evidence foundation.<br />Two ways to explore.</h2></div>
      <div><p>Everyday offers a guided, spacious reading experience. Research Pro provides denser provenance and cohort organization. Both retain the same confirmation, source-admission and fallback boundaries.</p><a className="portfolio-text-link" href="/ask">Explore Ask Dav AI →</a></div>
    </section>
    <aside className="safety-note"><strong>Research, with limits.</strong><span>Dav AI is not FDA approved or medical advice. It does not diagnose, prescribe, estimate personal risk or establish that a medication caused an event. Consult a clinician or pharmacist for medical decisions.</span></aside>
  </main>
}
