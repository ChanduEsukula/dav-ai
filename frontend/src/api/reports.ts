import { apiClient } from './client'

export type SafetyReportModule =
  | 'recallradar'
  | 'drugsignal'
  | 'foodradar'
  | 'cosmeticsignal'
  | 'both'

export type SafetyReportRequest = {
  prepared_for: string
  organization: string
  role: string
  query: string
  module: SafetyReportModule
  purpose: string
}

function getFilenameFromContentDisposition(contentDisposition: string | undefined): string {
  if (!contentDisposition) return 'dav-ai-safety-report.pdf'

  const match = contentDisposition.match(/filename="([^"]+)"/)
  return match?.[1] ?? 'dav-ai-safety-report.pdf'
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob)

  try {
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
  } finally {
    window.URL.revokeObjectURL(url)
  }
}

export async function downloadSafetyIntelligenceReport(
  payload: SafetyReportRequest
): Promise<string> {
  const response = await apiClient.post<Blob>('/api/v1/reports/safety-intelligence', payload, {
    responseType: 'blob',
  })

  const filename = getFilenameFromContentDisposition(response.headers['content-disposition'])

  downloadBlob(response.data, filename)

  return filename
}
