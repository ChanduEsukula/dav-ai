import { render, screen, waitFor, within } from '@testing-library/react'
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

const longOfficialReason =
  'Official openFDA NDC Directory drug listing/reference record. This long official text includes active ingredient, labeler, dosage form, route, product package, and listing context that should not be dumped into the collapsed result preview for a normal user. It should remain available in the expanded details view for reviewers who need the full source text. UNIQUE_FULL_LABEL_WARNING_TAIL'

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
  search_plan: {
    intent: 'drug',
    confidence: 'high',
    reason: 'The query appears to describe a drug, brand, generic ingredient, or NDC identifier.',
    primary_source_ids: ['openfda_drug_enforcement', 'rxnorm_rxnav_api', 'openfda_ndc_directory'],
    secondary_source_ids: ['dailymed_spl_api', 'openfda_drug_label'],
    sources_to_check: [
      'openfda_drug_enforcement',
      'rxnorm_rxnav_api',
      'dailymed_spl_api',
      'openfda_drug_label',
      'openfda_ndc_directory',
    ],
    clarification_required: false,
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
  sources_failed: [
    {
      source_id: 'dailymed_spl_api',
      source_name: 'DailyMed SPL API',
      source_type: 'live official API',
      source_url: 'https://dailymed.nlm.nih.gov/dailymed/services/v2',
      source_kind: 'structured_api',
      error_type: 'upstream_unavailable',
      reason: 'Temporary upstream source issue.',
    },
  ],
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
      'Dav AI also checked "ibuprofen" because it is a known related search term for the original query.',
      'Use the reference records to confirm exact product identity before searching official recall pages again.',
    ],
    caveat:
      'This summary is generated only from returned official/public records. It does not invent missing recalls, certify safety, or provide medical/legal advice.',
  },
  identifier_check: {
    detected: [],
    to_verify: [
      {
        type: 'recall_number',
        label: 'Recall or reference number',
        value: '66715-6547',
        source: 'openFDA NDC Directory API',
        reason: 'Match this official record number before acting on the result.',
      },
      {
        type: 'model',
        label: 'Model or affected item',
        value: 'Advil',
        source: 'openFDA NDC Directory API',
        reason: 'Match the affected model, item, year, package, or device identity.',
      },
      {
        type: 'lot',
        label: 'Lot, package, or product identifier',
        value: 'ibuprofen 200 mg',
        source: 'openFDA NDC Directory API',
        reason: 'Match the exact lot, package, code, strength, route, or listed identifier.',
      },
    ],
    user_message:
      'Verify exact identifiers before acting on any public safety record. No returned record proves every unit is recalled or safe.',
  },
  public_data_disclaimer:
    'Public records only. This does not certify that the product is safe.',
  limitations: ['Users must verify official source records.'],
  source_audits: [
    {
      audit_id: 'audit-openfda-ndc',
      source_id: 'openfda_ndc_directory',
      source_name: 'openFDA NDC Directory API',
      module: 'RealWorldSafety',
      upstream_status: 'success',
      record_count: 1,
      transform_version: 'real-world-safety-v0.1',
      source_snapshot_status: 'stored',
      source_pull_id: 'pull-openfda-ndc',
      source_payload_hash: 'payload-openfda-ndc',
    },
  ],
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
      reason: longOfficialReason,
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

