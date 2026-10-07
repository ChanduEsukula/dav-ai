import { useState } from 'react'
import {
  askStoredDrug,
  type AskDrugResponse,
} from '../api/drugCatalog'

const examples = [
  'What warnings are stored for this drug?',
  'Have there been recalls in this release?',
  'What adverse events appear in the stored release?',
  'What safety communications are available?',
  'Summarize the safety timeline.',
]

const officialSource = (url: string | null) =>
  Boolean(
    url &&
      /^https:\/\/(?:api\.fda\.gov|www\.fda\.gov|fda\.gov|download\.open\.fda\.gov)\//.test(
        url,
      ),
  )

export default function AskStoredDrug({
  drugId,
}: {
  drugId: string
}) {
  const [question, setQuestion] = useState('')
  const [result, setResult] =
    useState<AskDrugResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit(value: string) {
    if (!value.trim() || loading) return

    setQuestion(value)
    setLoading(true)
    setError('')
    setResult(null)

    try {
      setResult(
        await askStoredDrug(
          drugId,
          value,
        ),
      )
    } catch {
      setError(
        'Ask Dav AI is unavailable. You can still review the frozen stored evidence sections.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <section
      className="stored-ask"
      aria-label="Ask Dav AI about this drug"
    >
      <h3>Ask Dav AI</h3>

      <p>
        Ask Dav AI summarizes evidence from the frozen pharmaceutical
        release. It does not determine whether a drug caused an adverse
        event or provide medical advice.
      </p>

      <p>
        The language model may select only server-supplied evidence IDs.
        Dav AI validates that selection and renders the stored release
        evidence itself.
      </p>

      <details>
        <summary>Example questions</summary>
        <ul>
          {examples.map(example => (
            <li key={example}>
              <button
                type="button"
                disabled={loading}
                onClick={() => void submit(example)}
              >
                {example}
              </button>
            </li>
          ))}
        </ul>
      </details>

      <form
        onSubmit={event => {
          event.preventDefault()
          void submit(question)
        }}
      >
        <label htmlFor="stored-ask-question">
          Question about this selected drug
        </label>

        <textarea
          id="stored-ask-question"
          maxLength={500}
          value={question}
          disabled={loading}
          onChange={event =>
            setQuestion(event.target.value)
          }
          required
        />

        <button
          disabled={
            loading ||
            !question.trim()
          }
          type="submit"
        >
          Ask from stored evidence
        </button>
      </form>

      {loading && (
        <p role="status">
          Reviewing frozen release evidence…
        </p>
      )}

      {error && (
        <p role="alert">
          {error}
        </p>
      )}

      {result && (
        <div aria-live="polite">
          <p className="stored-text">
            {result.answer}
          </p>

          <p>
            {result.evidence_count} evidence items considered ·{' '}
            {result.status.replaceAll('_', ' ')}
          </p>

          <ol className="stored-citations">
            {result.citations.map(citation => (
              <li key={citation.id}>
                <strong>
                  [{citation.id}]{' '}
                  {citation.title ||
                    'Stored release evidence'}
                </strong>

                <p>
                  {citation.source} · Source record{' '}
                  {citation.source_record_id}
                  <br />
                  Source date:{' '}
                  {citation.source_date ||
                    'Not supplied'}{' '}
                  ({citation.source_date_type})
                </p>

                {citation.aggregation && (
                  <p>
                    {citation.aggregation.scope}
                  </p>
                )}

                {officialSource(
                  citation.source_url,
                ) && (
                  <a
                    href={
                      citation.source_url ||
                      undefined
                    }
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open cited official source [
                    {citation.id}]
                  </a>
                )}
              </li>
            ))}
          </ol>

          <details>
            <summary>
              Evidence limitations and release coverage
            </summary>

            <ul>
              {result.limitations.map(
                limitation => (
                  <li key={limitation}>
                    {limitation}
                  </li>
                ),
              )}
            </ul>

            {Object.entries(
              result.coverage,
            ).map(([kind, coverage]) => (
              <section key={kind}>
                <h4>
                  {kind.replaceAll('_', ' ')}
                </h4>

                <p>
                  Coverage state:{' '}
                  <strong>
                    {coverage.state}
                  </strong>{' '}
                  · {coverage.reason_code}
                </p>

                <p>
                  Scope: {coverage.scope}
                </p>

                <p>
                  As of:{' '}
                  {coverage.as_of_date ||
                    'Not supplied'}{' '}
                  · Source date:{' '}
                  {coverage.source_date ||
                    'Not supplied'}
                </p>

                {coverage.limitations.length >
                  0 && (
                  <ul>
                    {coverage.limitations.map(
                      limitation => (
                        <li
                          key={limitation}
                        >
                          {limitation}
                        </li>
                      ),
                    )}
                  </ul>
                )}
              </section>
            ))}
          </details>
        </div>
      )}
    </section>
  )
}
