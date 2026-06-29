import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
export const AUTH_TOKEN_STORAGE_KEY = 'dav_ai_auth_token'

let fallbackAuthToken: string | null = null

function generateRequestId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }

  return `frontend-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
})

export function getStoredAuthToken(): string | null {
  if (typeof window === 'undefined') {
    return fallbackAuthToken
  }

  if (typeof window.localStorage?.getItem !== 'function') {
    return fallbackAuthToken
  }

  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY) ?? fallbackAuthToken
}

export function setStoredAuthToken(token: string): void {
  fallbackAuthToken = token

  if (typeof window.localStorage?.setItem === 'function') {
    window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token)
  }
}

export function clearStoredAuthToken(): void {
  fallbackAuthToken = null

  if (typeof window.localStorage?.removeItem === 'function') {
    window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY)
  }
}

apiClient.interceptors.request.use((config) => {
  config.headers = config.headers ?? {}
  config.headers['X-Request-ID'] = generateRequestId()

  const token = getStoredAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})
