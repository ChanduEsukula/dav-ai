import { SynthesisOption } from './SynthesisOption'
import { useMemo, useState } from 'react'
import type { Candidate, PublicBriefing } from './contracts'
import type { Session } from './client'
import { Briefing } from './Evidence'
import {
  type CohortItem,
  type EvidenceStatus,
  MAX_COHORT_LIMIT,
  createCohortItemFromCandidate,
} from './cohort'

interface ResearchProWorkspaceProps {
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
  cohort: CohortItem[]
  setCohort: React.Dispatch<React.SetStateAction<CohortItem[]>>
  onSelectForDeepResearch: (item: CohortItem) => void
}

const modelNames: Record<string, string> = {
  'llama3.2:3b': 'Llama 3.2 3B (Q4_K_M · 2.0 GB)',
  'qwen3.5:4b-q4_K_M': 'Qwen 3.5 4B (Q4_K_M · 3.3 GB)',
}

export default function ResearchProWorkspace({
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
  model,
  setModel,
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
  cohort,
  setCohort,
  onSelectForDeepResearch,
}: ResearchProWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<'cohort' | 'deep_research'>('cohort')
  const [cohortFilter, setCohortFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'EVALUATED' | 'NOT_EVALUATED'>('ALL')
  const [cohortNotice, setCohortNotice] = useState<string | null>(null)
  const [sortField, setSortField] = useState<'name' | 'ndc' | 'status'>('name')
  const [sortAsc, setSortAsc] = useState(true)

  // Add Candidate to Cohort
  const handleAddToCohort = (candidate: Candidate) => {
    setCohortNotice(null)
    const primaryNdc = candidate.product_ndcs[0] || candidate.product_ref

    // Check duplicate
    if (cohort.some((item) => item.product_ndcs.includes(primaryNdc) || item.id === primaryNdc)) {
      setCohortNotice(`Product with NDC ${primaryNdc} is already in the research cohort.`)
      return
    }

    // Check max limit 50
    if (cohort.length >= MAX_COHORT_LIMIT) {
      setCohortNotice(`Cohort limit reached: maximum ${MAX_COHORT_LIMIT} products allowed.`)
      return
    }

    const newItem = createCohortItemFromCandidate(candidate)
    setCohort((prev) => [newItem, ...prev])
    setCohortNotice(`Added ${candidate.brand_names[0] || candidate.generic_name} to research cohort.`)
  }

  // Remove Candidate from Cohort
  const handleRemoveFromCohort = (id: string) => {
    setCohort((prev) => prev.filter((item) => item.id !== id))
    setCohortNotice(null)
  }

  // Clear Cohort
  const handleClearCohort = () => {
    if (window.confirm('Clear all products from the current research cohort?')) {
      setCohort([])
      setCohortNotice('Cohort cleared.')
    }
  }

  // Launch Deep Research from Cohort Item
  const handleLaunchDeepResearch = (item: CohortItem) => {
    setActiveTab('deep_research')
    setCohortNotice(`Selected ${item.brand_names[0] || item.generic_name} (${item.product_ndcs[0]}). Changing confirmed products requires a new local session and explicit confirmation.`)
    onSelectForDeepResearch(item)
  }

  // Filter and Sort Cohort
  const filteredCohort = useMemo(() => {
    return cohort
      .filter((item) => {
        if (statusFilter === 'EVALUATED' && item.last_research_status === 'Not evaluated') return false
        if (statusFilter === 'NOT_EVALUATED' && item.last_research_status !== 'Not evaluated') return false
        if (!cohortFilter.trim()) return true
        const term = cohortFilter.toLowerCase()
        return (
          item.brand_names.some((b) => b.toLowerCase().includes(term)) ||
          (item.generic_name && item.generic_name.toLowerCase().includes(term)) ||
          item.product_ndcs.some((ndc) => ndc.includes(term)) ||
          item.active_ingredients.some((ing) => ing.toLowerCase().includes(term))
        )
      })
      .sort((a, b) => {
        const valA =
          sortField === 'name'
            ? a.brand_names[0] || a.generic_name || ''
            : sortField === 'ndc'
              ? a.product_ndcs[0] || ''
              : a.last_research_status
        const valB =
          sortField === 'name'
            ? b.brand_names[0] || b.generic_name || ''
            : sortField === 'ndc'
              ? b.product_ndcs[0] || ''
              : b.last_research_status
        return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA)
      })
  }, [cohort, cohortFilter, statusFilter, sortField, sortAsc])

  const renderStatusBadge = (status: EvidenceStatus) => {
    const classMap: Record<EvidenceStatus, string> = {
      Available: 'badge-status-available',
      Partial: 'badge-status-partial',
      Incomplete: 'badge-status-incomplete',
      Unavailable: 'badge-status-unavailable',
      'Not evaluated': 'badge-status-not-evaluated',
      Error: 'badge-status-error',
    }
    return <span className={`pro-status-badge ${classMap[status]}`}>{status}</span>
  }

  return (
    <div className="pro-workspace-container">
      {/* Header */}
      <header className="pro-header-bar">
        <div>
          <span role="heading" aria-level={2} className="eyebrow">
            Ask Dav AI · Research Pro
          </span>
          <h1>Pharmaceutical Evidence Workspace</h1>
          <p className="pro-subtitle">
            Investigate product-specific labeling, historical recall applicability, and ingredient-level FAERS associations across a selected research cohort.
          </p>
        </div>
        <div className="pro-header-meta">
          <span className="pro-badge-release">Release: phase4b-communications-2026-10-06</span>
          <span className="pro-badge-security">Gate: publication_authorized=false</span>
        </div>
      </header>

      {/* Connection Panel if not paired */}
      {!session ? (
        <section className="pro-panel pro-connect-box">
          <div className="pro-connect-header">
            <h2>Pair Local Capabilities</h2>
            <p>
              Loopback API connection required at <code>http://127.0.0.1:8001</code>. Enter the ephemeral pairing capability issued by the local launcher.
            </p>
            {cohortNotice && <p role="status">{cohortNotice}</p>}
            {error && <p role="alert" className="pro-alert-danger">{error}</p>}
          </div>
          <form
            className="pro-connect-form"
            onSubmit={(e) => {
              e.preventDefault()
              onConnect()
            }}
          >
            <div className="pro-input-row">
              <label htmlFor="pro-pairing-input" className="sr-only">
                Local pairing capability
              </label>
              <input
                id="pro-pairing-input"
                type="password"
                autoComplete="off"
                spellCheck={false}
                value={pairing}
                onChange={(e) => setPairing(e.target.value)}
                placeholder="Paste the capability from your local launcher"
                required
              />
              <button
                type="submit"
                className="pro-btn-cyan"
                disabled={!!busy || !pairing.trim()}
              >
                Pair Local Session
              </button>
            </div>
          </form>
          <details className="pro-details-box">
            <summary>Startup Command</summary>
            <code>PYTHONPATH=backend .venv/bin/python -m app.local_research</code>
          </details>
        </section>
      ) : (
        <>
          {/* Active Session Info Bar */}
          <div className="pro-session-bar">
            <div className="pro-session-telemetry">
              <span className="telemetry-pill">
                <span className="pulse-dot" /> Session Active
              </span>
              <span className="telemetry-item">
                Lifetime: {Math.round(session.expires_in / 60)} min
              </span>
              <span className="telemetry-item">
                Inference: {session.model_runtime === 'available' ? 'Ollama Online' : 'Deterministic Only'}
              </span>
              <span className="telemetry-item">
                Cohort Size: <strong>{cohort.length}</strong> / {MAX_COHORT_LIMIT} products
              </span>
            </div>
            <button
              type="button"
              className="pro-btn-outline"
              onClick={onResetSession}
              disabled={!!busy}
            >
              Reset Session
            </button>
          </div>

          {error && (
            <div role="alert" className="pro-alert-danger">
              <strong>Error:</strong> {error}
            </div>
          )}
          {busy && (
            <div role="status" className="pro-alert-info">
              {busy}
            </div>
          )}
          {cohortNotice && (
            <div role="status" className="pro-alert-notice">
              {cohortNotice}
            </div>
          )}

          {/* Workspace Tabs */}
          <nav className="pro-workspace-tabs" aria-label="Research Workspace Modes">
            <button
              type="button"
              className={`pro-tab-btn ${activeTab === 'cohort' ? 'is-active' : ''}`}
              aria-pressed={activeTab === 'cohort'}
              onClick={() => setActiveTab('cohort')}
            >
              📋 Cohort Investigation & Overview ({cohort.length}/{MAX_COHORT_LIMIT})
            </button>
            <button
              type="button"
              className={`pro-tab-btn ${activeTab === 'deep_research' ? 'is-active' : ''}`}
              aria-pressed={activeTab === 'deep_research'}
              onClick={() => setActiveTab('deep_research')}
            >
              🔬 Deep Single-Product Research {product ? `(${product.brand_names[0] || product.generic_name})` : ''}
            </button>
          </nav>

          {/* TAB 1: COHORT INVESTIGATION */}
          {activeTab === 'cohort' && (
            <div className="pro-cohort-workspace">
              {/* Left Column: Search & Add to Cohort */}
              <div className="pro-grid-split">
                <section className="pro-panel pro-cohort-builder" aria-label="Cohort Builder">
                  <div className="panel-title-bar">
                    <h2>Cohort Builder</h2>
                    <span className="cohort-counter-badge">
                      {cohort.length} / {MAX_COHORT_LIMIT} selected
                    </span>
                  </div>

                  <p className="panel-instruction">
                    Search frozen FDA directory to select up to 50 specific pharmaceutical products for cohort analysis.
                  </p>

                  <form
                    role="search"
                    onSubmit={(e) => {
                      e.preventDefault()
                      onSearch()
                    }}
                  >
                    <label htmlFor="pro-medication-input">Search Product by Name, Ingredient or NDC</label>
                    <div className="pro-search-row">
                      <input
                        id="pro-medication-input"
                        type="text"
                        maxLength={200}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="e.g. Xanax, Metformin, 0009-0029"
                        required
                      />
                      <button
                        type="submit"
                        className="pro-btn-cyan"
                        disabled={!!busy || !query.trim()}
                      >
                        Search Directory
                      </button>
                    </div>
                  </form>

                  {/* Candidate Search Results */}
                  {candidates && (
                    <div className="pro-candidate-results">
                      <p className="candidate-count-summary">
                        Found {candidates.length} candidate record{candidates.length === 1 ? '' : 's'}.
                      </p>
                      {incomplete && (
                        <p className="pro-warning-text">
                          Directory match incomplete. Filter by 10-digit NDC for exact package targeting.
                        </p>
                      )}

                      <div className="pro-candidates-scroll">
                        {candidates.map((cand) => {
                          const primaryNdc = cand.product_ndcs[0] || cand.product_ref
                          const inCohort = cohort.some(
                            (c) => c.product_ndcs.includes(primaryNdc) || c.id === primaryNdc
                          )
                          return (
                            <div className="pro-candidate-row" key={cand.product_ref}>
                              <div className="cand-info">
                                <strong>{cand.brand_names.join(', ') || cand.generic_name}</strong>
                                <span className="cand-specs">
                                  {cand.strength ?? 'Strength unlisted'} · {cand.dosage_form ?? 'Form unlisted'}
                                </span>
                                <span className="cand-ndc">
                                  NDC: {cand.product_ndcs.join(', ')} · Packages: {cand.package_ndcs.join(', ') || 'None'}
                                </span>
                              </div>
                              <button
                                type="button"
                                className={`pro-btn-sm ${inCohort ? 'btn-already-added' : 'btn-add-cohort'}`}
                                disabled={inCohort || cohort.length >= MAX_COHORT_LIMIT || !!busy}
                                onClick={() => handleAddToCohort(cand)}
                              >
                                {inCohort ? 'In Cohort' : '+ Add to Cohort'}
                              </button>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </section>

                {/* Right Column: Selected Cohort Tray */}
                <section className="pro-panel pro-cohort-tray" aria-label="Selected Cohort Tray">
                  <div className="panel-title-bar">
                    <h2>Active Research Cohort</h2>
                    <div className="tray-action-group">
                      <button
                        type="button"
                        className="pro-btn-sm-danger"
                        disabled={cohort.length === 0}
                        onClick={handleClearCohort}
                      >
                        Clear Cohort
                      </button>
                    </div>
                  </div>

                  {cohort.length === 0 ? (
                    <div className="pro-empty-tray">
                      <p>No products in research cohort.</p>
                      <span>Search on the left to add up to 50 pharmaceutical products for comparison.</span>
                    </div>
                  ) : (
                    <div className="pro-tray-list">
                      <div className="cohort-progress-container">
                        <div
                          className="cohort-progress-bar"
                          style={{ width: `${(cohort.length / MAX_COHORT_LIMIT) * 100}%` }}
                        />
                      </div>

                      <div className="pro-tray-chips">
                        {cohort.map((item) => (
                          <div className="cohort-chip" key={item.id}>
                            <div className="chip-text">
                              <span className="chip-title">
                                {item.brand_names[0] || item.generic_name}
                              </span>
                              <span className="chip-ndc">{item.product_ndcs[0]}</span>
                            </div>
                            <button
                              type="button"
                              className="chip-remove-btn"
                              aria-label={`Remove ${item.brand_names[0] || item.generic_name} from cohort`}
                              onClick={() => handleRemoveFromCohort(item.id)}
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </section>
              </div>

              {/* Batch Evidence Overview Table */}
              <section className="pro-panel pro-cohort-table-section" aria-label="Batch Evidence Overview">
                <div className="table-controls-bar">
                  <div className="table-heading-group">
                    <h2>Batch Evidence Overview</h2>
                    <span className="table-subheading">
                      Scientific evidence status across selected cohort ({filteredCohort.length} records shown)
                    </span>
                  </div>

                  <div className="table-filters-group">
                    <input
                      type="text"
                      className="table-search-input"
                      placeholder="Filter cohort products..."
                      value={cohortFilter}
                      onChange={(e) => setCohortFilter(e.target.value)}
                    />
                    <select
                      className="table-status-select"
                      value={statusFilter}
                      onChange={(e) =>
                        setStatusFilter(
                          e.target.value as 'ALL' | 'EVALUATED' | 'NOT_EVALUATED'
                        )
                      }
                    >
                      <option value="ALL">All Statuses</option>
                      <option value="EVALUATED">Evaluated Only</option>
                      <option value="NOT_EVALUATED">Not Evaluated Only</option>
                    </select>
                  </div>
                </div>

                {/* Honest Batch Boundary Callout */}
                <div className="pro-boundary-callout" role="note">
                  <span className="callout-icon" aria-hidden="true">ℹ️</span>
                  <div>
                    <strong>Batch Execution Boundary Notice:</strong>
                    <p>
                      Dav AI operates with single-session local capabilities and process sandboxing to protect host resources. Simultaneous 50-product background agent execution is not enabled in single-session mode. You can evaluate cohort products individually using <strong>Deep Research</strong>. Statuses remain strictly <code>Not evaluated</code> until verified.
                    </p>
                  </div>
                </div>

                {/* The Responsive Table */}
                <div className="pro-table-wrapper">
                  <table className="pro-data-table">
                    <thead>
                      <tr>
                        <th
                          scope="col"
                          onClick={() => {
                            setSortField('name')
                            setSortAsc(!sortAsc)
                          }}
                          className="sortable-col"
                        >
                          Product Identity {sortField === 'name' ? (sortAsc ? '▲' : '▼') : ''}
                        </th>
                        <th
                          scope="col"
                          onClick={() => {
                            setSortField('ndc')
                            setSortAsc(!sortAsc)
                          }}
                          className="sortable-col"
                        >
                          Product NDC {sortField === 'ndc' ? (sortAsc ? '▲' : '▼') : ''}
                        </th>
                        <th scope="col">Label Evidence</th>
                        <th scope="col">Recall Actions</th>
                        <th scope="col">FAERS Signals</th>
                        <th
                          scope="col"
                          onClick={() => {
                            setSortField('status')
                            setSortAsc(!sortAsc)
                          }}
                          className="sortable-col"
                        >
                          Research Status {sortField === 'status' ? (sortAsc ? '▲' : '▼') : ''}
                        </th>
                        <th scope="col">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredCohort.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="table-empty-cell">
                            {cohort.length === 0
                              ? 'Cohort is empty. Add products above to begin cohort investigation.'
                              : 'No products match the active filter criteria.'}
                          </td>
                        </tr>
                      ) : (
                        filteredCohort.map((item) => (
                          <tr key={item.id}>
                            <td className="cell-product-identity">
                              <strong>{item.brand_names.join(', ') || item.generic_name}</strong>
                              <span className="cell-sub-specs">
                                {item.strength ?? 'Strength unlisted'} · {item.dosage_form ?? 'Form unlisted'}
                              </span>
                            </td>
                            <td className="cell-ndc">
                              <code>{item.product_ndcs.join(', ')}</code>
                            </td>
                            <td>{renderStatusBadge(item.label_status)}</td>
                            <td>{renderStatusBadge(item.recall_status)}</td>
                            <td>{renderStatusBadge(item.faers_status)}</td>
                            <td>{renderStatusBadge(item.last_research_status)}</td>
                            <td className="cell-actions">
                              <button
                                type="button"
                                className="pro-btn-table-action"
                                disabled={!!busy || item.product_ndcs.length === 0}
                                onClick={() => handleLaunchDeepResearch(item)}
                              >
                                Deep Research →
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          )}

          {/* TAB 2: DEEP SINGLE-PRODUCT RESEARCH */}
          {activeTab === 'deep_research' && (
            <div className="pro-deep-workspace">
              <div className="pro-deep-grid">
                {/* Step 1: Identity & Selection */}
                <section className="pro-panel" aria-label="Product Confirmation">
                  <div className="panel-title-bar">
                    <span className="step-tag">Step 01</span>
                    <h2>Exact Product Identity</h2>
                  </div>

                  {product ? (
                    <div className="pro-confirmed-card">
                      <div className="pro-confirmed-badge">✓ Product Identity Locked</div>
                      <h3>{product.brand_names.join(', ') || product.generic_name}</h3>
                      <p className="confirmed-specs">
                        {product.strength} · {product.dosage_form} · {product.routes.join(', ')}
                      </p>
                      <div className="confirmed-ndcs">
                        <span><strong>Product NDC:</strong> {product.product_ndcs.join(', ')}</span>
                        <span><strong>Package NDCs:</strong> {product.package_ndcs.join(', ') || 'None'}</span>
                        <span><strong>Active Ingredients:</strong> {product.active_ingredients.join(', ')}</span>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <p className="pro-instruction-text">
                        Deep research requires explicit human confirmation of exact National Drug Code (NDC).
                      </p>
                      <form
                        role="search"
                        onSubmit={(e) => {
                          e.preventDefault()
                          onSearch()
                        }}
                      >
                        <label htmlFor="pro-deep-search-input">Search Medication to Confirm:</label>
                        <div className="pro-search-row">
                          <input
                            id="pro-deep-search-input"
                            type="text"
                            maxLength={200}
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="e.g. Xanax, Lipitor or NDC"
                            required
                          />
                          <button
                            type="submit"
                            className="pro-btn-cyan"
                            disabled={!!busy || !query.trim()}
                          >
                            Find Candidate
                          </button>
                        </div>
                      </form>

                      {candidates && (
                        <div className="pro-deep-candidates">
                          <p role="status">
                            {candidates.length} candidate formulation{candidates.length === 1 ? '' : 's'}. Explicit confirmation required:
                          </p>
                          <div className="pro-candidates-scroll">
                            {candidates.map((cand) => (
                              <button
                                key={cand.product_ref}
                                type="button"
                                className={`pro-candidate-btn ${choice === cand.product_ref ? 'is-active' : ''}`}
                                aria-pressed={choice === cand.product_ref}
                                onClick={() => setChoice(cand.product_ref)}
                              >
                                <strong>{cand.brand_names.join(', ') || cand.generic_name}</strong>
                                <span>{cand.strength} · {cand.dosage_form} · NDC: {cand.product_ndcs.join(', ')}</span>
                              </button>
                            ))}
                          </div>
                          {candidates.length > 0 && (
                            <button
                              type="button"
                              className="pro-btn-cyan confirm-btn-full"
                              disabled={!choice || !!busy}
                              onClick={onConfirm}
                            >
                              Confirm Exact Product
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </section>

                {/* Step 2: Scope, Model & Execution */}
                <section className="pro-panel" aria-label="Investigation Scope & Inference">
                  <div className="panel-title-bar">
                    <span className="step-tag">Step 02</span>
                    <h2>Scope & Execution Engine</h2>
                  </div>

                  <form
                    onSubmit={(e) => {
                      e.preventDefault()
                      onRunResearch()
                    }}
                  >
                    <div className="pro-form-group">
                      <label htmlFor="pro-question-textarea">Research Question / Query Intent:</label>
                      <textarea
                        id="pro-question-textarea"
                        rows={3}
                        maxLength={2000}
                        value={question}
                        disabled={running || attempted}
                        onChange={(e) => setQuestion(e.target.value)}
                      />
                    </div>

                    <div className="pro-form-group">
                      <fieldset disabled={running || attempted} className="pro-fieldset">
                        <legend>Evidence Categories</legend>
                        <div className="pro-checkbox-grid">
                          <label className="pro-checkbox-label">
                            <input
                              type="checkbox"
                              checked={selectedCategories.includes('labels')}
                              onChange={() => toggleCategory('labels')}
                            />
                            <span>FDA Drug Labeling (SPL)</span>
                          </label>
                          <label className="pro-checkbox-label">
                            <input
                              type="checkbox"
                              checked={selectedCategories.includes('recalls')}
                              onChange={() => toggleCategory('recalls')}
                            />
                            <span>Historical Enforcement Recalls</span>
                          </label>
                          <label className="pro-checkbox-label">
                            <input
                              type="checkbox"
                              checked={selectedCategories.includes('faers')}
                              onChange={() => toggleCategory('faers')}
                            />
                            <span>FAERS Adverse Event Signals</span>
                          </label>
                        </div>
                      </fieldset>
                    </div>

                    <SynthesisOption enabled={synthesize} onChange={setSynthesize} disabled={running || attempted || !!busy} />
                    <div className="pro-form-group">
                      <label htmlFor="pro-model-select">Execution Inference Engine:</label>
                      <select
                        id="pro-model-select"
                        value={model}
                        disabled={running || attempted}
                        onChange={(e) => setModel(e.target.value)}
                      >
                        <option value="">Deterministic evidence planning</option>
                        {session.models.map((m) => (
                          <option key={m} value={m}>
                            {modelNames[m] ?? m} · Local Ollama Agent
                          </option>
                        ))}
                      </select>
                      {session.model_runtime === 'unavailable' && (
                        <p className="pro-subtle-hint">
                          Ollama daemon offline. Deterministic evidence retrieval pipeline active.
                        </p>
                      )}
                    </div>

                    <div className="pro-action-row">
                      <button
                        type="submit"
                        className="pro-btn-cyan run-btn-pro"
                        disabled={!product || selectedCategories.length === 0 || !question.trim() || running || attempted || !!busy}
                      >
                        {running ? 'Executing Bounded Agent…' : 'Execute Deep Evidence Retrieval'}
                      </button>

                      {!product && (
                        <span className="pro-hint">Confirm medication identity above to unlock execution.</span>
                      )}
                    </div>

                    {running && (
                      <div role="status" className="pro-running-box">
                        <div className="pro-pulse-bar" />
                        <p>Executing bounded local multi-source workflow with strict Pydantic validation…</p>
                      </div>
                    )}

                    {(running || (attempted && !result)) && (
                      <button
                        type="button"
                        className="pro-btn-danger cancel-pro-btn"
                        onClick={onCancelResearch}
                        disabled={!!busy}
                      >
                        Abort Execution & Reclaim Worker
                      </button>
                    )}
                  </form>
                </section>
              </div>

              {/* Verified Briefing Result */}
              {result && (
                <div className="pro-result-section">
                  <Briefing value={result} />
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Footer */}
      <footer className="pro-footer">
        <span>Dav AI Research Pro · Educational Pharmaceutical Explorer</span>
        <span>Read-Only SQLite Engine · Mode: 0444 · Localhost Loopback Only</span>
      </footer>
    </div>
  )
}
