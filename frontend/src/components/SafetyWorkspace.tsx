type SafetyWorkspaceProps = {
  goToRecallRadar: () => void
  goToDrugSignal: () => void
  goToHealthPulse: () => void
}

function SafetyWorkspace({
  goToRecallRadar,
  goToDrugSignal,
  goToHealthPulse,
}: SafetyWorkspaceProps) {
  return (
    <section className="safety-workspace" aria-label="Safety intelligence workspace">
      <div className="safety-workspace__header">
        <p className="eyebrow">Safety intelligence workspace</p>
        <h2>Two connected lenses for source-backed safety review.</h2>
        <p>
          Start with official recall records, then compare adverse-event reporting patterns.
          Dav AI keeps public sources, audit trails, and medical-safety boundaries visible.
        </p>
      </div>

      <div className="safety-workspace__tabs" aria-label="Safety modules">
        <button type="button" onClick={goToRecallRadar}>
          RecallRadar
        </button>

        <button type="button" onClick={goToDrugSignal}>
          DrugSignal
        </button>

        <button type="button" onClick={goToHealthPulse}>
          Health Pulse
        </button>
      </div>

      <div className="safety-workspace__grid">
        <article className="safety-workspace-card safety-workspace-card--recall">
          <div className="safety-workspace-card__topline">
            <div className="safety-workspace-card__icon" aria-hidden="true">
              <svg viewBox="0 0 48 48" focusable="false">
                <circle cx="24" cy="24" r="17" />
                <circle cx="24" cy="24" r="9" />
                <path d="M24 24 L24 7" />
                <circle cx="32" cy="16" r="2.4" />
              </svg>
            </div>

            <span className="safety-workspace-card__pill">Official FDA records</span>
          </div>

          <div>
            <p className="eyebrow">Official recall lens</p>
            <h3>RecallRadar</h3>
            <p>
              Review public FDA recall records, risk score, firm, status, recall date, and
              source-backed safety guidance.
            </p>
          </div>

          <div className="safety-workspace-card__meta">
            <span>Recall score</span>
            <span>FDA class</span>
            <span>Audit trail</span>
          </div>

          <button type="button" onClick={goToRecallRadar}>
            Open RecallRadar <span aria-hidden="true">→</span>
          </button>
        </article>

        <article className="safety-workspace-card safety-workspace-card--drug">
          <div className="safety-workspace-card__topline">
            <div className="safety-workspace-card__icon" aria-hidden="true">
              <svg viewBox="0 0 48 48" focusable="false">
                <rect
                  x="12"
                  y="17"
                  width="24"
                  height="14"
                  rx="7"
                  transform="rotate(-38 24 24)"
                />
                <path d="M20 16 L28 32" />
                <circle cx="34" cy="14" r="2" />
                <circle cx="14" cy="34" r="1.7" />
              </svg>
            </div>

            <span className="safety-workspace-card__pill">Public FAERS patterns</span>
          </div>

          <div>
            <p className="eyebrow">Adverse-event lens</p>
            <h3>DrugSignal</h3>
            <p>
              Explore public FAERS reporting patterns, top reactions, trend snapshot, reaction
              categories, and deterministic signal score.
            </p>
          </div>

          <div className="safety-workspace-card__meta">
            <span>Signal score</span>
            <span>Top reactions</span>
            <span>Trend snapshot</span>
          </div>

          <button type="button" onClick={goToDrugSignal}>
            Open DrugSignal <span aria-hidden="true">→</span>
          </button>
        </article>
      </div>

      <div className="safety-workspace__bridge">
        <strong>Recommended workflow:</strong>
        <span>
          Use RecallRadar for official recall context, then use DrugSignal to review broader public
          adverse-event reporting patterns.
        </span>
      </div>
    </section>
  )
}

export default SafetyWorkspace