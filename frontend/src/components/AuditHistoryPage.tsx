import { useEffect, useState } from 'react'
import {
  getAuditEventSourcePull,
  getAuditEvents,
  type AuditHistoryItem,
  type SourcePullProvenanceItem,
} from '../api/auditEvents'
import { PAGE_IDS } from '../types/navigation'

const moduleFilterOptions = [
  'RecallRadar',
  'DrugSignal',
  'FoodRadar',
  'CosmeticSignal',
  'RealWorldSafety',
  'RegionalHealthPulse',
] as const

type AuditModuleFilter = (typeof moduleFilterOptions)[number]
type ModuleFilter = 'all' | AuditModuleFilter
type StatusFilter = 'all' | 'success' | 'empty' | 'error'
type AuditDetailViewMode = 'basic' | 'technical'

function formatTimestamp(value: string) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(value))
  } catch {
    return value
  }
}

function shortenIdentifier(
  value: string | null | undefined,
  prefixLength = 8,
  suffixLength = 8,
) {
  if (!value) {
    return 'N/A'
  }

  if (value.length <= prefixLength + suffixLength + 3) {
    return value
  }

  return `${value.slice(0, prefixLength)}...${value.slice(-suffixLength)}`
}

function formatQueryParams(params: Record<string, unknown> | null) {
  return JSON.stringify(params ?? {}, null, 2)
}

