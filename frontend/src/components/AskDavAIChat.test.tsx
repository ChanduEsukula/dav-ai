import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { AssistantChatContext, AssistantChatResponse } from '../api/assistant'
import { askDavAI } from '../api/assistant'
import AskDavAIChat from './AskDavAIChat'

vi.mock('../api/assistant', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/assistant')>()
  return {
    ...actual,
    askDavAI: vi.fn(),
  }
})

const mockAskDavAI = vi.mocked(askDavAI)

const recallContext: AssistantChatContext = {
  module: 'recall',
  page_context: {
    query: 'eye drops',
    count: 1,
    source_name: 'openFDA Drug Enforcement API',
    endpoint: 'https://api.fda.gov/drug/enforcement.json',
    retrieval_timestamp: '2026-06-02T18:00:00Z',
    audit_id: 'audit-recall-1',
    limitations: ['Public recall data only. Not medical advice.'],
    recall: {
      top_results: [
        {
          recall_number: 'D-1234-2026',
          product_description: 'Example Eye Drops',
          reason_for_recall: 'Lack of assurance of sterility',
          classification: 'Class II',
          status: 'Ongoing',
          recall_initiation_date: '20260601',
          distribution_pattern: 'Nationwide',
          recalling_firm: 'Example Firm',
          risk_score_label: 'High',
          risk_score_value: 82,
        },
      ],
    },
  },
}

const drugContext: AssistantChatContext = {
  module: 'drug_event',
  page_context: {
    query: 'metformin',
    count: 2,
    source_name: 'openFDA Drug Event API',
    endpoint: 'https://api.fda.gov/drug/event.json',
    retrieval_timestamp: '2026-06-02T18:00:00Z',
    audit_id: 'audit-drug-1',
    limitations: [
      'Public-data safety intelligence only. Not medical advice.',
      'FAERS adverse-event reports do not prove causation.',
    ],
    drug_event: {
      intelligence_score: {
        score: 67,
        label: 'High',
        review_priority: 'Review',
        data_confidence: 'Moderate',
      },
      top_reactions: [
        {
          reaction: 'Gait disturbance',
          count: 2,
        },
      ],
      reaction_categories: [
        {
          category: 'Neurological',
          count: 2,
          reactions: ['Gait disturbance'],
        },
      ],
      faers_disclaimer: 'FAERS adverse-event reports do not prove causation.',
    },
  },
}

const answer: AssistantChatResponse = {
  answer: 'DAV AI can explain the public-data review context for this result.',
  bullets: ['Verify the source details.', 'Use the audit ID for traceability.'],
  refused: false,
  refusal_reason: null,
  source_citations: [
    {
      label: 'Source',
      value: 'openFDA Drug Enforcement API',
    },
    {
      label: 'Audit ID',
      value: 'audit-recall-1',
    },
  ],
  limitations: ['Public recall data only. Not medical advice.'],
  model_info: {
    provider: 'mock',
    model: 'mock-assistant-v0.1',
  },
  safety: {
    policy_version: 'ask-dav-ai-safety-v0.1',
    output_checked: true,
  },
}

const refusalAnswer: AssistantChatResponse = {
  ...answer,
  answer: 'I can explain public data, but I cannot provide medical advice.',
  refused: true,
  refusal_reason: 'medication guidance',
}

describe('AskDavAIChat', () => {
  beforeEach(() => {
    mockAskDavAI.mockReset()
  })

  it('renders as a collapsed floating button', () => {
    render(<AskDavAIChat context={recallContext} />)

    expect(screen.getByRole('button', { name: /Ask DAV AI/i })).toBeInTheDocument()
    expect(screen.queryByRole('dialog', { name: /Ask DAV AI/i })).not.toBeInTheDocument()
  })

  it('opens the drawer on click', () => {
    render(<AskDavAIChat context={recallContext} />)

    fireEvent.click(screen.getByRole('button', { name: /Ask DAV AI/i }))

    expect(screen.getByRole('dialog', { name: /Ask DAV AI/i })).toBeInTheDocument()
    expect(screen.getByText(/RecallRadar result context/i)).toBeInTheDocument()
    expect(screen.getByText(/Source-grounded safety assistant/i)).toBeInTheDocument()
    expect(screen.getByText(/Answers use only the current RecallRadar or DrugSignal results/i)).toBeInTheDocument()
  })

  it('shows no context state', () => {
    render(<AskDavAIChat context={null} />)

    fireEvent.click(screen.getByRole('button', { name: /Ask DAV AI/i }))

    expect(screen.getByText(/Search RecallRadar or DrugSignal first/i)).toBeInTheDocument()
  })

  it('sends sanitized context when asking a prompt', async () => {
    mockAskDavAI.mockResolvedValue(answer)
    render(<AskDavAIChat context={recallContext} />)

    fireEvent.click(screen.getByRole('button', { name: /Ask DAV AI/i }))
    fireEvent.click(screen.getByRole('button', { name: /Explain these results/i }))

    await waitFor(() => expect(mockAskDavAI).toHaveBeenCalledTimes(1))

    expect(mockAskDavAI).toHaveBeenCalledWith({
      ...recallContext,
      question: 'Explain these results in plain English.',
    })
    expect(JSON.stringify(mockAskDavAI.mock.calls[0][0])).not.toContain('raw')
  })

  it('displays an assistant answer with citations and limitations', async () => {
    mockAskDavAI.mockResolvedValue(answer)
    render(<AskDavAIChat context={recallContext} />)

    fireEvent.click(screen.getByRole('button', { name: /Ask DAV AI/i }))
    fireEvent.change(screen.getByLabelText(/Ask about the current public-data result/i), {
      target: { value: 'Where did this data come from?' },
    })
    fireEvent.click(screen.getByRole('button', { name: /^Ask$/i }))

    expect(await screen.findByText(/public-data review context/i)).toBeInTheDocument()
    expect(screen.getByText(/Audit ID: audit-recall-1/i)).toBeInTheDocument()
    expect(screen.getAllByText(/Not medical advice/i).length).toBeGreaterThan(0)
  })

  it('displays a refusal state', async () => {
    mockAskDavAI.mockResolvedValue(refusalAnswer)
    render(<AskDavAIChat context={drugContext} />)

    fireEvent.click(screen.getByRole('button', { name: /Ask DAV AI/i }))
    fireEvent.click(screen.getByRole('button', { name: /What does FAERS not prove/i }))

    expect(await screen.findByText(/Request refused safely/i)).toBeInTheDocument()
    expect(screen.getByText(/cannot provide medical advice/i)).toBeInTheDocument()
  })
})
