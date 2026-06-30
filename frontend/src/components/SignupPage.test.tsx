import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import { signup } from '../api/auth'
import { clearStoredAuthToken, getStoredAuthToken } from '../api/client'
import { getProfile } from '../api/profile'
import { AuthProvider } from '../auth/AuthContext'
import SignupPage from './SignupPage'

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

const mockSignup = vi.mocked(signup)
const mockGetProfile = vi.mocked(getProfile)

function renderSignup(onSignedUp = vi.fn()) {
  const goToLogin = vi.fn()

  render(
    <AuthProvider>
      <SignupPage onSignedUp={onSignedUp} goToLogin={goToLogin} />
    </AuthProvider>,
  )

  return { goToLogin }
}

beforeEach(() => {
  clearStoredAuthToken()
  vi.clearAllMocks()
  mockGetProfile.mockResolvedValue({
    user_id: 'user-1',
    role: null,
    state: null,
    zip_code: null,
    alert_interests: [],
    alert_frequency: null,
    report_style: 'simple',
    created_at: '2026-06-29T12:00:00Z',
    updated_at: '2026-06-29T12:00:00Z',
  })
})

test('validates signup form fields before submitting', async () => {
  const user = userEvent.setup()
  renderSignup()

  await user.click(screen.getByRole('button', { name: /Create account/i }))

  expect(screen.getByRole('alert')).toHaveTextContent('Full name is required.')
  expect(mockSignup).not.toHaveBeenCalled()
})

test('creates an account and continues to onboarding', async () => {
  const user = userEvent.setup()
  const onSignedUp = vi.fn()
  mockSignup.mockResolvedValue({
    access_token: 'signup-token',
    token_type: 'bearer',
    user: {
      id: 'user-1',
      full_name: 'Chandu Esukula',
      email: 'chandu.demo@example.com',
      created_at: '2026-06-29T12:00:00Z',
      updated_at: '2026-06-29T12:00:00Z',
    },
  })

  renderSignup(onSignedUp)

  await user.type(screen.getByLabelText(/Full name/i), 'Chandu Esukula')
  await user.type(screen.getByLabelText(/Email/i), 'chandu.demo@example.com')
  await user.type(screen.getByLabelText(/^Password$/i), 'safe-demo-password')
  await user.type(screen.getByLabelText(/Confirm password/i), 'safe-demo-password')
  await user.click(screen.getByRole('checkbox'))
  await user.click(screen.getByRole('button', { name: /Create account/i }))

  await waitFor(() => {
    expect(onSignedUp).toHaveBeenCalled()
  })
  expect(mockSignup).toHaveBeenCalledWith({
    full_name: 'Chandu Esukula',
    email: 'chandu.demo@example.com',
    password: 'safe-demo-password',
  })
  expect(getStoredAuthToken()).toBe('signup-token')
})
