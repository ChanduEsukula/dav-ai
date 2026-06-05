import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, test, vi } from 'vitest'
import AuditHistoryPage from './AuditHistoryPage'
import { getAuditEventSourcePull, getAuditEvents } from '../api/auditEvents'

vi.mock('../api/auditEvents', () => ({
  getAuditEvents: vi.fn(),
  getAuditEventSourcePull: vi.fn(),
}))

const mockedGetAuditEvents = vi.mocked(getAuditEvents)
const mockedGetAuditEventSourcePull = vi.mocked(getAuditEventSourcePull)

const rawPayloadVisibilityMessage =
  'Raw public-source payloads are stored for reproducibility and audit provenance, but are intentionally not displayed in the UI.'

const mockAuditItems = [
  {
    audit_id: '11111111-1111-4111-8111-111111111111',
    module: 'RecallRadar',
    source_id: 'openfda_drug_enforcement',
    source_name: 'openFDA Drug Enforcement API',
    endpoint: 'https://api.fda.gov/drug/enforcement.json',
    query: 'eye drops',
    query_params: {
      q: 'eye drops',
      limit: 5,
    },
    retrieval_timestamp: '2026-05-01T10:30:00Z',
    upstream_status: 'success',
    record_count: 1,
    transform_version: 'recall-transform-v0.1',
    score_version: 'recall-risk-v0.1',
    disclaimer_version: 'disclaimer-v0.1',
    error_message: null,
    created_at: '2026-05-05T00:08:55.761053Z',
  },
  {
    audit_id: '22222222-2222-4222-8222-222222222222',
    module: 'DrugSignal',
    source_id: 'openfda_drug_event',
    source_name: 'openFDA Drug Event API',
    endpoint: 'https://api.fda.gov/drug/event.json',
    query: 'metformin',
    query_params: {
      q: 'metformin',
      limit: 5,
    },
    retrieval_timestamp: '2026-05-01T20:30:00Z',
    upstream_status: 'success',
    record_count: 2,
    transform_version: 'drug-event-transform-v0.1',
    score_version: null,
    disclaimer_version: 'disclaimer-v0.1',
    error_message: null,
    created_at: '2026-05-05T00:08:54.412057Z',
  },
]

const mockSourcePull = {
  pull_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  audit_id: '11111111-1111-4111-8111-111111111111',
  source_id: 'openfda_drug_enforcement',
  source_name: 'openFDA Drug Enforcement API',
  endpoint: 'https://api.fda.gov/drug/enforcement.json',
  query: 'eye drops',
  query_params: {
    q: 'eye drops',
    limit: 5,
  },
  retrieval_timestamp: '2026-05-01T10:30:00Z',
  upstream_status: 'success',
  record_count: 1,
  payload_hash: 'a'.repeat(64),
  transform_version: 'recall-transform-v0.1',
  created_at: '2026-05-05T00:08:55.761053Z',
  snapshot_id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
}

