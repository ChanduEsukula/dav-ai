import {
  fireEvent,
  render,
  screen,
} from '@testing-library/react'
import {
  beforeEach,
  expect,
  test,
  vi,
} from 'vitest'

import AskStoredDrug from './AskStoredDrug'
import {
  askStoredDrug,
  type AskDrugResponse,
} from '../api/drugCatalog'

vi.mock('../api/drugCatalog', () => ({
  askStoredDrug: vi.fn(),
}))

const response: AskDrugResponse = {
  answer:
    'Stored release evidence: Fixture warning [S1]',
  evidence_count: 1,

  limitations: [
    'Frozen release evidence only.',
  ],

  status: 'answered',
  answer_mode: 'verified_release_evidence',

  citations: [
    {
      id: 'S1',
      record_id: 'label:test',
      type: 'labels',
      title: 'Boxed warning',
      text: 'Fixture warning',
      source: 'openfda_drug_label',
      source_record_id: 'fixture',
      source_url:
        'https://api.fda.gov/drug/label.json?search=id:fixture',
      source_date: '2026-08-28',
      source_date_type: 'effective_date',
    },
  ],

  coverage: {
    labels: {
      state: 'READY',
      reason_code:
        'SELECTED_PRODUCT_SCOPED_STORED_LABEL',
      scope: 'PRODUCT',
      as_of_date: '2026-09-25',
      source_date: '2026-09-25',
      measured_count: 1,
      unresolved_count: 0,
      limitations: [
        'Stored label evidence is product-specific.',
      ],
    },
  },
}

beforeEach(() => {
  vi.clearAllMocks()

  vi.mocked(
    askStoredDrug,
  ).mockResolvedValue(response)
})

test(
  'asks for selected drug and renders grounded release evidence',
  async () => {
    render(
      <AskStoredDrug drugId="selected-drug" />,
    )

    fireEvent.change(
      screen.getByLabelText(
        'Question about this selected drug',
      ),
      {
        target: {
          value:
            'What warnings are stored?',
        },
      },
    )

    fireEvent.click(
      screen.getByRole('button', {
        name: 'Ask from stored evidence',
      }),
    )

    expect(
      await screen.findByText(
        /Stored release evidence/,
      ),
    ).toBeInTheDocument()

    expect(
      askStoredDrug,
    ).toHaveBeenCalledWith(
      'selected-drug',
      'What warnings are stored?',
    )

    expect(
      screen.getByRole('link', {
        name:
          'Open cited official source [S1]',
      }),
    ).toHaveAttribute(
      'href',
      response.citations[0].source_url,
    )

    expect(
      screen.getByText(
        /Coverage state:/,
      ),
    ).toHaveTextContent('READY')

    expect(
      screen.getByText(
        /does not determine whether a drug caused/,
      ),
    ).toBeInTheDocument()
  },
)

test(
  'honest insufficient release evidence has no citations',
  async () => {
    vi.mocked(
      askStoredDrug,
    ).mockResolvedValue({
      ...response,
      status: 'insufficient_evidence',
      answer:
        'Dav AI does not have enough stored release evidence to answer that question.',
      citations: [],
      evidence_count: 0,
      coverage: {
        recalls: {
          state: 'UNKNOWN',
          reason_code:
            'NO_VERIFIED_RECALL_LINK',
          scope:
            'EXPLICIT_TEXT_NDC_PRODUCT_APPLICABILITY',
          as_of_date: '2026-09-26',
          source_date: '2026-09-25',
          measured_count: null,
          unresolved_count: null,
          limitations: [
            'Absence of an edge is not proof of no historical recalls.',
          ],
        },
      },
    })

    render(
      <AskStoredDrug drugId="selected-drug" />,
    )

    fireEvent.click(
      screen.getByRole('button', {
        name:
          'Have there been recalls in this release?',
      }),
    )

    expect(
      await screen.findByText(
        /does not have enough stored release evidence/,
      ),
    ).toBeInTheDocument()

    expect(
      screen.queryByRole('link'),
    ).not.toBeInTheDocument()

    expect(
      screen.getByText(
        /Coverage state:/,
      ),
    ).toHaveTextContent('UNKNOWN')
  },
)

test(
  'provider or route failure leaves stored evidence guidance',
  async () => {
    vi.mocked(
      askStoredDrug,
    ).mockRejectedValue(
      new Error('offline'),
    )

    render(
      <AskStoredDrug drugId="selected-drug" />,
    )

    fireEvent.click(
      screen.getByRole('button', {
        name:
          'What warnings are stored for this drug?',
      }),
    )

    expect(
      await screen.findByRole('alert'),
    ).toHaveTextContent(
      'still review the frozen stored evidence sections',
    )
  },
)
