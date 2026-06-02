type SemanticPreviewMatch = {
  record_id: string
  text: string
  similarity_score: number
  explanation: string
  source_name: string | null
}

type SemanticPreview = {
  query_text: string
  matches: SemanticPreviewMatch[]
  limitations: string[]
  preview_version: string
  is_production_ml: boolean
}

type SemanticPreviewPanelProps = {
  title: string
  preview: SemanticPreview
}

function SemanticPreviewPanel({ title, preview }: SemanticPreviewPanelProps) {
  return (
    <section className="semantic-preview-panel" aria-label={title}>
      <div className="semantic-preview-header">
        <div>
          <p className="eyebrow">Responsible AI/NLP preview</p>
          <h3>{title}</h3>
          <p>
            Deterministic public-data text similarity only. This is not medical advice,
            diagnostic output, care guidance, clinical decision support, production ML, RAG,
            LLM output, or alerting.
          </p>
        </div>

        <div className="semantic-preview-meta" aria-label="Semantic preview metadata">
          <span>{preview.preview_version}</span>
          <span>Production ML: {preview.is_production_ml ? 'Yes' : 'No'}</span>
        </div>
      </div>

      {preview.matches.length > 0 ? (
        <div className="semantic-preview-matches">
          {preview.matches.map((match) => (
            <article className="semantic-preview-card" key={match.record_id}>
              <div className="semantic-preview-card__topline">
                <span>{match.record_id}</span>
                <strong>{Math.round(match.similarity_score * 1000) / 1000}</strong>
              </div>

              <p className="semantic-preview-explanation">{match.explanation}</p>

              <p className="semantic-preview-text">{match.text}</p>

              <small>{match.source_name ?? 'Public data source'}</small>
            </article>
          ))}
        </div>
      ) : (
        <p className="semantic-preview-empty">
          No similar public-data text matches were returned for this preview.
        </p>
      )}

      <details className="semantic-preview-limitations">
        <summary>Preview limitations</summary>
        <ul>
          {preview.limitations.map((limitation) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
      </details>
    </section>
  )
}

export default SemanticPreviewPanel
