import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, expect, test, vi } from 'vitest'
import StoredDrugCatalog from './StoredDrugCatalog'
import { getSemaglutideRelease, getStoredDrug, searchCatalog } from '../api/drugCatalog'

vi.mock('../api/drugCatalog', () => ({ getStoredDrug: vi.fn(), searchCatalog: vi.fn(), getSemaglutideRelease: vi.fn() }))
const provenance = {
  source: 'openfda_ndc_directory',
  source_id: 'source:test',
  source_record_id: 'test-source',
  source_url: 'https://api.fda.gov/drug/ndc.json',
  observed_at: '2026-09-26T10:00:00Z',
}

const drug = {
  id: 'drug',
  product_id: 'drug',
  generic_name: 'semaglutide',
  brand_names: ['Example brand'],
  active_ingredients: ['semaglutide'],
  ingredient_ids: ['ingredient:test'],
  strength: '1 mg',
  dosage_form: 'Injection',
  routes: ['Subcutaneous'],
  manufacturers: ['Example labeler'],
  product_ndcs: ['12345-1234'],
  package_ndcs: [],
  rxcui: null,
  rxcuis: [
    {
      value: '123456',
      concept_type: 'UNKNOWN',
      is_unique_product: false,
      has_conflict: true,
    },
  ],
  is_combination: false,
  identity_partial: false,
  formulation_id: 'formulation:test',
  application_number: 'NDA000001',
  product_type: 'HUMAN PRESCRIPTION DRUG',
  marketing_category: 'NDA',
  consumer_classification: 'NORMAL_CONSUMER_HUMAN_PRODUCT',
  provenance,
}

const coverage = {
  state: 'READY',
  reason_code: 'TEST_READY',
  scope: 'FROZEN_TEST_SCOPE',
  as_of_date: '2026-09-26',
  source_date: '2026-09-25',
  measured_count: 1,
  unresolved_count: 0,
  stored_record_count: 1,
  bounded: true,
  truncated: false,
  empty_message:
    'No verified linked record is stored in this test release.',
  limitations: ['Test release limitation.'],
}

const ingredientCoverage = {
  ingredient_id: 'ingredient:test',
  state: 'READY',
  reason_code: 'SCOPED_INGREDIENT_ANALYTICS_AVAILABLE',
  scope: 'DEDUPLICATED_INGREDIENT_REPORT_ANALYTICS',
  as_of_date: '2026-09-26',
  source_date: '2026-09-23',
  measured_count: 1,
  unresolved_count: 0,
  limitations: [
    'Ingredient analytics are descriptive and non-causal.',
  ],
}

const label = {
  id: 'label',
  label_set_id: 'set-test',
  label_version: '2',
  effective_date: '2026-08-28',
  applicability_class: 'EXACT_PRODUCT',
  match_method: 'EXACT_NDC',
  matched_value: '12345-1234',
  evidence_scope: 'PRODUCT',

  boxed_warning: 'Stored warning',
  warnings_and_precautions: 'Stored warnings and precautions',
  warnings: null,
  contraindications: 'Stored contraindications',
  adverse_reactions: 'Stored adverse reactions',
  drug_interactions: 'Stored interactions',

  section_states: {
    boxed_warning: {
      text: 'Stored warning',
      field_present: true,
      state: 'READY',
      reason_code: 'EXACT_SOURCE_TEXT_PRESERVED',
    },
    warnings: {
      text: null,
      field_present: false,
      state: 'UNAVAILABLE',
      reason_code: 'SOURCE_FIELD_NOT_PRESENT',
    },
  },

  source: 'openfda_drug_label',
  source_record_id: 'label-source',
  source_url: 'https://api.fda.gov/drug/label.json',
}

const recall = {
  id: 'recall',
  recall_number: 'R-TEST',
  product_description: 'Stored recall',
  reason_for_recall: 'Source reason',
  classification: 'Class II',
  reported_status: 'Ongoing',
  recalling_firm: 'Example firm',
  recall_initiation_date: '2026-01-01',
  report_date: '2026-01-02',
  distribution_pattern: 'Nationwide',
  lot_information: 'Lot A',
  lot_scope: 'UNKNOWN',
  applicability_class: 'EXACT_PACKAGE',
  match_method: 'EXACT_PACKAGE_NDC',
  matched_value: '12345-1234-01',

  source: 'openfda_drug_enforcement',
  source_record_id: 'recall-source',
  source_url: 'https://api.fda.gov/drug/enforcement.json',
}

