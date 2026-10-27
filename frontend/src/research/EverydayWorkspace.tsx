import { SynthesisOption } from './SynthesisOption'
import type { Candidate, PublicBriefing } from './contracts'
import type { Session } from './client'
import { EverydayBriefing } from './EverydayEvidence'

interface EverydayWorkspaceProps {
  session: Session | null
  pairing: string
  setPairing: (val: string) => void
  onConnect: () => void
  query: string
  setQuery: (val: string) => void
  onSearch: () => void
  candidates: Candidate[] | null
  incomplete: boolean
  choice: string
  setChoice: (ref: string) => void
  onConfirm: () => void
  product: Candidate | null
  question: string
  setQuestion: (val: string) => void
  selectedCategories: string[]
  toggleCategory: (cat: string) => void
  model: string
  setModel: (val: string) => void
  synthesize?: boolean
  setSynthesize?: (enabled: boolean) => void
  models: string[]
  onRunResearch: () => void
  onCancelResearch: () => void
  onResetSession: () => void
  running: boolean
  attempted: boolean
  result: PublicBriefing | null
  busy: string
  error: string
}

function EverydayProductCard({ candidate }: { candidate: Candidate }) {
  return (
    <div className="everyday-candidate-item">
      <div className="candidate-primary-info">
        <strong>{candidate.brand_names.join(', ') || candidate.generic_name}</strong>
        <span className="candidate-strength">
          {candidate.strength ?? 'Strength unlisted'} · {candidate.dosage_form ?? 'Form unlisted'}
        </span>
      </div>
      <div className="candidate-secondary-info">
        <span>Route: {candidate.routes.join(', ') || 'Oral'}</span>
        <span>Product NDC: {candidate.product_ndcs.join(', ')}</span>
        {candidate.active_ingredients.length > 0 && (
          <span>Active Ingredient(s): {candidate.active_ingredients.join(', ')}</span>
        )}
      </div>
    </div>
  )
}

