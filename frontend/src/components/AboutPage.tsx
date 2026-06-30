function AboutPage() {
  return (
    <section className="about-page reveal">
      <div className="about-hero">
        <p className="eyebrow">About Dav AI</p>
        <h2>Public safety intelligence with source boundaries.</h2>
        <p>
          Dav AI is a full-stack public safety intelligence platform that routes product,
          drug, food, vehicle, device, supplement, and personal-care queries across selected
          public safety sources. It separates recalls from adverse-event signals, reference
          records, labels, outbreak context, source freshness, and audit trails so users can
          inspect what was checked and what cannot be concluded.
        </p>
      </div>

      <div className="about-grid">
        <article>
          <span>01</span>
          <h3>What the app does</h3>
          <p>
            Dav AI helps users search public safety records, review specialized evidence
            lanes like DrugSignal and FoodSignal, inspect Personal Care Signals, save
            repeatable monitors, and generate bounded explanations grounded in the current
            visible result context.
          </p>
        </article>

        <article>
          <span>02</span>
          <h3>What the app does not do</h3>
          <p>
            It does not diagnose conditions, recommend treatment, replace clinicians,
            provide legal or emergency guidance, prove causation, or decide that a product,
            drug, food, vehicle, device, supplement, or cosmetic is safe or unsafe.
          </p>
        </article>

        <article>
          <span>03</span>
          <h3>Source transparency</h3>
          <p>
            Workflows keep source details visible, including source name, endpoint,
            retrieval timestamp, integration mode, audit ID, transform version, and
            source-specific limitations where available.
          </p>
        </article>

        <article>
          <span>04</span>
          <h3>Bounded explanation layer</h3>
          <p>
            Explain These Results uses structured page context, source metadata, audit
            details, scores, and limitations. It is designed to explain retrieved public
            records, not to create medical, legal, or regulatory conclusions.
          </p>
        </article>
      </div>

      <div className="about-section">
        <div>
          <p className="eyebrow">Product positioning</p>
          <h3>Not a safety verdict. A source-grounded review workspace.</h3>
        </div>
        <p>
          Dav AI is designed for users who need a clearer starting point for public safety
          review without manually searching many government portals. The curated workspace
          centers on Safety Search, DrugSignal, FoodSignal, Personal Care Signals, Monitors,
          and Sources & Audit. Future phases may add stronger adverse-event signal timelines,
          production alert delivery, authentication/RBAC, deployment hardening, and carefully
          scoped ML/NLP features.
        </p>
      </div>

      <div className="audience-grid">
        <article>
          <h4>Consumers</h4>
          <p>Search a product and see which public safety sources returned matching records.</p>
        </article>
        <article>
          <h4>Pharmacies</h4>
          <p>Review drug recalls and public adverse-event reporting signals with source context.</p>
        </article>
        <article>
          <h4>Food and safety teams</h4>
          <p>Compare food recalls, USDA FSIS records, outbreak context, and public-data limits.</p>
        </article>
        <article>
          <h4>Engineers and reviewers</h4>
          <p>Inspect provenance, source freshness, audit trails, and bounded AI behavior.</p>
        </article>
      </div>

      <div className="safety-note">
        <strong>Important safety boundary:</strong>
        <span>
          Dav AI is not FDA approved, not medical advice, not legal advice, and not a replacement
          for FDA, CDC, USDA, CPSC, NHTSA, clinician, pharmacist, or emergency guidance.
          Adverse-event reports are public reporting signals only and do not prove causation.
          No matching result does not prove that something is safe.
        </span>
      </div>
    </section>
  )
}

export default AboutPage