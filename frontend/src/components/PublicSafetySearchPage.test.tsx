import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import {
  searchRealWorldSafety,
  type RealWorldSafetySearchResponse,
} from '../api/realWorldSafety'
import PublicSafetySearchPage from './PublicSafetySearchPage'

vi.mock('../api/realWorldSafety', async () => {
  const actual = await vi.importActual<typeof import('../api/realWorldSafety')>(
    '../api/realWorldSafety',
  )
  return { ...actual, searchRealWorldSafety: vi.fn() }
})

const mockSearchRealWorldSafety = vi.mocked(searchRealWorldSafety)

const publicSafetyResponse: RealWorldSafetySearchResponse = {
  query: 'Advil',
  raw_query: 'Advil',
  query_understanding: {
    original_query: 'Advil',
    normalized_query: 'advil',
    search_query: 'advil',
    corrections_applied: [],
    expanded_terms: ['ibuprofen'],
    expansion_search_terms_used: ['ibuprofen'],
    detected_identifiers: {
      vin: null,
      ndc: null,
      upc: null,
    },
    query_type_hints: ['drug'],
  },
  count: 1,
  limit: 10,
  retrieval_timestamp: '2026-06-23T14:00:00Z',
  sources_checked: [
    {
      source_id: 'openfda_ndc_directory',
      source_name: 'openFDA NDC Directory API',
      source_type: 'local curated official snapshot',
      source_url: 'https://api.fda.gov/drug/ndc.json',
      source_kind: 'structured_api',
      upstream_status: 'success',
      record_count: 1,
    },
    {
      source_id: 'openfda_drug_enforcement',
      source_name: 'openFDA Drug Enforcement API',
      source_type: 'local curated official snapshot',
      source_url: 'https://api.fda.gov/drug/enforcement.json',
      source_kind: 'structured_api',
      upstream_status: 'empty',
      record_count: 0,
    },
  ],
  sources_failed: [],
  records_per_source: {
    'openFDA NDC Directory API': 1,
  },
  structured_api_matches: 1,
  public_notice_matches: 0,
  total_matches: 1,
  no_match_explanation: null,
  safety_intelligence_summary: {
    query_type: 'drug',
    recall_or_enforcement_found: false,
    reference_or_label_found: true,
    signal_report_found: false,
    matched_sources_by_role: {
      recall_enforcement: [],
      reference_identity: ['openFDA NDC Directory API'],
      label_reference: [],
      signal_report: [],
      other: [],
    },
    checked_sources_by_role: {
      recall_enforcement: ['openFDA Drug Enforcement API'],
      reference_identity: ['openFDA NDC Directory API'],
      label_reference: [],
      signal_report: [],
      other: [],
    },
    top_result_titles: ['openFDA NDC listing: Advil (ibuprofen)'],
    expansion_explanations: [
      'Dav AI also checked "ibuprofen" because it is a known related search term for the original query.',
    ],
    plain_language_summary:
      'No matching recall/enforcement record was found in the returned results, but Dav AI found official identity or label reference records.',
    suggested_next_steps: [
      'Use the reference records to confirm exact product identity before searching official recall pages again.',
    ],
    caveat:
      'This summary is generated only from returned official/public records. It does not invent missing recalls, certify safety, or provide medical/legal advice.',
  },
  public_data_disclaimer:
    'Public records only. This does not certify that the product is safe.',
  limitations: ['Users must verify official source records.'],
  source_audits: [],
  results: [
    {
      source_name: 'openFDA NDC Directory API',
      source_type: 'local curated official snapshot',
      source_url: 'https://api.fda.gov/drug/ndc.json',
      source_kind: 'structured_api',
      category: 'Drug reference / NDC directory',
      product_name: 'Advil',
      brand_name: 'Advil',
      company_name: 'FDA / openFDA NDC Directory',
      title: 'openFDA NDC listing: Advil (ibuprofen)',
      reason: 'Official openFDA NDC Directory drug listing/reference record.',
      hazard_type: 'Reference record, not a recall',
      remedy:
        'Use this record to identify the drug product, NDC, active ingredient, dosage form, route, labeler, and package listing before comparing against recall/enforcement sources.',
      published_date: '20260102',
      recall_number: '66715-6547',
      affected_models: ['66715-6547', 'tablet'],
      affected_lots: ['ibuprofen 200 mg'],
      raw_payload_hash: 'hash-advil',
      retrieved_at: '2026-06-23T14:00:00Z',
      record_url: 'https://api.fda.gov/drug/ndc.json',
    },
  ],
}

beforeEach(() => {
  mockSearchRealWorldSafety.mockReset()
  mockSearchRealWorldSafety.mockResolvedValue(publicSafetyResponse)
  window.history.replaceState(null, '', '/')
})

test('renders RealWorldSafety response data in the Public Safety Search page', async () => {
  const user = userEvent.setup()
  render(<PublicSafetySearchPage initialQuery="" />)

  await user.type(screen.getByLabelText(/Safety record search/i), 'Advil')
  await user.click(screen.getByRole('button', { name: 'Search public records' }))

  await waitFor(() => {
    expect(mockSearchRealWorldSafety).toHaveBeenCalledWith('Advil', 10)
  })

  expect(await screen.findByText(/How Dav AI interpreted the search/i)).toBeInTheDocument()
  expect(screen.getByText(/Dav AI also checked ibuprofen/i)).toBeInTheDocument()
  expect(screen.getAllByText('advil').length).toBeGreaterThan(0)
  expect(screen.getAllByText('ibuprofen').length).toBeGreaterThan(0)
  expect(screen.getByText(/official identity or label reference records/i)).toBeInTheDocument()
  expect(screen.getAllByText('Reference identity').length).toBeGreaterThan(0)
  expect(screen.getAllByText('openFDA NDC Directory API').length).toBeGreaterThan(0)
  expect(screen.getByText('openFDA NDC listing: Advil (ibuprofen)')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Open official record' })).toHaveAttribute(
    'href',
    'https://api.fda.gov/drug/ndc.json',
  )
})