export default function EverydayWorkspace({
  session,
  pairing,
  setPairing,
  onConnect,
  query,
  setQuery,
  onSearch,
  candidates,
  incomplete,
  choice,
  setChoice,
  onConfirm,
  product,
  question,
  setQuestion,
  selectedCategories,
  toggleCategory,
  onRunResearch,
  synthesize,
  setSynthesize,
  onCancelResearch,
  onResetSession,
  running,
  attempted,
  result,
  busy,
  error,
}: EverydayWorkspaceProps) {
  const categoryOptions = [
    {
      id: 'labels',
      title: 'Drug labeling',
      desc: 'Official package insert, boxed warnings, precautions, and contraindications.',
    },
    {
      id: 'recalls',
      title: 'Historical recalls',
      desc: 'Enforcement actions, batch/lot recalls, and official recalling firm statements.',
    },
    {
      id: 'faers',
      title: 'FAERS reporting evidence',
      desc: 'Ingredient-level reporting associations from FAERS; not causal safety signals.',
    },
  ]

  return (
    <div className="everyday-workspace-content">
      <header className="everyday-hero">
        <span role="heading" aria-level={2} className="eyebrow">
          Ask Dav AI
        </span>
        <h1>Understand your medication information</h1>
        <p className="everyday-hero-desc">
          Explore FDA-derived drug labeling, historical recalls, and reported adverse-event evidence, with clear explanations of what the available sources can and cannot establish.
        </p>
      </header>

      {error && (
        <div role="alert" className="everyday-banner-alert">
          <strong>Notice:</strong> {error}
        </div>
      )}
      {busy && (
        <p role="status" className="everyday-banner-status">
          {busy}
        </p>
      )}

      {!session ? (
        <section className="everyday-panel everyday-connect-panel">
          <div className="connect-intro">
            <span className="step-tag">Step 1</span>
            <h2>Connect to your local research session</h2>
            <p>
              Dav AI operates securely on your local computer. Enter the pairing token printed in your terminal to begin.
            </p>
          </div>
          <form
            className="everyday-connect-form"
            onSubmit={(e) => {
              e.preventDefault()
              onConnect()
            }}
          >
            <label htmlFor="everyday-pairing">Local pairing capability</label>
            <div className="pairing-input-group">
              <input
                id="everyday-pairing"
                type="password"
                autoComplete="off"
                spellCheck={false}
                value={pairing}
                onChange={(e) => setPairing(e.target.value)}
                placeholder="Paste token from terminal (e.g. dav_pair_...)"
                required
              />
              <button
                type="submit"
                className="everyday-btn-primary"
                disabled={!!busy || !pairing.trim()}
              >
                Create local session
              </button>
            </div>
            <details className="everyday-helper-details">
              <summary>How do I start the local agent server?</summary>
              <div className="helper-content">
                <p>Run the following command in your terminal:</p>
                <code>PYTHONPATH=backend .venv/bin/python -m app.local_research</code>
                <p>Copy the pairing token displayed in your terminal output.</p>
              </div>
            </details>
          </form>
        </section>
      ) : (
        <>
          <div className="everyday-session-info-bar">
            <span>
              ✓ Connected locally · Session memory only (expires in {Math.round(session.expires_in / 60)} min)
            </span>
            <button
              type="button"
              className="everyday-btn-text"
              onClick={onResetSession}
              disabled={!!busy}
            >
              New research session
            </button>
          </div>

          <div className="everyday-stepper-container">
            {/* Step 1: Medication Selection */}
            <section className="everyday-step-card" aria-label="Step 1: Medication Selection">
              <div className="step-header">
                <span className="step-badge">1</span>
                <div>
                  <h2>{product ? 'Confirmed product' : 'Search & Select Your Medication'}</h2>
                  <p>Search by brand name, generic ingredient, or exact 10-digit National Drug Code (NDC).</p>
                </div>
              </div>

              {product ? (
                <div className="everyday-confirmed-box">
                  <div className="confirmed-check-badge">✓ Confirmed & Locked</div>
                  <EverydayProductCard candidate={product} />
                  <p className="confirmed-note">
                    Product identity is verified and locked for this research run to prevent formulation confusion.
                  </p>
                </div>
              ) : (
                <div className="everyday-search-area">
                  <form
                    role="search"
                    onSubmit={(e) => {
                      e.preventDefault()
                      onSearch()
                    }}
                  >
                    <label htmlFor="everyday-medication-input">Brand, ingredient or NDC</label>
                    <div className="everyday-search-bar">
                      <input
                        id="everyday-medication-input"
                        type="text"
                        maxLength={200}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="e.g. Xanax, Lipitor, or 0009-0029"
                        required
                      />
                      <button
                        type="submit"
                        className="everyday-btn-primary"
                        disabled={!!busy || !query.trim()}
                      >
                        Search
                      </button>
                    </div>
                  </form>

                  {candidates && (
                    <div className="everyday-candidates-area">
                      <p role="status" className="candidates-status-text">
                        {candidates.length > 0
                          ? `${candidates.length} candidate${candidates.length === 1 ? '' : 's'} · explicit confirmation required`
                          : 'No matching products in this frozen release.'}
                      </p>
                      {incomplete && (
                        <p className="incomplete-warning">
                          Search results may be incomplete. Try searching by specific NDC or formulation.
                        </p>
                      )}

                      <div className="everyday-candidates-list">
                        {candidates.map((cand) => (
                          <button
                            key={cand.product_ref}
                            type="button"
                            className={`candidate-select-btn ${choice === cand.product_ref ? 'is-selected' : ''}`}
                            aria-pressed={choice === cand.product_ref}
                            onClick={() => setChoice(cand.product_ref)}
                          >
                            <span className="selection-radio-dot" />
                            <EverydayProductCard candidate={cand} />
                          </button>
                        ))}
                      </div>

                      {candidates.length > 0 && (
                        <button
                          type="button"
                          className="everyday-btn-primary confirm-btn"
                          disabled={!choice || !!busy}
                          onClick={onConfirm}
                        >
                          Confirm selected product
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}
            </section>

            {/* Step 2: Evidence Categories & Research Question */}
            <section className="everyday-step-card" aria-label="Step 2: Evidence Scope">
              <div className="step-header">
                <span className="step-badge">2</span>
                <div>
                  <h2>Choose What to Investigate</h2>
                  <p>Select the evidence sources you want to review for your confirmed medication.</p>
                </div>
              </div>

              <div className="everyday-categories-picker">
                {categoryOptions.map((opt) => (
                  <div
                    key={opt.id}
                    className={`everyday-category-option ${selectedCategories.includes(opt.id) ? 'category-active' : ''}`}
                  >
                    <label className="everyday-check-label">
                      <input
                        type="checkbox"
                        checked={selectedCategories.includes(opt.id)}
                        disabled={running || !!busy}
                        onChange={() => toggleCategory(opt.id)}
                      />
                      {opt.title}
                    </label>
                    <span className="category-desc">{opt.desc}</span>
                  </div>
                ))}
              </div>

              <SynthesisOption enabled={synthesize} onChange={setSynthesize} disabled={running || !!busy} />
              <div className="suggested-questions" aria-label="Suggested research questions">
                <span>Try a source-focused question</span>
                {['What label warnings are available?', 'What historical recall records are available?', 'What ingredient-level FAERS reports are available?'].map(suggestion => <button type="button" key={suggestion} disabled={running || !!busy} onClick={() => setQuestion(suggestion)}>{suggestion}</button>)}
              </div>
              <div className="everyday-question-block">
                <label htmlFor="everyday-question">Your Research Question (Optional):</label>
                <textarea
                  id="everyday-question"
                  rows={2}
                  maxLength={1000}
                  value={question}
                  disabled={running || !!busy}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="e.g. What recalls or safety warnings exist for this drug?"
                />
              </div>

              <div className="everyday-actions-footer">
                <button
                  type="button"
                  className="everyday-btn-primary run-research-btn"
                  disabled={!product || selectedCategories.length === 0 || running || !!busy}
                  onClick={onRunResearch}
                >
                  {running ? 'Running Local Research…' : 'Research selected evidence'}
                </button>

                {!product && (
                  <p className="hint-text">Please search and confirm a medication above to unlock research.</p>
                )}
              </div>

              {running && (
                <div role="status" className="everyday-running-notice">
                  <div className="running-spinner" />
                  <div>
                    <strong>Research is running locally</strong>
                    <p>One bounded workflow is executing. Evidence will appear when verification finishes.</p>
                  </div>
                </div>
              )}

              {(running || (attempted && !result)) && (
                <button
                  type="button"
                  className="everyday-btn-secondary cancel-btn"
                  onClick={onCancelResearch}
                  disabled={!!busy}
                >
                  Cancel and close session
                </button>
              )}
            </section>
          </div>

          {/* Results Presentation */}
          {result && <EverydayBriefing briefing={result} />}
        </>
      )}

      <footer className="everyday-footer">
        <p>
          Dav AI is an educational pharmaceutical evidence research platform. It is not medical advice, clinical guidance, or an FDA endorsement. Stored records represent a frozen release window.
        </p>
      </footer>
    </div>
  )
}
