import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import { login } from '../api/auth'
import {
  apiClient,
  clearStoredAuthToken,
  getStoredAuthToken,
  setStoredAuthToken,
} from '../api/client'
import { getProfile } from '../api/profile'
import { AuthProvider, useAuth } from './AuthContext'

vi.mock('../api/auth', () => ({
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  signup: vi.fn(),
}))

vi.mock('../api/profile', async () => {
  const actual = await vi.importActual<typeof import('../api/profile')>(
    '../api/profile',
  )

  return {
    ...actual,
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
  }
})

const mockLogin = vi.mocked(login)
const mockGetProfile = vi.mocked(getProfile)

function LoginProbe() {
  const auth = useAuth()

  return (
    <div>
      <p data-testid="token">{auth.token ?? 'no-token'}</p>
      <button
        type="button"
        onClick={() =>
          void auth.login({
            email: 'chandu.demo@example.com',
            password: 'safe-demo-password',
          })
        }
      >
        Login probe
      </button>
    </div>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  clearStoredAuthToken()
})

test('stores token after login', async () => {
  const user = userEvent.setup()
  mockLogin.mockResolvedValue({
    access_token: 'context-token',
    token_type: 'bearer',
    user: {
      id: 'user-1',
      full_name: 'Chandu Esukula',
      email: 'chandu.demo@example.com',
      created_at: '2026-06-29T12:00:00Z',
      updated_at: '2026-06-29T12:00:00Z',
    },
  })
  mockGetProfile.mockResolvedValue({
    user_id: 'user-1',
    role: 'consumer',
    state: 'MN',
    zip_code: '55114',
    alert_interests: ['Food recalls'],
    alert_frequency: 'weekly',
    report_style: 'simple',
    created_at: '2026-06-29T12:00:00Z',
    updated_at: '2026-06-29T12:00:00Z',
  })

  render(
    <AuthProvider>
      <LoginProbe />
    </AuthProvider>,
  )

  await user.click(screen.getByRole('button', { name: /Login probe/i }))

  await waitFor(() => {
    expect(screen.getByTestId('token')).toHaveTextContent('context-token')
  })
  expect(getStoredAuthToken()).toBe('context-token')
})

test('api client attaches bearer token from localStorage', async () => {
  const originalAdapter = apiClient.defaults.adapter
  let observedAuthorization: string | undefined

  apiClient.defaults.adapter = async (config) => {
    observedAuthorization = String(config.headers?.Authorization ?? '')

    return {
      data: { ok: true },
      status: 200,
      statusText: 'OK',
      headers: {},
      config,
    }
  }

  setStoredAuthToken('stored-token')

  try {
    await apiClient.get('/api/v1/auth/me')
  } finally {
    apiClient.defaults.adapter = originalAdapter
  }

  expect(observedAuthorization).toBe('Bearer stored-token')
})
