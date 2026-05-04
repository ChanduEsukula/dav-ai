function AboutPage() {
  return (
    <section className="about-page reveal">
      <div className="about-hero">
        <p className="eyebrow">About MedTrek AI</p>
        <h2>Healthcare safety intelligence from public FDA signals.</h2>
        <p>
          MedTrek AI is a full-stack public safety intelligence platform that turns
          fragmented recall and drug-safety data into clear, source-aware review workflows.
          The current MVP focuses on RecallRadar, a live FDA recall search experience powered
          by public openFDA enforcement data.
        </p>
      </div>

      <div className="about-grid">
        <article>
          <span>01</span>
          <h3>What the app does</h3>
          <p>
            MedTrek AI helps users search public recall records, review FDA classification,
            check recall status, understand recall timing, and inspect audit details from the
            source response.
          </p>
        </article>

        <article>
          <span>02</span>
          <h3>What the app does not do</h3>
          <p>
            It does not diagnose conditions, recommend treatment, replace clinicians, or tell
            users to start, stop, or change medication. It is an information and review tool,
            not a medical decision system.
          </p>
        </article>

        <article>
          <span>03</span>
          <h3>Data source transparency</h3>
          <p>
            The current workflow uses public openFDA recall/enforcement data. Each result keeps
            source details visible, including retrieval timestamp, source name, score version,
            and technical audit context.
          </p>
        </article>

        <article>
          <span>04</span>
          <h3>Recall Review Score</h3>
          <p>
            The score is a review-priority signal. It combines recall class, status, recency,
            scope, and confidence into a simple number so users can identify which public
            records deserve closer review.
          </p>
        </article>
      </div>

      <div className="about-section">
        <div>
          <p className="eyebrow">Product positioning</p>
          <h3>Not another health app. A source-audited safety workflow.</h3>
        </div>
        <p>
          MedTrek AI is designed for users who need to review public safety information
          without manually searching multiple government portals. The long-term vision includes
          DrugSignal for adverse-event patterns, role-based briefings, saved monitors, and
          source-audited safety dashboards.
        </p>
      </div>

      <div className="audience-grid">
        <article>
          <h4>Consumers</h4>
          <p>Search a product or drug and understand whether public recall records exist.</p>
        </article>
        <article>
          <h4>Pharmacies</h4>
          <p>Review recall signals, affected products, source details, and staff checklist items.</p>
        </article>
        <article>
          <h4>Clinics</h4>
          <p>Prepare patient-facing safety communication based on public data, not guesses.</p>
        </article>
        <article>
          <h4>Public-health teams</h4>
          <p>Track what changed, where the data came from, and why a signal matters.</p>
        </article>
      </div>

      <div className="safety-note">
        <strong>Important safety boundary:</strong>
        <span>
          MedTrek AI is not FDA approved, not medical advice, and not a replacement for FDA,
          CDC, clinician, pharmacist, or emergency guidance.
        </span>
      </div>
    </section>
  )
}

export default AboutPage