function escapeCsvValue(value: string | number | null | undefined) {
  const normalizedValue = value === null || value === undefined ? '' : String(value)

  if (/[",\n]/.test(normalizedValue)) {
    return `"${normalizedValue.replaceAll('"', '""')}"`
  }

  return normalizedValue
}

function buildAuditCsv(items: AuditHistoryItem[]) {
  const headers = [
    'created_at',
    'module',
    'query',
    'upstream_status',
    'record_count',
    'source_name',
    'audit_id',
    'source_id',
    'transform_version',
    'score_version',
  ]

  const rows = items.map((item) => [
    item.created_at,
    item.module,
    item.query,
    item.upstream_status,
    item.record_count,
    item.source_name,
    item.audit_id,
    item.source_id,
    item.transform_version,
    item.score_version ?? '',
  ])

  return [
    headers.join(','),
    ...rows.map((row) => row.map(escapeCsvValue).join(',')),
  ].join('\n')
}

function buildAuditTraceSummary(item: AuditHistoryItem) {
  return [
    `Audit ID: ${item.audit_id}`,
    `Module: ${item.module}`,
    `Query: ${item.query}`,
    `Source: ${item.source_name}`,
    `Status: ${item.upstream_status}`,
    `Records: ${item.record_count}`,
    `Created: ${item.created_at}`,
  ].join('\n')
}

function buildProvenanceSummary(
  item: AuditHistoryItem,
  sourcePull: SourcePullProvenanceItem,
) {
  return [
    'Dav AI provenance summary',
    '',
    `Audit ID: ${item.audit_id}`,
    `Module: ${item.module}`,
    `Query: ${item.query}`,
    `Source: ${sourcePull.source_name ?? item.source_name}`,
    `Endpoint: ${sourcePull.endpoint ?? item.endpoint}`,
    `Records: ${sourcePull.record_count ?? item.record_count}`,
    `Retrieved: ${sourcePull.retrieval_timestamp ?? item.retrieval_timestamp}`,
    `Payload hash: ${sourcePull.payload_hash}`,
    '',
    'Raw public-source payloads are stored for reproducibility and audit provenance, but are intentionally not displayed in the UI.',
    'This is public-data traceability only. It is not medical advice, diagnosis, treatment guidance, clinical decision support, or proof of causality.',
  ].join('\n')
}

function buildAppliedFilterSummary(
  moduleFilter: ModuleFilter,
  statusFilter: StatusFilter,
  searchText: string,
) {
  const filters = []

  if (moduleFilter !== 'all') {
    filters.push(`Module = ${moduleFilter}`)
  }

  if (statusFilter !== 'all') {
    filters.push(`Status = ${statusFilter}`)
  }

  if (searchText.trim()) {
    filters.push(`Search = ${searchText.trim()}`)
  }

  return filters.length > 0 ? filters.join(' · ') : 'None'
}

function getAuditIdFromUrl() {
  return new URLSearchParams(window.location.search).get('audit_id')
}

function setAuditIdInUrl(auditId: string | null) {
  const url = new URL(window.location.href)

  url.searchParams.set('page', PAGE_IDS.AUDIT)

  if (auditId) {
    url.searchParams.set('audit_id', auditId)
  } else {
    url.searchParams.delete('audit_id')
  }

  window.history.replaceState(null, '', url.toString())
}

function getSourcePullTitle(
  status: string,
  sourcePull: SourcePullProvenanceItem | null,
) {
  if (sourcePull) {
    return 'Source pull recorded'
  }

  if (status === 'loading') {
    return 'Checking source pull'
  }

  if (status === 'not_found') {
    return 'No source pull recorded yet'
  }

  if (status === 'error') {
    return 'Source pull unavailable'
  }

  return 'Source pull status'
}

export default function AuditHistoryPage() {
  const [items, setItems] = useState<AuditHistoryItem[]>([])
  const [selectedItem, setSelectedItem] = useState<AuditHistoryItem | null>(null)
  const [status, setStatus] = useState<string>('idle')
  const [persistenceAvailable, setPersistenceAvailable] = useState<boolean>(false)
  const [errorMessage, setErrorMessage] = useState<string>('')
  const [draftModuleFilter, setDraftModuleFilter] = useState<ModuleFilter>('all')
  const [draftStatusFilter, setDraftStatusFilter] = useState<StatusFilter>('all')
  const [draftSearchText, setDraftSearchText] = useState('')
  const [appliedModuleFilter, setAppliedModuleFilter] = useState<ModuleFilter>('all')
  const [appliedStatusFilter, setAppliedStatusFilter] = useState<StatusFilter>('all')
  const [appliedSearchText, setAppliedSearchText] = useState('')
  const [copyMessage, setCopyMessage] = useState('')
  const [detailViewMode, setDetailViewMode] = useState<AuditDetailViewMode>('basic')
  const [sourcePull, setSourcePull] = useState<SourcePullProvenanceItem | null>(null)
  const [sourcePullStatus, setSourcePullStatus] = useState<string>('idle')
  const [sourcePullMessage, setSourcePullMessage] = useState('')

  const appliedFilterSummary = buildAppliedFilterSummary(
    appliedModuleFilter,
    appliedStatusFilter,
    appliedSearchText,
  )

  useEffect(() => {
    let isMounted = true

    async function loadAuditHistory() {
      setStatus('loading')
      setErrorMessage('')

      try {
        const response = await getAuditEvents(20, {
          module: appliedModuleFilter === 'all' ? undefined : appliedModuleFilter,
          upstreamStatus: appliedStatusFilter === 'all' ? undefined : appliedStatusFilter,
          searchText: appliedSearchText.trim() || undefined,
        })

        if (!isMounted) return

        setPersistenceAvailable(response.persistence_available)
        setStatus(response.status)

        if (response.status === 'ok') {
          setItems(response.items)

          const auditIdFromUrl = getAuditIdFromUrl()
          const urlSelectedItem = auditIdFromUrl
            ? response.items.find((item) => item.audit_id === auditIdFromUrl)
            : null

          setSelectedItem(urlSelectedItem ?? response.items[0] ?? null)
          return
        }

        setItems([])
        setSelectedItem(null)

        if (response.status === 'skipped') {
          setErrorMessage('Audit persistence is not configured for this environment.')
        } else if (response.status === 'error') {
          setErrorMessage('Audit history could not be loaded from the database.')
        }
      } catch {
        if (!isMounted) return

        setStatus('error')
        setItems([])
        setSelectedItem(null)
        setErrorMessage('Audit History API is unavailable. Check that the backend is running.')
      }
    }

    loadAuditHistory()

    return () => {
      isMounted = false
    }
  }, [appliedModuleFilter, appliedSearchText, appliedStatusFilter])

  useEffect(() => {
    let isMounted = true

    async function loadSourcePullProvenance() {
      if (!selectedItem) {
        setSourcePull(null)
        setSourcePullStatus('idle')
        setSourcePullMessage('')
        return
      }

      setSourcePullStatus('loading')
      setSourcePullMessage('')

      try {
        const response = await getAuditEventSourcePull(selectedItem.audit_id)

        if (!isMounted) return

        setSourcePullStatus(response.status)
        setSourcePull(response.item)
        setSourcePullMessage(response.message ?? '')
      } catch {
        if (!isMounted) return

        setSourcePullStatus('error')
        setSourcePull(null)
        setSourcePullMessage('Source-pull provenance API is unavailable.')
      }
    }

    void loadSourcePullProvenance()

    return () => {
      isMounted = false
    }
  }, [selectedItem])

  function applyFilters() {
    setAppliedModuleFilter(draftModuleFilter)
    setAppliedStatusFilter(draftStatusFilter)
    setAppliedSearchText(draftSearchText)
  }

  function resetFilters() {
    setDraftModuleFilter('all')
    setDraftStatusFilter('all')
    setDraftSearchText('')
    setAppliedModuleFilter('all')
    setAppliedStatusFilter('all')
    setAppliedSearchText('')
    setAuditIdInUrl(null)
  }

  function selectAuditItem(item: AuditHistoryItem) {
    setSelectedItem(item)
    setAuditIdInUrl(item.audit_id)
  }

  function exportAuditCsv() {
    if (items.length === 0) return

    const csv = buildAuditCsv(items)
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')

    link.href = url
    link.download = `dav-ai-audit-history-${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  function showCopyMessage(message: string) {
    setCopyMessage(message)

    window.setTimeout(() => {
      setCopyMessage('')
    }, 2000)
  }

  async function copyAuditId(item: AuditHistoryItem) {
    await navigator.clipboard.writeText(item.audit_id)
    showCopyMessage('Copied audit ID')
  }

  async function copyTraceSummary(item: AuditHistoryItem) {
    await navigator.clipboard.writeText(buildAuditTraceSummary(item))
    showCopyMessage('Copied trace summary')
  }

  async function copyAuditLink(item: AuditHistoryItem) {
    const url = new URL(window.location.href)
    url.searchParams.set('page', PAGE_IDS.AUDIT)
    url.searchParams.set('audit_id', item.audit_id)

    await navigator.clipboard.writeText(url.toString())
    showCopyMessage('Copied audit link')
  }

  async function copyProvenanceSummary(
    item: AuditHistoryItem,
    sourcePull: SourcePullProvenanceItem,
  ) {
    await navigator.clipboard.writeText(buildProvenanceSummary(item, sourcePull))
    showCopyMessage('Copied provenance summary')
  }

  async function copyPayloadHash(sourcePull: SourcePullProvenanceItem) {
    await navigator.clipboard.writeText(sourcePull.payload_hash)
    showCopyMessage('Copied payload hash')
  }

  async function copySourcePullId(sourcePull: SourcePullProvenanceItem) {
    await navigator.clipboard.writeText(sourcePull.pull_id)
    showCopyMessage('Copied source pull ID')
  }

  async function copySnapshotId(sourcePull: SourcePullProvenanceItem) {
    if (!sourcePull.snapshot_id) {
      return
    }

    await navigator.clipboard.writeText(sourcePull.snapshot_id)
    showCopyMessage('Copied snapshot ID')
  }

  return (
    <main
      className="info-page audit-history-page"
      style={{ paddingTop: '8rem', minHeight: '100vh' }}
    >
      <section className="info-hero">
        <p className="eyebrow">Source transparency</p>
        <h1>Audit History</h1>
        <p>
          Review recent public-data searches, source metadata, retrieval timestamps,
          record counts, transform versions, scoring versions, and disclaimer versions.
        </p>
      </section>

      <section className="info-card">
        <div className="audit-history-header">
          <div>
            <h2>Recent audit events</h2>
            <p>
              This is public-data traceability only. It is not clinical record storage
              and should not contain PHI.
            </p>
          </div>

          <div className="audit-status-pill">
            {persistenceAvailable ? 'Persistence active' : 'Persistence unavailable'}
          </div>
        </div>

        {status === 'loading' && (
          <p className="muted-text">Loading audit history from the backend...</p>
        )}

        {errorMessage && (
          <div className="audit-error-box">
            {errorMessage}
          </div>
        )}

        {status === 'ok' && items.length > 0 && (
          <form
            className="audit-filter-panel"
            aria-label="Audit history filters"
            onSubmit={(event) => {
              event.preventDefault()
              applyFilters()
            }}
          >
            <label>
              Module
              <select
                value={draftModuleFilter}
                onChange={(event) => setDraftModuleFilter(event.target.value as ModuleFilter)}
              >
                <option value="all">All modules</option>
                {moduleFilterOptions.map((moduleName) => (
                  <option key={moduleName} value={moduleName}>
                    {moduleName}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Status
              <select
                value={draftStatusFilter}
                onChange={(event) => setDraftStatusFilter(event.target.value as StatusFilter)}
              >
                <option value="all">All statuses</option>
                <option value="success">success</option>
                <option value="empty">empty</option>
                <option value="error">error</option>
              </select>
            </label>

            <label className="audit-search-field">
              Search
              <input
                type="search"
                value={draftSearchText}
                onChange={(event) => setDraftSearchText(event.target.value)}
                placeholder="Search query, audit ID, source, or version"
              />
            </label>

            <button type="submit">
              Apply filters
            </button>

            <button type="button" onClick={resetFilters}>
              Reset filters
            </button>

            <button type="button" onClick={exportAuditCsv}>
              Export CSV
            </button>

            <p>
              {appliedModuleFilter === 'all' && appliedStatusFilter === 'all' && !appliedSearchText.trim()
                ? `Showing ${items.length} recent audit events`
                : `Showing ${items.length} matching audit events`}
            </p>

            <p className="audit-applied-filter-summary">
              Active filters: {appliedFilterSummary}
            </p>
          </form>
        )}

        {status === 'ok' && items.length === 0 && (
          <p className="muted-text">
            {appliedModuleFilter === 'all' && appliedStatusFilter === 'all' && !appliedSearchText.trim()
              ? 'No audit events found yet.'
              : 'No audit events match the current filters.'}
          </p>
        )}

        {items.length > 0 && (
          <div className="audit-history-layout">
            <div className="audit-table-wrap">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Module</th>
                    <th>Query</th>
                    <th>Source</th>
                    <th>Status</th>
                    <th>Records</th>
                    <th>Score version</th>
                  </tr>
                </thead>

                <tbody>
                  {items.map((item) => (
                    <tr
                      key={item.audit_id}
                      className={selectedItem?.audit_id === item.audit_id ? 'selected' : ''}
                      onClick={() => selectAuditItem(item)}
                    >
                      <td>{formatTimestamp(item.created_at)}</td>
                      <td>{item.module}</td>
                      <td>{item.query}</td>
                      <td>{item.source_name}</td>
                      <td>
                        <span className={`audit-status audit-status-${item.upstream_status}`}>
                          {item.upstream_status}
                        </span>
                      </td>
                      <td>{item.record_count}</td>
                      <td>{item.score_version ?? 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {selectedItem && (
              <aside className="audit-detail-card">
                <p className="eyebrow">Selected audit event</p>
                <h3>{selectedItem.module}</h3>

                <div className="audit-detail-view-toggle" aria-label="Audit detail view mode">
                  <button
                    type="button"
                    className={detailViewMode === 'basic' ? 'active' : ''}
                    aria-pressed={detailViewMode === 'basic'}
                    onClick={() => setDetailViewMode('basic')}
                  >
                    Basic view
                  </button>
                  <button
                    type="button"
                    className={detailViewMode === 'technical' ? 'active' : ''}
                    aria-pressed={detailViewMode === 'technical'}
                    onClick={() => setDetailViewMode('technical')}
                  >
                    Technical view
                  </button>
                </div>

                <div className="audit-detail-actions">
                  <button type="button" onClick={() => copyAuditId(selectedItem)}>
                    Copy audit ID
                  </button>
                  <button type="button" onClick={() => copyTraceSummary(selectedItem)}>
                    Copy trace summary
                  </button>
                  <button type="button" onClick={() => copyAuditLink(selectedItem)}>
                    Copy audit link
                  </button>
                </div>

                {copyMessage && (
                  <p className="audit-copy-message" role="status">
                    {copyMessage}
                  </p>
                )}

                <dl>
                  {detailViewMode === 'technical' && (
                    <div>
                      <dt>Audit ID</dt>
                      <dd>{selectedItem.audit_id}</dd>
                    </div>
                  )}

                  <div>
                    <dt>Query</dt>
                    <dd>{selectedItem.query}</dd>
                  </div>

                  <div>
                    <dt>Source</dt>
                    <dd>{selectedItem.source_name}</dd>
                  </div>

                  {detailViewMode === 'technical' && (
                    <div>
                      <dt>Endpoint</dt>
                      <dd>{selectedItem.endpoint}</dd>
                    </div>
                  )}

                  <div>
                    <dt>Retrieval timestamp</dt>
                    <dd>{formatTimestamp(selectedItem.retrieval_timestamp)}</dd>
                  </div>

                  <div>
                    <dt>Created at</dt>
                    <dd>{formatTimestamp(selectedItem.created_at)}</dd>
                  </div>

                  {detailViewMode === 'technical' && (
                    <div>
                      <dt>Transform version</dt>
                      <dd>{selectedItem.transform_version}</dd>
                    </div>
                  )}

                  {detailViewMode === 'technical' && (
                    <div>
                      <dt>Score version</dt>
                      <dd>{selectedItem.score_version ?? 'N/A'}</dd>
                    </div>
                  )}

                  {detailViewMode === 'technical' && (
                    <div>
                      <dt>Disclaimer version</dt>
                      <dd>{selectedItem.disclaimer_version ?? 'N/A'}</dd>
                    </div>
                  )}

                  <div>
                    <dt>Record count</dt>
                    <dd>{selectedItem.record_count}</dd>
                  </div>

                  {selectedItem.error_message && (
                    <div>
                      <dt>Error message</dt>
                      <dd>{selectedItem.error_message}</dd>
                    </div>
                  )}
                </dl>

                {detailViewMode === 'technical' && (
                  <div className="audit-query-params">
                    <h4>Query parameters</h4>
                    <pre>{formatQueryParams(selectedItem.query_params)}</pre>
                  </div>
                )}

                <div className="audit-source-pull-card">
                  <div className="audit-source-pull-header">
                    <div>
                      <p className="eyebrow">Provenance</p>
                      <h4>{getSourcePullTitle(sourcePullStatus, sourcePull)}</h4>
                    </div>
                    <span className={`audit-status audit-status-${sourcePullStatus}`}>
                      {sourcePullStatus}
                    </span>
                  </div>

                  {sourcePullMessage && (
                    <p className="audit-source-pull-note">{sourcePullMessage}</p>
                  )}

                  {sourcePull && (
                    <>
                      <p className="audit-source-pull-summary">
                        Dav AI stored a reproducible public-source pull for this
                        audit event. Raw public-source payloads are stored for
                        reproducibility and audit provenance, but are intentionally
                        not displayed in the UI.
                      </p>

                      <div className="audit-detail-actions">
                        <button
                          type="button"
                          className="audit-provenance-copy-button"
                          onClick={() => copyProvenanceSummary(selectedItem, sourcePull)}
                        >
                          Copy provenance summary
                        </button>

                        <button
                          type="button"
                          className="audit-provenance-copy-button"
                          onClick={() => copyPayloadHash(sourcePull)}
                        >
                          Copy payload hash
                        </button>

                        <button
                          type="button"
                          className="audit-provenance-copy-button"
                          onClick={() => copySourcePullId(sourcePull)}
                        >
                          Copy source pull ID
                        </button>

                        {sourcePull.snapshot_id && (
                          <button
                            type="button"
                            className="audit-provenance-copy-button"
                            onClick={() => copySnapshotId(sourcePull)}
                          >
                            Copy snapshot ID
                          </button>
                        )}
                      </div>

                      <div className="audit-source-pull-summary-grid">
                        <div>
                          <span>Source</span>
                          <strong>{sourcePull.source_name ?? 'N/A'}</strong>
                        </div>

                        <div>
                          <span>Records</span>
                          <strong>{sourcePull.record_count ?? 'N/A'}</strong>
                        </div>

                        <div>
                          <span>Retrieved</span>
                          <strong>
                            {sourcePull.retrieval_timestamp
                              ? formatTimestamp(sourcePull.retrieval_timestamp)
                              : 'N/A'}
                          </strong>
                        </div>

                        <div>
                          <span>Payload hash</span>
                          <strong title={sourcePull.payload_hash}>
                            {shortenIdentifier(sourcePull.payload_hash, 10, 10)}
                          </strong>
                        </div>
                      </div>

                      {detailViewMode === 'technical' && (
                        <details className="audit-source-pull-details" open>
                          <summary>Technical provenance details</summary>

                          <dl className="audit-source-pull-grid">
                            <div>
                              <dt>Source Pull ID</dt>
                              <dd title={sourcePull.pull_id}>
                                {shortenIdentifier(sourcePull.pull_id)}
                              </dd>
                            </div>

                            <div>
                              <dt>Snapshot ID</dt>
                              <dd title={sourcePull.snapshot_id ?? undefined}>
                                {shortenIdentifier(sourcePull.snapshot_id)}
                              </dd>
                            </div>

                            <div>
                              <dt>Full payload hash</dt>
                              <dd title={sourcePull.payload_hash}>
                                {sourcePull.payload_hash}
                              </dd>
                            </div>

                            <div>
                              <dt>Retrieval timestamp</dt>
                              <dd>
                                {sourcePull.retrieval_timestamp
                                  ? formatTimestamp(sourcePull.retrieval_timestamp)
                                  : 'N/A'}
                              </dd>
                            </div>

                            <div>
                              <dt>Upstream status</dt>
                              <dd>{sourcePull.upstream_status ?? 'N/A'}</dd>
                            </div>

                            <div>
                              <dt>Record count</dt>
                              <dd>{sourcePull.record_count ?? 'N/A'}</dd>
                            </div>

                            <div>
                              <dt>Endpoint</dt>
                              <dd>{sourcePull.endpoint ?? 'N/A'}</dd>
                            </div>

                            <div>
                              <dt>Transform version</dt>
                              <dd>{sourcePull.transform_version ?? 'N/A'}</dd>
                            </div>

                            <div>
                              <dt>Raw payload visibility</dt>
                              <dd>
                                Stored for reproducibility and audit provenance,
                                but intentionally not displayed in the UI.
                              </dd>
                            </div>
                          </dl>

                          <div className="audit-query-params">
                            <h4>Source pull query parameters</h4>
                            <pre>{formatQueryParams(sourcePull.query_params)}</pre>
                          </div>
                        </details>
                      )}
                    </>
                  )}
                </div>
              </aside>
            )}
          </div>
        )}
      </section>
    </main>
  )
}
