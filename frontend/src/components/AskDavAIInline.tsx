import { useState } from 'react'
import type { AskDavAIAnswer, AskDavAIPrompt } from '../utils/reviewAssistant'

type AskDavAIInlineProps = {
  title: string
  description: string
  prompts: {
    label: string
    prompt: AskDavAIPrompt
  }[]
  onAsk: (prompt: AskDavAIPrompt, question?: string) => AskDavAIAnswer
}

function AskDavAIInline({ title, description, prompts, onAsk }: AskDavAIInlineProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<AskDavAIAnswer | null>(null)

  function handlePrompt(prompt: AskDavAIPrompt) {
    setAnswer(onAsk(prompt))
    setIsOpen(true)
  }

  function handleCustomQuestion() {
    const trimmedQuestion = question.trim()

    if (!trimmedQuestion) return

    setAnswer(onAsk('plain_english', trimmedQuestion))
    setQuestion('')
    setIsOpen(true)
  }

  return (
    <section className="ask-dav-ai-inline" aria-label={title}>
      <div className="ask-dav-ai-inline__header">
        <div>
          <p className="eyebrow">Ask DAV AI</p>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>

        <button type="button" onClick={() => setIsOpen((current) => !current)}>
          {isOpen ? 'Hide' : 'Ask'}
        </button>
      </div>

      {isOpen && (
        <div className="ask-dav-ai-inline__body">
          <div className="ask-dav-ai-prompts" aria-label="Suggested Ask DAV AI prompts">
            {prompts.map((item) => (
              <button key={item.label} type="button" onClick={() => handlePrompt(item.prompt)}>
                {item.label}
              </button>
            ))}
          </div>

          <div className="ask-dav-ai-question">
            <label htmlFor={`${title.replace(/\s+/g, '-').toLowerCase()}-question`}>
              Ask a question about these public-data results
            </label>

            <div>
              <input
                id={`${title.replace(/\s+/g, '-').toLowerCase()}-question`}
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    handleCustomQuestion()
                  }
                }}
                placeholder="Example: What should I verify?"
              />

              <button type="button" onClick={handleCustomQuestion}>
                Ask
              </button>
            </div>
          </div>

          {answer && (
            <article className="ask-dav-ai-answer" aria-live="polite">
              <h4>{answer.title}</h4>
              <p>{answer.summary}</p>

              <ul>
                {answer.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>

              <div className="ask-dav-ai-source">
                {answer.sourceDetails.map((detail) => (
                  <span key={detail}>{detail}</span>
                ))}
              </div>

              <p className="ask-dav-ai-limitation">{answer.limitation}</p>
            </article>
          )}
        </div>
      )}
    </section>
  )
}

export default AskDavAIInline
