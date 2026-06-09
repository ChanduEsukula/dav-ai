import { useMemo, useState } from 'react'
import {
  askDavAI,
  type AssistantChatContext,
  type AssistantChatResponse,
} from '../api/assistant'

type AskDavAIChatProps = {
  context: AssistantChatContext | null
}

type PromptChip = {
  label: string
  question: string
}

const basePrompts: PromptChip[] = [
  {
    label: 'Explain these results',
    question: 'Explain these results in plain English.',
  },
  {
    label: 'What should I verify?',
    question: 'What should I verify from these results?',
  },
  {
    label: 'Where did this data come from?',
    question: 'Where did this data come from?',
  },
  {
    label: 'What are the limitations?',
    question: 'What are the limitations of these results?',
  },
]

const drugSignalPrompt: PromptChip = {
  label: 'What does FAERS not prove?',
  question: 'What does FAERS not prove from these reports?',
}

function contextLabel(context: AssistantChatContext | null) {
  if (!context) return 'No result context'

  const labels: Record<AssistantChatContext['module'], string> = {
    recall: 'RecallRadar result context',
    drug_event: 'DrugSignal result context',
    food: 'FoodRadar result context',
    cosmetic: 'CosmeticSignal result context',
  }

  return labels[context.module]
}

function AskDavAIChat({ context }: AskDavAIChatProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<AssistantChatResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const prompts = useMemo(() => {
    if (context?.module === 'drug_event') {
      return [...basePrompts, drugSignalPrompt]
    }

    return basePrompts
  }, [context])

  async function submitQuestion(nextQuestion: string) {
    const trimmedQuestion = nextQuestion.trim()

    if (!trimmedQuestion || !context || loading) return

    setLoading(true)
    setError('')

    try {
      const response = await askDavAI({
        ...context,
        question: trimmedQuestion,
      })
      setAnswer(response)
      setQuestion('')
    } catch {
      setError('Ask DAV AI is unavailable. Try again after the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="ask-dav-ai-chat" aria-label="Ask DAV AI chatbot">
      <button
        type="button"
        className="ask-dav-ai-chat__toggle"
        onClick={() => setIsOpen((current) => !current)}
        aria-expanded={isOpen}
      >
        Ask DAV AI
      </button>

      {isOpen && (
        <div className="ask-dav-ai-chat__drawer" role="dialog" aria-label="Ask DAV AI">
          <div className="ask-dav-ai-chat__header">
            <div>
              <p className="eyebrow">Ask DAV AI</p>
              <h2>Source-grounded safety assistant</h2>
              <p>Answers use only the current RecallRadar, DrugSignal, FoodRadar, or CosmeticSignal results. Not medical advice, diagnosis, treatment guidance, causation proof, or safety guarantees.</p>
            </div>

            <button type="button" onClick={() => setIsOpen(false)} aria-label="Close Ask DAV AI">
              Close
            </button>
          </div>

          <p className="ask-dav-ai-chat__context">{contextLabel(context)}</p>

          {!context && (
            <div className="ask-dav-ai-chat__empty" role="status">
              Search RecallRadar, DrugSignal, FoodRadar, or CosmeticSignal first, then ask about the current public-source result.
            </div>
          )}

          {context && (
            <>
              <div className="ask-dav-ai-chat__prompts" aria-label="Suggested questions">
                {prompts.map((prompt) => (
                  <button
                    type="button"
                    key={prompt.label}
                    onClick={() => submitQuestion(prompt.question)}
                    disabled={loading}
                  >
                    {prompt.label}
                  </button>
                ))}
              </div>

              <form
                className="ask-dav-ai-chat__form"
                onSubmit={(event) => {
                  event.preventDefault()
                  submitQuestion(question)
                }}
              >
                <label htmlFor="ask-dav-ai-question">Ask about the current public-data result</label>
                <div>
                  <input
                    id="ask-dav-ai-question"
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="Example: What should I verify?"
                  />
                  <button type="submit" disabled={loading || !question.trim()}>
                    {loading ? 'Asking...' : 'Ask'}
                  </button>
                </div>
              </form>
            </>
          )}

          {error && (
            <p className="ask-dav-ai-chat__error" role="alert">
              {error}
            </p>
          )}

          {answer && (
            <article
              className={`ask-dav-ai-chat__answer${
                answer.refused ? ' ask-dav-ai-chat__answer--refused' : ''
              }`}
              aria-live="polite"
            >
              {answer.refused && <strong>Request refused safely</strong>}
              <p>{answer.answer}</p>

              <ul>
                {answer.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>

              <div className="ask-dav-ai-chat__citations">
                {answer.source_citations.map((citation) => (
                  <span key={`${citation.label}-${citation.value}`}>
                    {citation.label}: {citation.value}
                  </span>
                ))}
              </div>

              <div className="ask-dav-ai-chat__limitations">
                {answer.limitations.map((limitation) => (
                  <p key={limitation}>{limitation}</p>
                ))}
              </div>
            </article>
          )}
        </div>
      )}
    </section>
  )
}

export default AskDavAIChat
