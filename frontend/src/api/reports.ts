import { apiClient } from './client'

export async function generateReport(productId: string, name: string, age?: number) {
  const result = await apiClient.post<Blob>('/api/v1/reports/pharmaceutical', {
    product_id: productId, name, ...(age === undefined ? {} : { age }),
  }, { responseType: 'blob' })
  if (!String(result.headers['content-type'] || '').includes('application/pdf')) {
    throw new Error('The report service returned an unexpected response.')
  }
  return result.data
}
