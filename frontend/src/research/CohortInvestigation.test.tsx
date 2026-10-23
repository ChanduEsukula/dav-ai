import { render, screen, fireEvent } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ResearchProWorkspace from './ResearchProWorkspace'
import type { Candidate } from './contracts'
import { MAX_COHORT_LIMIT, type CohortItem } from './cohort'

const makeCandidate = (id: string, name: string): Candidate => ({
  product_ref: `ref_${id}`,
  brand_names: [name],
  generic_name: name.toLowerCase(),
  strength: '10 mg',
  dosage_form: 'TABLET',
  routes: ['ORAL'],
  active_ingredients: [name.toLowerCase()],
  product_ndcs: [`0000-${id}`],
  package_ndcs: [`0000-${id}-01`],
})

describe('Research Pro Cohort Investigation Workflow', () => {
  let mockCohort: CohortItem[] = []
  const setCohort = vi.fn((updater) => {
    mockCohort = typeof updater === 'function' ? updater(mockCohort) : updater
  })

  const baseProps = {
    session: {
      session_id: 'sess_1',
      capability: 'cap_1',
      expires_in: 600,
      models: ['qwen3.5:4b-q4_K_M', 'llama3.2:3b'],
      model_runtime: 'available' as const,
    },
    pairing: '',
    setPairing: vi.fn(),
    onConnect: vi.fn(),
    query: '',
    setQuery: vi.fn(),
    onSearch: vi.fn(),
    candidates: null,
    incomplete: false,
    choice: '',
    setChoice: vi.fn(),
    onConfirm: vi.fn(),
    product: null,
    question: '',
    setQuestion: vi.fn(),
    selectedCategories: ['labels', 'recalls', 'faers'],
    toggleCategory: vi.fn(),
    model: '',
    setModel: vi.fn(),
    models: ['qwen3.5:4b-q4_K_M'],
    onRunResearch: vi.fn(),
    onCancelResearch: vi.fn(),
    onResetSession: vi.fn(),
    running: false,
    attempted: false,
    result: null,
    busy: '',
    error: '',
    cohort: [] as CohortItem[],
    setCohort,
  }

  beforeEach(() => {
    mockCohort = []
    vi.clearAllMocks()
  })

  it('renders empty cohort state with instructional guidance', () => {
    render(<ResearchProWorkspace {...baseProps} cohort={[]} />)

    expect(screen.getByText('No products in research cohort.')).toBeInTheDocument()
    expect(
      screen.getByText(/Search on the left to add up to 50 pharmaceutical products/i)
    ).toBeInTheDocument()
    expect(screen.getByText('0 / 50 selected')).toBeInTheDocument()
  })

  it('adds candidate products to the cohort tray and increments count', () => {
    const candidateA = makeCandidate('0001', 'Lipitor')
    const { rerender } = render(
      <ResearchProWorkspace {...baseProps} candidates={[candidateA]} cohort={[]} />
    )

    const addBtn = screen.getByRole('button', { name: /\+ add to cohort/i })
    fireEvent.click(addBtn)

    expect(setCohort).toHaveBeenCalled()
    expect(mockCohort).toHaveLength(1)
    expect(mockCohort[0].brand_names).toContain('Lipitor')

    // Rerender with updated cohort
    rerender(
      <ResearchProWorkspace
        {...baseProps}
        candidates={[candidateA]}
        cohort={mockCohort}
      />
    )
    expect(screen.getByText('1 / 50 selected')).toBeInTheDocument()
    expect(screen.getByText('In Cohort')).toBeDisabled()
  })

  it('prevents duplicate additions to the cohort and alerts user', () => {
    const candidateA = makeCandidate('0001', 'Lipitor')
    const existingCohort: CohortItem[] = [
      {
        id: '0000-0001',
        brand_names: ['Lipitor'],
        generic_name: 'atorvastatin',
        strength: '10 mg',
        dosage_form: 'TABLET',
        routes: ['ORAL'],
        product_ndcs: ['0000-0001'],
        package_ndcs: ['0000-0001-01'],
        active_ingredients: ['atorvastatin'],
        label_status: 'Not evaluated',
        recall_status: 'Not evaluated',
        faers_status: 'Not evaluated',
        coverage_summary: 'Frozen release',
        last_research_status: 'Not evaluated',
        added_at: new Date().toISOString(),
      },
    ]

    render(
      <ResearchProWorkspace
        {...baseProps}
        candidates={[candidateA]}
        cohort={existingCohort}
      />
    )

    expect(screen.getByRole('button', { name: 'In Cohort' })).toBeDisabled()
  })

  it('strictly enforces the 50-product maximum cohort limit', () => {
    const fullCohort: CohortItem[] = Array.from({ length: MAX_COHORT_LIMIT }, (_, i) => ({
      id: `0000-${i}`,
      brand_names: [`Drug ${i}`],
      generic_name: `drug_${i}`,
      strength: '10 mg',
      dosage_form: 'TABLET',
      routes: ['ORAL'],
      product_ndcs: [`0000-${i}`],
      package_ndcs: [],
      active_ingredients: [`ingredient_${i}`],
      label_status: 'Not evaluated',
      recall_status: 'Not evaluated',
      faers_status: 'Not evaluated',
      coverage_summary: 'Frozen release',
      last_research_status: 'Not evaluated',
      added_at: new Date().toISOString(),
    }))

    const candidate51 = makeCandidate('9999', 'Extra Drug')
    render(
      <ResearchProWorkspace
        {...baseProps}
        candidates={[candidate51]}
        cohort={fullCohort}
      />
    )

    expect(screen.getByText('50 / 50 selected')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /\+ add to cohort/i })).toBeDisabled()
  })

  it('allows removing an individual product from the cohort', () => {
    const item1: CohortItem = {
      id: '0000-1111',
      brand_names: ['Drug To Remove'],
      generic_name: 'test',
      strength: '10 mg',
      dosage_form: 'TABLET',
      routes: ['ORAL'],
      product_ndcs: ['0000-1111'],
      package_ndcs: [],
      active_ingredients: ['test'],
      label_status: 'Not evaluated',
      recall_status: 'Not evaluated',
      faers_status: 'Not evaluated',
      coverage_summary: 'Frozen',
      last_research_status: 'Not evaluated',
      added_at: new Date().toISOString(),
    }

    render(<ResearchProWorkspace {...baseProps} cohort={[item1]} />)

    const removeBtn = screen.getByRole('button', {
      name: /remove drug to remove from cohort/i,
    })
    fireEvent.click(removeBtn)

    expect(setCohort).toHaveBeenCalled()
  })

  it('renders honest batch execution boundary notice and distinct "Not evaluated" status badges', () => {
    const item: CohortItem = {
      id: '0000-2222',
      brand_names: ['Metformin XR'],
      generic_name: 'metformin',
      strength: '500 mg',
      dosage_form: 'EXTENDED RELEASE TABLET',
      routes: ['ORAL'],
      product_ndcs: ['0000-2222'],
      package_ndcs: [],
      active_ingredients: ['metformin hydrochloride'],
      label_status: 'Not evaluated',
      recall_status: 'Not evaluated',
      faers_status: 'Not evaluated',
      coverage_summary: 'Frozen',
      last_research_status: 'Not evaluated',
      added_at: new Date().toISOString(),
    }

    render(<ResearchProWorkspace {...baseProps} cohort={[item]} />)

    // Verify boundary callout
    expect(screen.getByText(/batch execution boundary notice:/i)).toBeInTheDocument()
    expect(
      screen.getByText(/simultaneous 50-product background agent execution is not enabled/i)
    ).toBeInTheDocument()

    // Verify "Not evaluated" badges in the table
    const notEvaluatedBadges = screen.getAllByText('Not evaluated')
    expect(notEvaluatedBadges.length).toBeGreaterThanOrEqual(4) // Label, Recall, FAERS, Last Research
  })
})
