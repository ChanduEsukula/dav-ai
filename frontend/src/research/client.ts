import type { Created, Candidates, Confirmed, Outcome } from './contracts'

// Deliberately fixed loopback endpoint; a hosted API URL cannot enable agents.
const root = 'http://127.0.0.1:8001/api/local/research/sessions'
export class ResearchError extends Error {
  constructor(publicCode: string) { super(publicCode) }
}
export type Session = Created
async function request<T>(url: string, capability: string, body?: object): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 25_000)
  try {
    const response = await fetch(url, {
      method: body === undefined ? 'GET' : 'POST', credentials: 'omit', redirect: 'error',
      cache: 'no-store', referrerPolicy: 'no-referrer', signal: controller.signal,
      headers: { Authorization: `Bearer ${capability}`, 'Content-Type': 'application/json' },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new ResearchError(error.detail?.code ?? 'api_unavailable')
    }
    return await response.json() as T
  } catch (error) {
    if (error instanceof ResearchError) throw error
    throw new ResearchError(error instanceof DOMException && error.name === 'AbortError' ? 'timeout' : 'api_unavailable')
  } finally { clearTimeout(timer) }
}
const path = (s: Session, action: string) => `${root}/${encodeURIComponent(s.session_id)}/${action}`
export const researchApi = {
  create: (pairing: string) => request<Created>(root, pairing, {}),
  search: (s: Session, query: string) => request<Candidates>(path(s, 'resolve'), s.capability, { query }),
  confirm: (s: Session, product_ref: string) => request<Confirmed>(path(s, 'confirm'), s.capability, { product_ref }),
  run: (s: Session, question: string, categories: string[], model: string | null) => request<Outcome>(path(s, 'research'), s.capability, { question, categories, model }),
  result: (s: Session) => request<Outcome>(path(s, 'result'), s.capability),
  cancel: (s: Session) => request<Outcome>(path(s, 'cancel'), s.capability, {}),
  close: (s: Session) => request<Outcome>(path(s, 'close'), s.capability, {}),
}
