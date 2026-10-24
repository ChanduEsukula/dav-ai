import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { RagEvidencePanel, Briefing } from './Evidence'
import { EverydayRagCard, EverydayBriefing } from './EverydayEvidence'
import type { PublicRagEvidence, PublicBriefing } from './contracts'

const mockSupportedRag: PublicRagEvidence = {
  type: 'hybrid_rag_evidence',
  status: 'supported',
  route: 'hybrid_routing',
  verified_answer: true,
  confidence: 'calibrated',
  reason: 'verified_relevant_sections',
  product_ref: 'p_test_123',
  requested_sections: ['contraindications'],
  missing_sections: [],
  degraded_reason: null,
  limitations: ['Hybrid RAG passages are scoped to confirmed product FDA label only.'],
  passages: [
    {
      chunk_id: 'prod1:contraindications:chunk_0',
      section: 'contraindications',
      ordinal: 0,
      text: 'Lipitor is contraindicated in patients with active liver disease or unexplained persistent elevations of hepatic transaminases.',
      citation_tag: '[SPL:contraindications:1]',
      source_url: 'https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=test-set-id',
      source_record_id: 'test-set-id',
    },
  ],
}

const mockCandidateRag: PublicRagEvidence = {
  type: 'hybrid_rag_evidence',
  status: 'candidate_only',
  route: 'bge_semantic',
  verified_answer: false,
  confidence: 'uncalibrated',
  reason: 'candidate_semantic_matches',
  product_ref: 'p_test_123',
  requested_sections: ['warnings_and_precautions'],
  missing_sections: [],
  degraded_reason: null,
  limitations: [
    'Vector similarity candidates are not verified clinical answers.',
    'Candidate passages require human or label review before clinical reliance.',
  ],
  passages: [
    {
      chunk_id: 'prod1:warnings_and_precautions:chunk_1',
      section: 'warnings_and_precautions',
      ordinal: 1,
      text: 'Cases of myopathy and rhabdomyolysis have been reported with HMG-CoA reductase inhibitors including Lipitor.',
      citation_tag: '[SPL:warnings_and_precautions:1]',
      source_url: 'https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=test-set-id',
      source_record_id: 'test-set-id',
    },
  ],
}

const mockInsufficientRag: PublicRagEvidence = {
  type: 'hybrid_rag_evidence',
  status: 'insufficient_evidence',
  route: 'sql_section_check',
  verified_answer: false,
  confidence: 'none',
  reason: 'unsupported_topic',
  product_ref: 'p_test_123',
  requested_sections: [],
  missing_sections: [],
  degraded_reason: null,
  limitations: ['No sufficient evidence in the official FDA label for this product.'],
  passages: [],
}

const mockSectionAbsentRag: PublicRagEvidence = {
  type: 'hybrid_rag_evidence',
  status: 'insufficient_evidence',
  route: 'sql_section_check',
  verified_answer: false,
  confidence: 'none',
  reason: 'section_absent',
  product_ref: 'p_test_123',
  requested_sections: ['boxed_warning'],
  missing_sections: ['boxed_warning'],
  degraded_reason: null,
  limitations: ['Section boxed_warning is absent in the admitted label.'],
  passages: [],
}

const baseBriefing: PublicBriefing = {
  schema_version: 'agent-research-v2',
  status: 'completed',
  workflow_state: 'COMPLETE',
  routing: {
    mode: 'deterministic',
    model_planned_tools: [],
    backend_completed_tools: ['labels'],
    discarded_model_content: false,
  },
  medication: {
    product_ref: 'p_test_123',
    product_ndcs: ['0071-0155-23'],
    package_ndcs: ['0071-0155-23-01'],
    generic_name: 'atorvastatin calcium',
    brand_names: ['Lipitor'],
    dosage_form: 'TABLET, FILM COATED',
    strength: '10 mg',
    routes: ['ORAL'],
    active_ingredients: ['atorvastatin calcium'],
    provenance: {
      source: 'dailymed',
      source_id: 'test-set-id',
      source_record_id: 'test-set-id',
      source_url: 'https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=test-set-id',
      observed_at: '2026-01-01',
    },
  },
  requested_categories: ['labels'],
  sections: [
    {
      category: 'labels',
      status: 'available',
      reason: null,
      evidence: {
        type: 'drug_label_evidence',
        scope: 'PRODUCT_LINKED_LABEL',
        product_ref: 'p_test_123',
        source_snapshot_date: '2026-01-01',
        release: {
          release_id: 'pharma_v1',
          contract_id: 'pharma_contract_v1',
          policy_version: '1.0',
          schema_version: '1.0',
          build_version: '1.0',
          build_time_utc: '2026-01-01T00:00:00Z',
          ndc_observation_date: '2026-01-01',
          label_export_date: '2026-01-01',
          window_start: '2020-01-01',
          window_end: '2026-01-01',
          publication_authorized: false,
        },
        coverage: {
          state: 'present',
          reason_code: null,
          scope: 'PRODUCT',
          as_of_date: '2026-01-01',
          source_date: '2026-01-01',
          measured_count: 1,
          unresolved_count: 0,
          stored_record_count: 1,
          bounded: true,
          truncated: false,
          empty_message: null,
          limitations: [],
        },
        missing_sections: [],
        limitations: [],
        records: [
          {
            label_set_id: 'test-set-id',
            label_version: '1',
            effective_date: '2024-01-01',
            applicability_class: 'EXACT_PRODUCT',
            evidence_scope: 'PRODUCT',
            selection_status: 'SELECTED_STORED',
            match_method: 'ndc',
            matched_value: '0071-0155-23',
            source: 'dailymed',
            source_record_id: 'test-set-id',
            source_url: 'https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=test-set-id',
            boxed_warning: null,
            warnings_and_precautions: 'Risk of myopathy and liver enzyme elevations.',
            warnings: null,
            contraindications: 'Active liver failure.',
            drug_interactions: 'Avoid strong CYP3A4 inhibitors.',
            adverse_reactions: 'Nasopharyngitis, arthralgia.',
            section_states: {},
          },
        ],
      },
    },
  ],
  limitations: ['Study findings reflect frozen FDA snapshot.'],
  rag: null,
}

