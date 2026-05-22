function AboutPage() {
  return (
    <section className="about-page reveal">
      <div className="about-hero">
        <p className="eyebrow">About Dav AI</p>
        <h2>Healthcare safety intelligence from public FDA signals.</h2>
        <p>
          Dav AI is a full-stack public safety intelligence platform that turns
          fragmented recall and adverse-event data into clear, source-aware review
          workflows. The current MVP includes RecallRadar, DrugSignal, and a deterministic
          Safety Briefing Engine v1 powered by public openFDA data.
        </p>
      </div>

      <div className="about-grid">
        <article>
          <span>01</span>
          <h3>What the app does</h3>
          <p>
            Dav AI helps users search public FDA recall records, explore FAERS
            adverse-event reporting patterns, review source metadata, and generate
            role-based safety briefings grounded in structured public data.
          </p>
        </article>

        <article>
          <span>02</span>
          <h3>What the app does not do</h3>
          <p>
            It does not diagnose conditions, recommend treatment, replace clinicians,
            claim FAERS causation, or tell users to start, stop, or change medication.
            It is an information and review workflow, not a medical decision system.
          </p>
        </article>

        <article>
          <span>03</span>
          <h3>Data source transparency</h3>
          <p>
            Current workflows use public openFDA Drug Enforcement and Drug Event data.
            Each result keeps source details visible, including retrieval timestamp,
            source name, endpoint, audit ID, transform version, and technical audit context.
          </p>
        </article>

        <article>
          <span>04</span>
          <h3>Safety Briefing Engine v1</h3>
          <p>
            The briefing engine creates deterministic role-based summaries for consumers,
            pharmacies, clinics, and public-health analysts. It uses structured API response
            data only and keeps limitations visible.
          </p>
        </article>
      </div>

      <div className="about-section">
        <div>
          <p className="eyebrow">Product positioning</p>
          <h3>Not another health app. A source-audited safety workflow.</h3>
        </div>
        <p>
          Dav AI is designed for users who need to review public safety information
          without manually searching multiple government portals. The current system focuses
          on RecallRadar, DrugSignal, role-based briefings, source transparency, and audit
          persistence. Future phases may add saved monitors, alert workflows, audit history,
          deployment hardening, and carefully scoped ML/NLP features.
        </p>
      </div>

      <div className="audience-grid">
        <article>
          <h4>Consumers</h4>
          <p>Search a product or drug and understand whether public recall records exist.</p>
        </article>
        <article>
          <h4>Pharmacies</h4>
          <p>Review recall and FAERS reporting patterns with source details and checklist items.</p>
        </article>
        <article>
          <h4>Clinics</h4>
          <p>Prepare patient-facing safety communication based on public data, not guesses.</p>
        </article>
        <article>
          <h4>Public-health teams</h4>
          <p>Track what source was used, when it was retrieved, and why a signal needs review.</p>
        </article>
      </div>

      <div className="safety-note">
        <strong>Important safety boundary:</strong>
        <span>
          Dav AI is not FDA approved, not medical advice, and not a replacement for FDA,
          CDC, clinician, pharmacist, or emergency guidance. FAERS reports are safety signals
          only and do not prove causation.
        </span>
      </div>
    </section>
  )
}

export default AboutPage