const detail = {
  drug,

  safety: {
    drug_id: 'drug',

    labels: {
      records: [label],
      latest_records: [label],
      coverage,
    },

    recalls: {
      records: [recall],
      coverage,
    },

    communications: {
      records: [],
      coverage: {
        ...coverage,
        state: 'UNKNOWN',
        reason_code: 'NO_VERIFIED_COMMUNICATION_LINK',
        measured_count: null,
        stored_record_count: 0,
      },
    },

    adverse_events: {
      records: [
        {
          ingredient_id: 'ingredient:test',
          ingredient_name: 'semaglutide',
          scope: 'INGREDIENT',

          analytics: {
            window_start: '2020-01-01',
            window_end: '2026-06-30',

            report_count: 1,
            unique_case_count: 1,
            serious_report_count: 1,
            serious_known_report_count: 1,

            death_report_count: 0,
            hospitalization_report_count: 0,
            disability_report_count: 0,
            life_threatening_report_count: 0,

            suspect_report_count: 1,
            concomitant_report_count: 0,
            interacting_report_count: 0,

            active_month_count: 1,
            reaction_term_count: 1,
            co_report_activity: 1,

            count_unit: 'REPORT',
            date_basis: 'LAST_RECEIVED',

            limitations: [
              'Non-causal descriptive analytics.',
            ],
          },

          top_reported_reactions: [
            {
              reaction: 'Nausea',
              co_report_activity: 1,
              active_months: 1,
              rank: 1,
            },
          ],

          coverage: ingredientCoverage,
        },
      ],

      coverage,

      summary: {
        scope: 'INGREDIENT_COMPONENTS_ONLY',
        ingredient_count: 1,
        ingredients_with_analytics: 1,
        ingredients_without_analytics: 0,
        product_report_total: null,
        limitation:
          'Dav AI does not sum ingredient FAERS counts into a product-level adverse-event total. These are descriptive ingredient-level co-reporting associations, not incidence or causality.',
      },
    },
  },

  timeline: [],
}