function createPublicSafetyResponse(
  query: string,
): RealWorldSafetySearchResponse {
  const normalizedQuery = query.toLocaleLowerCase('en-US')

  if (normalizedQuery === 'advil') {
    return publicSafetyResponse
  }

  if (normalizedQuery === 'mystery item') {
    return {
      ...publicSafetyResponse,
      query,
      raw_query: query,
      query_understanding: {
        ...publicSafetyResponse.query_understanding,
        original_query: query,
        normalized_query: normalizedQuery,
        search_query: normalizedQuery,
        corrections_applied: [],
        expanded_terms: [],
        expansion_search_terms_used: [],
        query_type_hints: ['consumer_product'],
      },
      search_plan: {
        intent: 'consumer_product',
        confidence: 'medium',
        reason: 'The query appears to describe a consumer product, but no matching records were returned.',
        primary_source_ids: ['cpsc_recalls'],
        secondary_source_ids: [],
        sources_to_check: ['cpsc_recalls'],
        clarification_required: false,
      },
      count: 0,
      sources_checked: [
        {
          source_id: 'cpsc_recalls',
          source_name: 'CPSC recalls',
          source_type: 'local curated official snapshot',
          source_url: 'https://www.cpsc.gov/Recalls',
          source_kind: 'public_notice',
          upstream_status: 'empty',
          record_count: 0,
        },
      ],
      sources_failed: [],
      records_per_source: {},
      structured_api_matches: 0,
      public_notice_matches: 0,
      total_matches: 0,
      no_match_explanation:
        'No matching public record was found in the checked U.S. sources. This does not certify that the product is safe.',
      safety_intelligence_summary: {
        ...publicSafetyResponse.safety_intelligence_summary,
        query_type: 'consumer_product',
        recall_or_enforcement_found: false,
        reference_or_label_found: false,
        signal_report_found: false,
        matched_sources_by_role: {
          recall_enforcement: [],
          reference_identity: [],
          label_reference: [],
          signal_report: [],
          other: [],
        },
        checked_sources_by_role: {
          recall_enforcement: ['CPSC recalls'],
          reference_identity: [],
          label_reference: [],
          signal_report: [],
          other: [],
        },
        top_result_titles: [],
        expansion_explanations: [],
        plain_language_summary:
          'No matching public record was found in the returned results from the checked sources.',
        suggested_next_steps: [],
      },
      source_audits: [],
      results: [],
    }
  }

  if (normalizedQuery === 'sunscreen') {
    return {
      ...publicSafetyResponse,
      query,
      raw_query: query,
      query_understanding: {
        ...publicSafetyResponse.query_understanding,
        original_query: query,
        normalized_query: normalizedQuery,
        search_query: normalizedQuery,
        corrections_applied: [],
        expanded_terms: [],
        expansion_search_terms_used: [],
        query_type_hints: ['unknown'],
      },
      search_plan: {
        intent: 'ambiguous',
        confidence: 'low',
        reason: 'The query could refer to more than one safety area.',
        primary_source_ids: [],
        secondary_source_ids: [],
        sources_to_check: [],
        clarification_required: true,
      },
      count: 0,
      sources_checked: [],
      sources_failed: [],
      records_per_source: {},
      structured_api_matches: 0,
      public_notice_matches: 0,
      total_matches: 0,
      no_match_explanation:
        'No matching public record was found in the checked U.S. sources. This does not certify that the product is safe.',
      safety_intelligence_summary: {
        ...publicSafetyResponse.safety_intelligence_summary,
        query_type: 'ambiguous',
        recall_or_enforcement_found: false,
        reference_or_label_found: false,
        signal_report_found: false,
        matched_sources_by_role: {
          recall_enforcement: [],
          reference_identity: [],
          label_reference: [],
          signal_report: [],
          other: [],
        },
        checked_sources_by_role: {
          recall_enforcement: [],
          reference_identity: [],
          label_reference: [],
          signal_report: [],
          other: [],
        },
        top_result_titles: [],
        expansion_explanations: [],
        plain_language_summary:
          'No matching public record was found in the returned results from the checked sources.',
        suggested_next_steps: [],
      },
      source_audits: [],
      results: [],
    }
  }


  return {
    ...publicSafetyResponse,
    query,
    raw_query: query,
    query_understanding: {
      ...publicSafetyResponse.query_understanding,
      original_query: query,
      normalized_query: normalizedQuery,
      search_query: normalizedQuery,
      corrections_applied: [],
      expanded_terms: [],
      expansion_search_terms_used: [],
      query_type_hints: ['consumer_product'],
    },
    search_plan: {
      intent: 'consumer_product',
      confidence: 'high',
      reason: 'The query appears to describe a consumer product.',
      primary_source_ids: ['cpsc_recalls_api'],
      secondary_source_ids: ['fda_recalls_market_withdrawals_safety_alerts'],
      sources_to_check: ['cpsc_recalls_api', 'fda_recalls_market_withdrawals_safety_alerts'],
      clarification_required: false,
    },
    safety_intelligence_summary: {
      ...publicSafetyResponse.safety_intelligence_summary,
      top_result_titles: [`Public safety result for ${query}`],
      expansion_explanations: [],
      plain_language_summary: `Public records returned for ${query}.`,
      suggested_next_steps: [`Verify official source records for ${query}.`],
    },
    results: publicSafetyResponse.results.map((record) => ({
      ...record,
      category: 'Consumer product reference',
      product_name: query,
      brand_name: query,
      title: `Public safety result for ${query}`,
      reason: `Official public record text for ${query}.`,
      hazard_type: 'Public record, not a recall',
      recall_number: null,
      affected_models: [],
      affected_lots: [],
      raw_payload_hash: `hash-${normalizedQuery.replace(/\s+/g, '-')}`,
    })),
  }
}