describe('AuditHistoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    window.history.replaceState(null, '', '/')
    mockedGetAuditEventSourcePull.mockResolvedValue({
      status: 'not_found',
      persistence_available: true,
      item: null,
      message: 'No source pull found for this audit_id.',
    })
  })

  test('renders loading state before audit history resolves', () => {
    mockedGetAuditEvents.mockReturnValue(new Promise(() => {}))

    render(<AuditHistoryPage />)

    expect(
      screen.getByText(/Loading audit history from the backend/i),
    ).toBeInTheDocument()
  })

  test('renders audit history rows from the API', async () => {
    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    render(<AuditHistoryPage />)

    expect(await screen.findByText('Audit History')).toBeInTheDocument()
    expect((await screen.findAllByText('eye drops')).length).toBeGreaterThan(0)
    expect(screen.getAllByText('metformin').length).toBeGreaterThan(0)
    expect(screen.getByText('Persistence active')).toBeInTheDocument()
    expect(screen.getAllByText('recall-risk-v0.1').length).toBeGreaterThan(0)
  })

  test('renders Regional Health Pulse module filter option', async () => {
    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    render(<AuditHistoryPage />)

    expect(await screen.findByText('Audit History')).toBeInTheDocument()
    expect(
      screen.getByRole('option', { name: 'Regional Health Pulse' }),
    ).toBeInTheDocument()
  })

  test('selects the first audit event by default', async () => {
    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    render(<AuditHistoryPage />)

    expect(await screen.findByText('Selected audit event')).toBeInTheDocument()
    expect(screen.getAllByText('RecallRadar').length).toBeGreaterThan(0)
    expect(screen.getAllByText('eye drops').length).toBeGreaterThan(0)
    expect(screen.getAllByText('openFDA Drug Enforcement API').length).toBeGreaterThan(0)

    fireEvent.click(screen.getByText('Technical view'))

    expect(screen.getByText('11111111-1111-4111-8111-111111111111')).toBeInTheDocument()
    expect(screen.getByText('https://api.fda.gov/drug/enforcement.json')).toBeInTheDocument()
  })

  test('selects audit event from audit_id URL parameter when present', async () => {
    window.history.replaceState(
      null,
      '',
      '/?page=audit&audit_id=22222222-2222-4222-8222-222222222222',
    )

    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    render(<AuditHistoryPage />)

    expect(await screen.findByText('Selected audit event')).toBeInTheDocument()
    expect(screen.getAllByText('DrugSignal').length).toBeGreaterThan(0)
    expect(screen.getAllByText('metformin').length).toBeGreaterThan(0)

    fireEvent.click(screen.getByText('Technical view'))

    expect(screen.getByText('22222222-2222-4222-8222-222222222222')).toBeInTheDocument()

    await waitFor(() => {
      expect(mockedGetAuditEventSourcePull).toHaveBeenCalledWith(
        '22222222-2222-4222-8222-222222222222',
      )
    })

    window.history.replaceState(null, '', '/')
  })

  test('clicking another row updates the selected detail card', async () => {
    const user = userEvent.setup()

    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    render(<AuditHistoryPage />)

    const metforminRowText = await screen.findByText('metformin')
    await user.click(metforminRowText.closest('tr') as HTMLTableRowElement)
    await user.click(screen.getByText('Technical view'))

    expect(screen.getByText('22222222-2222-4222-8222-222222222222')).toBeInTheDocument()
    expect(screen.getByText('https://api.fda.gov/drug/event.json')).toBeInTheDocument()
    expect(screen.getAllByText('DrugSignal').length).toBeGreaterThan(0)
    expect(window.location.search).toContain('page=audit')
    expect(window.location.search).toContain('audit_id=22222222-2222-4222-8222-222222222222')
  })

  test('renders source pull provenance for the selected audit event', async () => {
    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    mockedGetAuditEventSourcePull.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      item: mockSourcePull,
      message: null,
    })

    render(<AuditHistoryPage />)

    expect(await screen.findByText('Source pull recorded')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Technical view'))

    await waitFor(() => {
      expect(mockedGetAuditEventSourcePull).toHaveBeenCalledWith(
        '11111111-1111-4111-8111-111111111111',
      )
      expect(screen.getByText(/a{10}\.\.\.a{10}/)).toBeInTheDocument()
      expect(screen.getAllByText('openFDA Drug Enforcement API').length).toBeGreaterThan(0)
      expect(screen.getByText('Technical provenance details')).toBeInTheDocument()
    })

    expect(screen.getByText(new RegExp(rawPayloadVisibilityMessage, 'i'))).toBeInTheDocument()
    expect(screen.getByText('Source Pull ID')).toBeInTheDocument()
    expect(screen.getByText('Snapshot ID')).toBeInTheDocument()
    expect(screen.getByText('Full payload hash')).toBeInTheDocument()
    expect(screen.getByText('Upstream status')).toBeInTheDocument()
    expect(screen.getByText('Raw payload visibility')).toBeInTheDocument()
    expect(screen.queryByText(/raw_payload/i)).not.toBeInTheDocument()
  })

  test('copies provenance summary from the source pull card', async () => {
    const writeText = vi.fn()

    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText,
      },
      configurable: true,
    })

    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    mockedGetAuditEventSourcePull.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      item: {
        pull_id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        audit_id: '11111111-1111-4111-8111-111111111111',
        source_id: 'openfda_drug_enforcement',
        source_name: 'openFDA Drug Enforcement API',
        endpoint: 'https://api.fda.gov/drug/enforcement.json',
        query: 'eye drops',
        query_params: {
          q: 'eye drops',
          limit: 5,
        },
        retrieval_timestamp: '2026-05-01T10:30:00Z',
        upstream_status: 'success',
        record_count: 1,
        payload_hash: 'a'.repeat(64),
        transform_version: 'recall-transform-v0.1',
        created_at: '2026-05-05T00:08:55.761053Z',
        snapshot_id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      },
      message: null,
    })

    render(<AuditHistoryPage />)

    fireEvent.click(await screen.findByText('Copy provenance summary'))

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining('Dav AI provenance summary'),
    )
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining('Audit ID: 11111111-1111-4111-8111-111111111111'),
    )
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining('Payload hash: ' + 'a'.repeat(64)),
    )
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(rawPayloadVisibilityMessage),
    )
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining(
        'This is public-data traceability only. It is not medical advice, diagnosis, treatment guidance, clinical decision support, or proof of causality.',
      ),
    )
    expect(await screen.findByText('Copied provenance summary')).toBeInTheDocument()
  })

  test('renders source pull provenance not-found message', async () => {
    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    mockedGetAuditEventSourcePull.mockResolvedValue({
      status: 'not_found',
      persistence_available: true,
      item: null,
      message: 'No source pull found for this audit_id.',
    })

    render(<AuditHistoryPage />)

    expect(
      await screen.findByText('No source pull found for this audit_id.'),
    ).toBeInTheDocument()
    expect(screen.getByText('No source pull recorded yet')).toBeInTheDocument()
  })

  test('requests backend-filtered audit history when filters change', async () => {
    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    render(<AuditHistoryPage />)

    expect(await screen.findByText(/Showing\s+2\s+recent audit events/i)).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Module'), {
      target: { value: 'DrugSignal' },
    })

    expect(mockedGetAuditEvents).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByText('Apply filters'))

    await waitFor(() => {
      expect(mockedGetAuditEvents).toHaveBeenLastCalledWith(20, {
        module: 'DrugSignal',
        upstreamStatus: undefined,
        searchText: undefined,
      })
    })

    fireEvent.change(screen.getByLabelText('Status'), {
      target: { value: 'success' },
    })

    fireEvent.click(screen.getByText('Apply filters'))

    await waitFor(() => {
      expect(mockedGetAuditEvents).toHaveBeenLastCalledWith(20, {
        module: 'DrugSignal',
        upstreamStatus: 'success',
        searchText: undefined,
      })
    })

    fireEvent.change(screen.getByLabelText('Search'), {
      target: { value: 'metformin' },
    })

    fireEvent.click(screen.getByText('Apply filters'))

    await waitFor(() => {
      expect(mockedGetAuditEvents).toHaveBeenLastCalledWith(20, {
        module: 'DrugSignal',
        upstreamStatus: 'success',
        searchText: 'metformin',
      })
    })

    fireEvent.click(screen.getByText('Reset filters'))

    await waitFor(() => {
      expect(mockedGetAuditEvents).toHaveBeenLastCalledWith(20, {
        module: undefined,
        upstreamStatus: undefined,
        searchText: undefined,
      })
    })
  })

  test('shows applied filter summary after filters are applied', async () => {
    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    render(<AuditHistoryPage />)

    expect(await screen.findByText('Active filters: None')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Module'), {
      target: { value: 'RecallRadar' },
    })

    fireEvent.change(screen.getByLabelText('Status'), {
      target: { value: 'success' },
    })

    fireEvent.change(screen.getByLabelText('Search'), {
      target: { value: 'eye' },
    })

    fireEvent.click(screen.getByText('Apply filters'))

    expect(
      await screen.findByText('Active filters: Module = RecallRadar · Status = success · Search = eye'),
    ).toBeInTheDocument()
  })

  test('applies filters when pressing Enter in the search field', async () => {
    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    render(<AuditHistoryPage />)

    await screen.findByText(/Showing\s+2\s+recent audit events/i)

    fireEvent.change(screen.getByLabelText('Module'), {
      target: { value: 'RecallRadar' },
    })

    fireEvent.change(screen.getByLabelText('Status'), {
      target: { value: 'success' },
    })

    fireEvent.change(screen.getByLabelText('Search'), {
      target: { value: 'eye' },
    })

    fireEvent.submit(screen.getByLabelText('Audit history filters'))

    await waitFor(() => {
      expect(mockedGetAuditEvents).toHaveBeenLastCalledWith(20, {
        module: 'RecallRadar',
        upstreamStatus: 'success',
        searchText: 'eye',
      })
    })
  })

  test('copies audit ID and trace summary from the detail card', async () => {
    const writeText = vi.fn()

    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText,
      },
      configurable: true,
    })

    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    render(<AuditHistoryPage />)

    await screen.findByText('Selected audit event')

    fireEvent.click(screen.getByText('Copy audit ID'))

    expect(writeText).toHaveBeenCalledWith('11111111-1111-4111-8111-111111111111')
    expect(await screen.findByText('Copied audit ID')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Copy trace summary'))

    expect(writeText).toHaveBeenLastCalledWith(
      [
        'Audit ID: 11111111-1111-4111-8111-111111111111',
        'Module: RecallRadar',
        'Query: eye drops',
        'Source: openFDA Drug Enforcement API',
        'Status: success',
        'Records: 1',
        'Created: 2026-05-05T00:08:55.761053Z',
      ].join('\n'),
    )
    expect(await screen.findByText('Copied trace summary')).toBeInTheDocument()
  })

  test('copies shareable audit link from the detail card', async () => {
    const writeText = vi.fn()

    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText,
      },
      configurable: true,
    })

    window.history.replaceState(null, '', '/?page=audit')

    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    render(<AuditHistoryPage />)

    await screen.findByText('Selected audit event')

    fireEvent.click(screen.getByText('Copy audit link'))

    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining('page=audit'),
    )
    expect(writeText).toHaveBeenCalledWith(
      expect.stringContaining('audit_id=11111111-1111-4111-8111-111111111111'),
    )
    expect(await screen.findByText('Copied audit link')).toBeInTheDocument()

    window.history.replaceState(null, '', '/')
  })

  test('exports displayed audit history rows as CSV', async () => {
    const createObjectURL = vi.fn(() => 'blob:mock-audit-csv')
    const revokeObjectURL = vi.fn()
    const click = vi.fn()

    vi.stubGlobal('URL', {
      createObjectURL,
      revokeObjectURL,
    })

    const originalCreateElement = document.createElement.bind(document)

    vi.spyOn(document, 'createElement').mockImplementation((tagName) => {
      const element = originalCreateElement(tagName)

      if (tagName.toLowerCase() === 'a') {
        element.click = click
      }

      return element
    })

    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: mockAuditItems.length,
      items: mockAuditItems,
    })

    render(<AuditHistoryPage />)

    fireEvent.click(await screen.findByText('Export CSV'))

    expect(createObjectURL).toHaveBeenCalledTimes(1)
    expect(click).toHaveBeenCalledTimes(1)
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock-audit-csv')
  })

  test('renders empty state when no audit events are returned', async () => {
    mockedGetAuditEvents.mockResolvedValue({
      status: 'ok',
      persistence_available: true,
      count: 0,
      items: [],
    })

    render(<AuditHistoryPage />)

    expect(await screen.findByText(/No audit events found yet/i)).toBeInTheDocument()
  })

  test('renders skipped persistence message', async () => {
    mockedGetAuditEvents.mockResolvedValue({
      status: 'skipped',
      persistence_available: false,
      count: 0,
      items: [],
    })

    render(<AuditHistoryPage />)

    expect(
      await screen.findByText(/Audit persistence is not configured/i),
    ).toBeInTheDocument()
    expect(screen.getByText('Persistence unavailable')).toBeInTheDocument()
  })

  test('renders API unavailable message when request fails', async () => {
    mockedGetAuditEvents.mockRejectedValue(new Error('Network error'))

    render(<AuditHistoryPage />)

    await waitFor(() => {
      expect(
        screen.getByText(/Audit History API is unavailable/i),
      ).toBeInTheDocument()
    })
  })
})