describe('RagEvidencePanel in Research Pro Experience', () => {
  it('renders verified relevant evidence badge and passages for supported status', () => {
    render(<RagEvidencePanel rag={mockSupportedRag} />)

    expect(screen.getByText('Relevant FDA Label Passages (Hybrid RAG)')).toBeInTheDocument()
    expect(screen.getByText('Verified Relevant Evidence')).toBeInTheDocument()
    expect(screen.getByText('[SPL:contraindications:1]')).toBeInTheDocument()
    expect(
      screen.getByText(/Lipitor is contraindicated in patients with active liver disease/),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /contraindications ↓/i })).toHaveAttribute(
      'href',
      '#section-contraindications',
    )
  })

  it('renders unverified candidate warning banner when status is candidate_only', () => {
    render(<RagEvidencePanel rag={mockCandidateRag} />)

    expect(screen.getByText('Unverified Semantic Candidates')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent(/Semantic Candidates Only:/)
    expect(screen.getByRole('alert')).toHaveTextContent(/NOT verified clinical answers/)
    expect(screen.getByText('[SPL:warnings_and_precautions:1]')).toBeInTheDocument()
    expect(
      screen.getByText(/Cases of myopathy and rhabdomyolysis have been reported/),
    ).toBeInTheDocument()
  })

  it('renders unsupported topic alert when evidence is insufficient', () => {
    render(<RagEvidencePanel rag={mockInsufficientRag} />)

    expect(screen.getByText('Insufficient Label Evidence')).toBeInTheDocument()
    const alert = screen.getByRole('status')
    expect(alert).toHaveTextContent(/No Sufficient Supporting Evidence:/)
    expect(alert).toHaveTextContent(
      /requested topic or clinical condition was not found in the official label/,
    )
    expect(screen.queryByText(/\[SPL:/)).not.toBeInTheDocument()
  })

  it('renders section absent alert when specific requested section is missing', () => {
    render(<RagEvidencePanel rag={mockSectionAbsentRag} />)

    const alert = screen.getByRole('status')
    expect(alert).toHaveTextContent(/requested label section \(boxed_warning\) is absent/)
  })

  it('returns null and renders nothing when rag status is not_configured', () => {
    const { container } = render(
      <RagEvidencePanel
        rag={{
          type: 'hybrid_rag_evidence',
          status: 'not_configured',
          route: 'none',
          verified_answer: false,
          confidence: 'none',
          reason: 'rag_unconfigured',
          product_ref: 'p_test_123',
          requested_sections: [],
          missing_sections: [],
          degraded_reason: null,
          limitations: [],
          passages: [],
        }}
      />,
    )
    expect(container.firstChild).toBeNull()
  })
})

describe('EverydayRagCard in Everyday Consumer Experience', () => {
  it('renders clear consumer passages and badge for supported status', () => {
    render(<EverydayRagCard rag={mockSupportedRag} />)

    expect(screen.getByText('Relevant Label Passages (Smart Search)')).toBeInTheDocument()
    expect(screen.getByText('Verified Label Excerpts')).toBeInTheDocument()
    expect(screen.getByText('[SPL:contraindications:1]')).toBeInTheDocument()
    expect(
      screen.getByText(/Lipitor is contraindicated in patients with active liver disease/),
    ).toBeInTheDocument()
  })

  it('renders consumer candidate warning banner for candidate_only status', () => {
    render(<EverydayRagCard rag={mockCandidateRag} />)

    expect(screen.getByText('Related Topic Excerpts (Unverified)')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent(/Review Full Label Below:/)
    expect(screen.getByRole('alert')).toHaveTextContent(/matched by topic similarity/)
  })

  it('renders clear consumer explanation when topic is not found', () => {
    render(<EverydayRagCard rag={mockInsufficientRag} />)

    expect(screen.getByText('Search Findings')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent(
      /FDA label for this medication does not discuss the specific condition or question asked/,
    )
  })
})

describe('Briefing and EverydayBriefing RAG Integration', () => {
  it('renders RAG panel within Briefing when rag evidence is provided', () => {
    const briefingWithRag: PublicBriefing = {
      ...baseBriefing,
      rag: mockSupportedRag,
    }
    render(<Briefing value={briefingWithRag} />)

    expect(screen.getByText('Relevant FDA Label Passages (Hybrid RAG)')).toBeInTheDocument()
    expect(screen.getByText('Verified Relevant Evidence')).toBeInTheDocument()
  })

  it('renders EverydayRagCard within EverydayBriefing when rag evidence is provided', () => {
    const briefingWithRag: PublicBriefing = {
      ...baseBriefing,
      rag: mockCandidateRag,
    }
    render(<EverydayBriefing briefing={briefingWithRag} />)

    expect(screen.getByText('Relevant Label Passages (Smart Search)')).toBeInTheDocument()
    expect(screen.getByText('Related Topic Excerpts (Unverified)')).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent(/Review Full Label Below:/)
  })

  it('omits RAG section cleanly when briefing has no rag field', () => {
    render(<Briefing value={baseBriefing} />)
    expect(screen.queryByText(/Hybrid RAG/i)).not.toBeInTheDocument()

    render(<EverydayBriefing briefing={baseBriefing} />)
    expect(screen.queryByText(/Relevant Label Passages \(Smart Search\)/i)).not.toBeInTheDocument()
  })
})