const semaglutideRelease = {
  schema_version: 'dav-ai-semaglutide-snapshot-v1',
  artifact_version: '0.1-manual',
  drug: {
    display_name: 'Semaglutide',
    canonical_name: 'semaglutide',
    ingredient_id: 'ingredient:aceb6dacee359207f1939f8b',
    cohort_rank: 14,
    cohort_version: 'DAV_AI_100_V1',
    identity_status: 'VERIFIED',
    mapping_confidence: 'EXACT',
    is_combination: false,
    source_product_count: 142,
    product_ndc_count: 104,
    associated_rxcui_count: 23,
    mapping_source: 'openFDA NDC directory identity snapshot',
  },
  analytics: {
    scope: 'ingredient-level retrospective co-reporting aggregates',
    source: 'FAERS-derived monthly aggregates',
    start_month: '2020-01-01',
    end_month: '2026-06-01',
    ingredient_reaction_month_rows: 30216,
    distinct_reaction_terms: 4264,
    months: 78,
    pair_report_activity: 97481,
    monthly: [],
    top_reactions: [],
    interpretation: 'Counts represent ingredient-reaction co-reporting activity and do not establish causality, incidence, patient risk, or unique-patient counts.',
  },
  regulatory_evidence: {
    scope: 'product-specific',
    verified_label_count: 4,
    classification: 'EXACT_PRODUCT',
    labels: [],
    note: 'Label evidence applies only to listed product/formulation associations.',
  },
  recalls: {
    coverage_status: 'UNKNOWN',
    verified_applicable_records: null,
    note: 'No verified recall classifications were established by this release audit; this must not be interpreted as zero recalls.',
  },
  coverage: {
    identity: 'READY',
    co_reporting_analytics: 'READY',
    product_label_applicability: 'READY',
    label_text: 'READY',
    recalls: 'UNKNOWN',
    report_level_2020plus_outcomes: 'PARTIAL',
    safety_communications: 'PARTIAL',
    ml_ranking: 'NOT_INCLUDED',
  },
  limitations: [
    'Co-reporting summaries are retrospective and are not causal safety findings.',
  ],
  sources: {
    cohort: 'data/cohorts/dav_ai_100_v1.csv',
    analytics: 'data/derived/dav_ai_100_v1/monthly_2020plus.parquet',
    regulatory_audit: 'docs/evidence/regulatory-applicability/audit.json',
    label_bulk_cache: 'data/pharma_bulk_cache/example',
  },
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(getSemaglutideRelease).mockResolvedValue(semaglutideRelease)
  vi.mocked(searchCatalog).mockResolvedValue({ results: [drug], count: 1 })
  vi.mocked(getStoredDrug).mockResolvedValue(detail)
})
test('all seven tabs expose frozen release evidence and limitations', async () => {
  render(<StoredDrugCatalog initialQuery="metformin" />)

  fireEvent.click(
    await screen.findByRole('button', {
      name: /semaglutide.*Example brand/,
    }),
  )

  await screen.findByRole('tab', { name: 'OVERVIEW' })

  expect(screen.getAllByRole('tab')).toHaveLength(7)

  expect(
    screen.getByText(/1 associated/),
  ).toBeInTheDocument()

  fireEvent.click(
    screen.getByRole('tab', { name: 'LABEL' }),
  )

  expect(
    screen.getByText('Stored warning'),
  ).toBeInTheDocument()

  expect(
    screen.getByText(/Coverage state: READY/),
  ).toBeInTheDocument()

  expect(
    screen.getByRole('link', {
      name: 'Open official source',
    }),
  ).toHaveAttribute(
    'href',
    label.source_url,
  )

  fireEvent.click(
    screen.getByRole('tab', { name: 'RECALLS' }),
  )

  expect(
    screen.getByText(/Reported status: Ongoing/),
  ).toBeInTheDocument()

  expect(
    screen.getByText(/Lot A/),
  ).toBeInTheDocument()

  fireEvent.click(
    screen.getByRole('tab', {
      name: 'ADVERSE EVENTS',
    }),
  )

  expect(
    screen.getByText(
      /Ingredient-level adverse-event analytics/,
    ),
  ).toBeInTheDocument()

  expect(
    screen.getByText(
      /does not sum ingredient FAERS counts/,
    ),
  ).toBeInTheDocument()

  expect(
    screen.getByText(
      /1 deduplicated ingredient-report associations/,
    ),
  ).toBeInTheDocument()

  expect(
    screen.getByText(
      /Nausea: 1 co-report activity/,
    ),
  ).toBeInTheDocument()

  fireEvent.click(
    screen.getByRole('tab', { name: 'SAFETY' }),
  )

  expect(
    screen.getByText(
      'No verified linked record is stored in this test release.',
    ),
  ).toBeInTheDocument()

  fireEvent.click(
    screen.getByRole('tab', { name: 'TIMELINE' }),
  )

  expect(
    screen.getByText(
      /Only dated evidence from the frozen release/,
    ),
  ).toBeInTheDocument()

  fireEvent.click(
    screen.getByRole('tab', { name: 'SOURCES' }),
  )

  expect(
    screen.getAllByText(
      /Scope: FROZEN_TEST_SCOPE/,
    ),
  ).toHaveLength(4)
})

test('same search can retry after failure', async () => {
  vi.mocked(searchCatalog).mockRejectedValueOnce(new Error('offline'))
  render(<StoredDrugCatalog initialQuery="metformin" />)
  await screen.findByRole('alert')
  fireEvent.click(screen.getByRole('button', { name: 'Search stored data' }))
  await screen.findByRole('button', { name: /semaglutide.*Example brand/ })
  expect(searchCatalog).toHaveBeenCalledTimes(2)
})
test('detail failure has a working retry', async () => {
  vi.mocked(getStoredDrug).mockRejectedValueOnce(new Error('offline'))
  render(<StoredDrugCatalog initialQuery="metformin" />)
  fireEvent.click(await screen.findByRole('button', { name: /semaglutide.*Example brand/ }))
  fireEvent.click(await screen.findByRole('button', { name: 'Retry details' }))
  await screen.findByRole('tab', { name: 'LABEL' })
  expect(getStoredDrug).toHaveBeenCalledTimes(2)
})

test('Semaglutide uses the compact release path without legacy catalog calls', async () => {
  render(<StoredDrugCatalog initialQuery="semaglutide" />)

  expect(await screen.findByText('Semaglutide')).toBeInTheDocument()

  expect(searchCatalog).not.toHaveBeenCalled()
  expect(getStoredDrug).not.toHaveBeenCalled()

  expect(screen.getByRole('tab', { name: 'CO-REPORTING ACTIVITY' })).toBeInTheDocument()
  expect(screen.getByRole('tab', { name: 'LABELS' })).toBeInTheDocument()
  expect(screen.getByRole('tab', { name: 'RECALLS / COVERAGE' })).toBeInTheDocument()
})