beforeEach(() => {
  mockSearchRealWorldSafety.mockReset()
  mockSearchRealWorldSafety.mockImplementation(async (query) =>
    createPublicSafetyResponse(query),
  )
  window.history.replaceState(null, '', '/')
})

test('uses the shared safety-area workspace for the empty state', () => {
  const { container } = render(<PublicSafetySearchPage initialQuery="" />)

  expect(
    container.querySelector(
      '.safety-area-page.safety-area-page--public.pharmacy-detail-page.public-safety-page',
    ),
  ).toBeInTheDocument()
  expect(container.querySelector('.pharmacy-overview.public-safety-overview')).toBeInTheDocument()
  expect(container.querySelector('.pharmacy-workspace')).toBeInTheDocument()
  expect(container.querySelector('.pharmacy-recall-panel')).toBeInTheDocument()
  expect(container.querySelector('.pharmacy-insight-rail')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Matched public records' })).toBeInTheDocument()
  expect(screen.getByText('Public records will appear here.')).toBeInTheDocument()
  expect(screen.getByText('What to verify next')).toBeInTheDocument()
  expect(screen.getByText('Safety boundary')).toBeInTheDocument()
})

test('renders a compact Public Safety summary, workspace, and advanced details', async () => {
  const user = userEvent.setup()
  render(<PublicSafetySearchPage initialQuery="" />)

  await user.type(screen.getByLabelText(/Safety record search/i), 'Advil')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  await waitFor(() => {
    expect(mockSearchRealWorldSafety).toHaveBeenCalledWith('Advil', 10, 'score')
  })

  expect(
    await screen.findByRole('heading', { name: 'Matched public records' }),
  ).toBeInTheDocument()
  const summaryStrip = screen.getByLabelText('Summary for Advil')
  expect(screen.getByText(/No matching recall\/enforcement record was found/i)).toBeInTheDocument()
  expect(within(summaryStrip).getByText('Current query')).toBeInTheDocument()
  expect(within(summaryStrip).getByText('Detected area')).toBeInTheDocument()
  expect(within(summaryStrip).getByText('Matches')).toBeInTheDocument()
  expect(within(summaryStrip).getByText('Sources checked')).toBeInTheDocument()
  expect(within(summaryStrip).getByText('Source issues')).toBeInTheDocument()
  expect(within(summaryStrip).getAllByText('1')).toHaveLength(2)
  expect(within(summaryStrip).getByText('drug')).toBeInTheDocument()
  expect(screen.getByText('Some sources could not be checked')).toBeInTheDocument()
  expect(screen.getByText(/Results may be incomplete because one or more public sources had an issue/i)).toBeInTheDocument()
  expect(screen.getByText(/DailyMed SPL API:/i)).toBeInTheDocument()

  expect(screen.getByText('Export')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Download Excel' })).toBeDisabled()
  expect(screen.getByText('Advanced source details')).toBeVisible()
  expect(screen.getByText('Query understanding')).not.toBeVisible()
  expect(screen.getByText('Evidence types found')).not.toBeVisible()
  expect(screen.getByText('Sources checked and verification links')).not.toBeVisible()

  expect(screen.getByText(/Official openFDA NDC Directory drug listing/i)).toBeInTheDocument()
  expect(screen.getByText(/UNIQUE_FULL_LABEL_WARNING_TAIL/i)).not.toBeVisible()

  expect(screen.getByText(/official identity or label reference records/i)).toBeInTheDocument()
  expect(screen.getByText('openFDA NDC listing: Advil (ibuprofen)')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Open official record' })).toHaveAttribute(
    'href',
    'https://api.fda.gov/drug/ndc.json',
  )

  await user.click(screen.getByText(/Official openFDA NDC Directory drug listing/i))
  expect(screen.getByText(/UNIQUE_FULL_LABEL_WARNING_TAIL/i)).toBeInTheDocument()
  expect(screen.queryByText('Record role')).not.toBeInTheDocument()

  await user.click(screen.getByText('Advanced source details'))
  expect(screen.getByText('Query understanding')).toBeVisible()
  expect(screen.getByText('Evidence types found')).toBeVisible()
  expect(screen.getByText('Sources checked and verification links')).toBeVisible()
  expect(screen.getAllByText('Source freshness').length).toBeGreaterThan(0)
  expect(screen.getByText('Pulled and stored')).toBeInTheDocument()
  expect(screen.getByText('Snapshot: stored')).toBeInTheDocument()
  expect(screen.getByText('Source pull stored')).toBeInTheDocument()
  expect(screen.getByText('Payload hash captured')).toBeInTheDocument()
  await user.click(screen.getByText('Query understanding'))
  expect(screen.getByText('Raw query')).toBeVisible()
  expect(
    screen.getAllByText(/Dav AI also checked "ibuprofen" because it is a known related search term/i),
  ).toHaveLength(1)
})

test('shows identifier check guidance from the public safety API response', async () => {
  const user = userEvent.setup()
  render(<PublicSafetySearchPage initialQuery="" />)

  await user.type(screen.getByLabelText(/Safety record search/i), 'Advil')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  expect(await screen.findByText('Identifier check')).toBeInTheDocument()
  const identifierPanel = screen
    .getByText('Identifier check')
    .closest('.public-safety-identifier-card')
  expect(identifierPanel).not.toBeNull()

  const identifierScope = within(identifierPanel as HTMLElement)
  expect(
    identifierScope.getByRole('heading', { name: 'Verify the exact item before acting.' }),
  ).toBeInTheDocument()
  expect(identifierScope.getByText('Verify from returned records')).toBeInTheDocument()
  expect(identifierScope.getByText('Recall or reference number')).toBeInTheDocument()
  expect(identifierScope.getByText('66715-6547')).toBeInTheDocument()
  expect(identifierScope.getByText('Lot, package, or product identifier')).toBeInTheDocument()
  expect(identifierScope.getByText('ibuprofen 200 mg')).toBeInTheDocument()
  expect(
    identifierScope.getByText(/No returned record proves every unit is recalled or safe/i),
  ).toBeInTheDocument()
})

test('labels curated snapshots, live APIs, and live public pages in source metadata', async () => {
  const sourceRecords = [
    {
      source_id: 'cpsc_recalls_api',
      source_name: 'CPSC Recalls API',
      source_type: 'local curated official snapshot',
      source_url: 'local:data/safety_sources/cpsc/cpsc_daily_products_curated_records.json',
      source_kind: 'structured_api' as const,
      upstream_status: 'success',
      record_count: 1,
    },
    {
      source_id: 'nhtsa_recalls_api_datasets',
      source_name: 'NHTSA Recalls API / datasets',
      source_type: 'API',
      source_url: 'https://api.nhtsa.gov/recalls/recallsByVehicle',
      source_kind: 'structured_api' as const,
      upstream_status: 'success',
      record_count: 1,
    },
    {
      source_id: 'fda_recalls_market_withdrawals_safety_alerts',
      source_name: 'FDA Recalls, Market Withdrawals & Safety Alerts',
      source_type: 'public notice page',
      source_url: 'https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts',
      source_kind: 'public_notice' as const,
      upstream_status: 'success',
      record_count: 1,
    },
  ]
  const baseRecord = publicSafetyResponse.results[0]

  mockSearchRealWorldSafety.mockResolvedValueOnce({
    ...publicSafetyResponse,
    query: 'air fryer',
    raw_query: 'air fryer',
    count: 3,
    total_matches: 3,
    sources_checked: sourceRecords,
    results: sourceRecords.map((source, index) => ({
      ...baseRecord,
      source_name: source.source_name,
      source_type: source.source_type,
      source_url: source.source_url,
      source_kind: source.source_kind,
      title: `${source.source_name} result`,
      raw_payload_hash: `source-mode-${index}`,
    })),
  })

  render(<PublicSafetySearchPage initialQuery="air fryer" />)

  expect(await screen.findByText('CPSC Recalls API result')).toBeInTheDocument()
  expect(screen.getAllByText('Curated official snapshot').length).toBeGreaterThan(0)
  expect(screen.getAllByText('Live public API').length).toBeGreaterThan(0)
  expect(screen.getAllByText('Live public page').length).toBeGreaterThan(0)
})

test('keeps edited draft input separate from submitted Public Safety results', async () => {
  const user = userEvent.setup()
  window.history.replaceState(null, '', '/?page=public-safety&q=air+fryer')

  render(<PublicSafetySearchPage initialQuery="air fryer" />)

  expect(
    await screen.findByRole('heading', { name: 'Matched public records' }),
  ).toBeInTheDocument()
  expect(screen.getByText('Public records returned for air fryer.')).toBeInTheDocument()
  expect(new URLSearchParams(window.location.search).get('q')).toBe('air fryer')

  const input = screen.getByLabelText(/Safety record search/i)
  expect(input).toHaveValue('air fryer')

  await user.clear(input)
  await user.type(input, 'refrigerator')

  expect(input).toHaveValue('refrigerator')
  expect(
    screen.getByText(/Showing 1 of 1 returned record for air fryer/i),
  ).toBeInTheDocument()
  expect(screen.getByText('Public records returned for air fryer.')).toBeInTheDocument()
  expect(
    screen.getByText(
      'Showing results for air fryer. Search refrigerator to update results.',
    ),
  ).toBeInTheDocument()
  expect(new URLSearchParams(window.location.search).get('q')).toBe('air fryer')

  await user.click(screen.getByRole('button', { name: 'Search' }))

  await waitFor(() => {
    expect(mockSearchRealWorldSafety).toHaveBeenLastCalledWith('refrigerator', 10, 'score')
  })
  expect(
    await screen.findByText(/Showing 1 of 1 returned record for refrigerator/i),
  ).toBeInTheDocument()
  expect(screen.getByText('Public records returned for refrigerator.')).toBeInTheDocument()
  expect(
    screen.queryByText(
      'Showing results for air fryer. Search refrigerator to update results.',
    ),
  ).not.toBeInTheDocument()
  expect(new URLSearchParams(window.location.search).get('q')).toBe('refrigerator')
})

test('submits Public Safety quick chips immediately and updates the URL query', async () => {
  const user = userEvent.setup()
  render(<PublicSafetySearchPage initialQuery="" />)

  await user.click(screen.getByRole('button', { name: 'air fryer' }))

  await waitFor(() => {
    expect(mockSearchRealWorldSafety).toHaveBeenLastCalledWith('air fryer', 10, 'score')
  })
  expect(
    await screen.findByText(/Showing 1 of 1 returned record for air fryer/i),
  ).toBeInTheDocument()
  expect(screen.getByLabelText(/Safety record search/i)).toHaveValue('air fryer')
  expect(new URLSearchParams(window.location.search).get('q')).toBe('air fryer')
})

test('shows Vehicle Recall Check guidance on the empty Public Safety workspace', () => {
  render(<PublicSafetySearchPage initialQuery="" />)

  expect(screen.getByText('Vehicle Recall Check')).toBeInTheDocument()
  expect(
    screen.getByRole('heading', { name: 'Search by year, make, model, or VIN.' }),
  ).toBeInTheDocument()
  expect(screen.getByRole('button', { name: '2018 Toyota Camry' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: '2020 Honda Civic' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: '4T1B11HK5JU000001' })).toBeInTheDocument()
  expect(
    screen.getByText(/Always verify the exact VIN and campaign status on the official NHTSA page/i),
  ).toBeInTheDocument()
})

test('submits Vehicle Recall Check examples through Public Safety search', async () => {
  const user = userEvent.setup()
  render(<PublicSafetySearchPage initialQuery="" />)

  await user.click(screen.getByRole('button', { name: '2018 Toyota Camry' }))

  await waitFor(() => {
    expect(mockSearchRealWorldSafety).toHaveBeenLastCalledWith(
      '2018 Toyota Camry',
      10,
      'score',
    )
  })
  expect(screen.getByLabelText(/Safety record search/i)).toHaveValue('2018 Toyota Camry')
  expect(new URLSearchParams(window.location.search).get('q')).toBe('2018 Toyota Camry')
})

test('keeps the shared Priority and Latest controls wired to Public Safety sorting', async () => {
  const user = userEvent.setup()
  render(<PublicSafetySearchPage initialQuery="Advil" />)

  await screen.findByRole('heading', { name: 'Matched public records' })
  expect(screen.getByRole('button', { name: 'Priority' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )

  await user.click(screen.getByRole('button', { name: 'Latest' }))

  await waitFor(() => {
    expect(mockSearchRealWorldSafety).toHaveBeenLastCalledWith('Advil', 10, 'latest')
  })
  expect(screen.getByRole('button', { name: 'Latest' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
})


test('shows a clarification state for ambiguous Public Safety searches', async () => {
  const user = userEvent.setup()
  render(<PublicSafetySearchPage initialQuery="" />)

  await user.type(screen.getByLabelText(/Safety record search/i), 'sunscreen')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  expect(
    await screen.findByRole('heading', { name: 'Choose a safety area to continue' }),
  ).toBeInTheDocument()
  expect(screen.getByText(/did not run a broad source sweep/i)).toBeInTheDocument()
  expect(screen.getByText('Not checked yet')).toBeInTheDocument()
  expect(screen.getByText('Advanced source details')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Download Excel' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Consumer product recall' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Drug / OTC label' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Food or supplement' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Cosmetic product' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Medical device' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Vehicle' })).toBeInTheDocument()
  expect(screen.queryByText('No returned records')).not.toBeInTheDocument()
})


test('sets Public Safety assistant context after a successful search', async () => {
  const user = userEvent.setup()
  const setAssistantContext = vi.fn()

  render(
    <PublicSafetySearchPage
      initialQuery=""
      setAssistantContext={setAssistantContext}
    />,
  )

  await user.type(screen.getByLabelText(/Safety record search/i), 'Advil')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  await waitFor(() => {
    expect(setAssistantContext).toHaveBeenCalledWith(
      expect.objectContaining({
        module: 'public_safety',
        page_context: expect.objectContaining({
          query: 'Advil',
          count: 1,
          source_name: 'DavAI Public Safety Search',
          endpoint: '/api/v1/real-world-safety/search',
          audit_id: 'audit-openfda-ndc',
          public_safety: expect.objectContaining({
            summary: expect.objectContaining({
              query_type: 'drug',
              reference_or_label_found: true,
            }),
            top_records: expect.arrayContaining([
              expect.objectContaining({
                title: 'openFDA NDC listing: Advil (ibuprofen)',
                source_name: 'openFDA NDC Directory API',
                product_name: 'Advil',
              }),
            ]),
          }),
        }),
      }),
    )
  })

  const latestContextCall = setAssistantContext.mock.calls
    .map((call) => call[0])
    .filter(Boolean)
    .at(-1)

  expect(JSON.stringify(latestContextCall)).not.toContain('raw_payload_hash')
  expect(JSON.stringify(latestContextCall)).not.toContain('hash-advil')
})

test('clears Public Safety assistant context when a search returns no matches', async () => {
  const user = userEvent.setup()
  const setAssistantContext = vi.fn()

  render(
    <PublicSafetySearchPage
      initialQuery=""
      setAssistantContext={setAssistantContext}
    />,
  )

  await user.type(screen.getByLabelText(/Safety record search/i), 'mystery item')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  await waitFor(() => {
    expect(mockSearchRealWorldSafety).toHaveBeenCalledWith('mystery item', 10, 'score')
  })

  await waitFor(() => {
    expect(setAssistantContext).toHaveBeenLastCalledWith(null)
  })

  expect(
    await screen.findByText(/No matching public records were returned from the checked sources/i),
  ).toBeInTheDocument()
  expect(screen.getByText(/This does not prove the item is safe/i)).toBeInTheDocument()
  expect(screen.getByText(/Search the exact brand, product name, model, or manufacturer/i)).toBeInTheDocument()
})

test('clears Public Safety assistant context when a search fails', async () => {
  const user = userEvent.setup()
  const setAssistantContext = vi.fn()
  mockSearchRealWorldSafety.mockRejectedValueOnce(new Error('source unavailable'))

  render(
    <PublicSafetySearchPage
      initialQuery=""
      setAssistantContext={setAssistantContext}
    />,
  )

  await user.type(screen.getByLabelText(/Safety record search/i), 'battery')
  await user.click(screen.getByRole('button', { name: 'Search' }))

  await waitFor(() => {
    expect(mockSearchRealWorldSafety).toHaveBeenCalledWith('battery', 10, 'score')
  })

  await waitFor(() => {
    expect(setAssistantContext).toHaveBeenLastCalledWith(null)
  })

  expect(
    await screen.findByText(/Unable to load public safety records/i),
  ).toBeInTheDocument()
})
