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

const publicSafetyContext: AssistantChatContext = {
  module: 'public_safety',
  page_context: {
    query: 'air fryer',
    count: 1,
    source_name: 'DavAI Public Safety Search',
    endpoint: '/api/v1/real-world-safety/search',
    retrieval_timestamp: '2026-06-02T18:00:00Z',
    audit_id: 'audit-public-safety-1',
    limitations: [
      'Public data only. Verify exact product identifiers with the official source.',
    ],
    public_safety: {
      summary: {
        query_type: 'consumer_product',
        recall_or_enforcement_found: true,
        reference_or_label_found: false,
        signal_report_found: false,
        plain_language_summary: 'An official public safety record matched this search.',
        suggested_next_steps: ['Verify the exact model and recall number.'],
        caveat: 'No result or partial result is not a safety guarantee.',
      },
      identifier_check: {
        user_message: 'Verify exact identifiers before acting.',
        detected: [],
        to_verify: [
          {
            type: 'model',
            label: 'Model number',
            value: 'AF-100',
            source: 'public safety result',
            reason: 'Model numbers determine whether a specific unit is affected.',
          },
        ],
      },
      sources_checked: [
        {
          source_id: 'cpsc_recalls',
          source_name: 'CPSC Recalls',
          source_type: 'consumer_product_recall',
          source_kind: 'structured_api',
          upstream_status: 'ok',
          record_count: 1,
        },
      ],
      sources_failed: [],
      top_records: [
        {
          title: 'Example Air Fryer Recall',
          product_name: 'Example Air Fryer',
          brand_name: 'ExampleBrand',
          company_name: 'Example Company',
          source_name: 'CPSC Recalls',
          source_type: 'consumer_product_recall',
          source_kind: 'structured_api',
          category: 'consumer_product',
          reason: 'Fire and burn hazard',
          hazard_type: 'fire',
          remedy: 'Stop use and contact firm for remedy.',
          published_date: '2026-06-01',
          recall_number: '26-123',
          affected_models: ['AF-100'],
          affected_lots: [],
          record_url: 'https://www.cpsc.gov/example',
          extraction_confidence: null,
          source_text_excerpt: 'Example official recall excerpt.',
        },
      ],
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

    expect(screen.getByRole('button', { name: /Explain These Results/i })).toBeInTheDocument()
    expect(screen.queryByRole('dialog', { name: /Explain These Results/i })).not.toBeInTheDocument()
  })

  it('opens the drawer on click', () => {
    render(<AskDavAIChat context={recallContext} />)

    fireEvent.click(screen.getByRole('button', { name: /Explain These Results/i }))

    expect(screen.getByRole('dialog', { name: /Explain These Results/i })).toBeInTheDocument()
    expect(screen.getByText(/RecallRadar result context/i)).toBeInTheDocument()
    expect(screen.getByText(/Source-grounded result explanation/i)).toBeInTheDocument()
    expect(screen.getByText(/Explanations stay inside the current result, source metadata, audit context, and safety limitations/i)).toBeInTheDocument()
  })

  it('does not render a visible entry point without result context', () => {
    render(<AskDavAIChat context={null} />)

    expect(screen.queryByRole('button', { name: /Explain These Results/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('dialog', { name: /Explain These Results/i })).not.toBeInTheDocument()
  })

  it('sends sanitized context when asking a prompt', async () => {
    mockAskDavAI.mockResolvedValue(answer)
    render(<AskDavAIChat context={recallContext} />)

    fireEvent.click(screen.getByRole('button', { name: /Explain These Results/i }))
    fireEvent.click(screen.getByRole('button', { name: /^Explain these results$/ }))

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

    fireEvent.click(screen.getByRole('button', { name: /Explain These Results/i }))
    fireEvent.change(screen.getByLabelText(/Ask about the current public-data result/i), {
      target: { value: 'Where did this data come from?' },
    })
    fireEvent.click(screen.getByRole('button', { name: /^Explain$/i }))

    expect(await screen.findByText(/public-data review context/i)).toBeInTheDocument()
    expect(screen.getByText(/Audit ID: audit-recall-1/i)).toBeInTheDocument()
    expect(screen.getAllByText(/Not medical advice/i).length).toBeGreaterThan(0)
  })

  it('renders Public Safety-specific suggested prompts and sends the selected question', async () => {
    mockAskDavAI.mockResolvedValue(answer)
    render(<AskDavAIChat context={publicSafetyContext} />)

    fireEvent.click(screen.getByRole('button', { name: /Explain These Results/i }))

    expect(screen.getByText(/Public Safety Search result context/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /What evidence types were found/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Which sources were checked/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /What identifiers should I verify/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Is this a recall or reference record/i })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /What evidence types were found/i }))

    await waitFor(() => expect(mockAskDavAI).toHaveBeenCalledTimes(1))
    expect(mockAskDavAI).toHaveBeenCalledWith({
      ...publicSafetyContext,
      question: 'What evidence types were found in this Public Safety Search?',
    })
  })

  it('displays a refusal state', async () => {
    mockAskDavAI.mockResolvedValue(refusalAnswer)
    render(<AskDavAIChat context={drugContext} />)

    fireEvent.click(screen.getByRole('button', { name: /Explain These Results/i }))
    fireEvent.click(screen.getByRole('button', { name: /What does FAERS not prove/i }))

    expect(await screen.findByText(/Request refused safely/i)).toBeInTheDocument()
    expect(screen.getByText(/cannot provide medical advice/i)).toBeInTheDocument()
  })
})
