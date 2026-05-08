import { useEffect, useState } from 'react'
import {
  getAuditEvents,
  type AuditHistoryItem,
} from '../api/auditEvents'

type ModuleFilter = 'all' | 'RecallRadar' | 'DrugSignal'
type StatusFilter = 'all' | 'success' | 'empty' | 'error'

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

function formatQueryParams(params: Record<string, unknown>) {
  return JSON.stringify(params, null, 2)
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
          setSelectedItem(response.items[0] ?? null)
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
  }

  function exportAuditCsv() {
    if (items.length === 0) return

    const csv = buildAuditCsv(items)
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')

    link.href = url
    link.download = `medtrek-audit-history-${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
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
                <option value="RecallRadar">RecallRadar</option>
                <option value="DrugSignal">DrugSignal</option>
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
                      onClick={() => setSelectedItem(item)}
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

                <dl>
                  <div>
                    <dt>Audit ID</dt>
                    <dd>{selectedItem.audit_id}</dd>
                  </div>

                  <div>
                    <dt>Query</dt>
                    <dd>{selectedItem.query}</dd>
                  </div>

                  <div>
                    <dt>Source</dt>
                    <dd>{selectedItem.source_name}</dd>
                  </div>

                  <div>
                    <dt>Endpoint</dt>
                    <dd>{selectedItem.endpoint}</dd>
                  </div>

                  <div>
                    <dt>Retrieval timestamp</dt>
                    <dd>{formatTimestamp(selectedItem.retrieval_timestamp)}</dd>
                  </div>

                  <div>
                    <dt>Created at</dt>
                    <dd>{formatTimestamp(selectedItem.created_at)}</dd>
                  </div>

                  <div>
                    <dt>Transform version</dt>
                    <dd>{selectedItem.transform_version}</dd>
                  </div>

                  <div>
                    <dt>Score version</dt>
                    <dd>{selectedItem.score_version ?? 'N/A'}</dd>
                  </div>

                  <div>
                    <dt>Disclaimer version</dt>
                    <dd>{selectedItem.disclaimer_version ?? 'N/A'}</dd>
                  </div>

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

                <div className="audit-query-params">
                  <h4>Query parameters</h4>
                  <pre>{formatQueryParams(selectedItem.query_params)}</pre>
                </div>
              </aside>
            )}
          </div>
        )}
      </section>
    </main>
  )
}
