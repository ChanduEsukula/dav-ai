import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import { login } from '../api/auth'
import { clearStoredAuthToken, getStoredAuthToken } from '../api/client'
import { getProfile } from '../api/profile'
import { AuthProvider } from '../auth/AuthContext'
import LoginPage from './LoginPage'

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

function renderLogin(onSignedIn = vi.fn()) {
  const goToSignup = vi.fn()

  render(
    <AuthProvider>
      <LoginPage onSignedIn={onSignedIn} goToSignup={goToSignup} />
    </AuthProvider>,
  )

  return { goToSignup }
}

beforeEach(() => {
  clearStoredAuthToken()
  vi.clearAllMocks()
})

test('signs in and routes to profile when profile is complete', async () => {
  const user = userEvent.setup()
  const onSignedIn = vi.fn()
  mockLogin.mockResolvedValue({
    access_token: 'login-token',
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

  renderLogin(onSignedIn)

  await user.type(screen.getByLabelText(/Email/i), 'chandu.demo@example.com')
  await user.type(screen.getByLabelText(/Password/i), 'safe-demo-password')
  await user.click(screen.getByRole('button', { name: /Sign in/i }))

  await waitFor(() => {
    expect(onSignedIn).toHaveBeenCalledWith('profile')
  })
  expect(getStoredAuthToken()).toBe('login-token')
})

test('shows invalid login error', async () => {
  const user = userEvent.setup()
  mockLogin.mockRejectedValue({
    isAxiosError: true,
    response: {
      status: 401,
    },
  })

  renderLogin()

  await user.type(screen.getByLabelText(/Email/i), 'chandu.demo@example.com')
  await user.type(screen.getByLabelText(/Password/i), 'wrong-password')
  await user.click(screen.getByRole('button', { name: /Sign in/i }))

  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Invalid email or password.',
  )
})
