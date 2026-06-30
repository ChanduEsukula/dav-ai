import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import { getCurrentUser } from '../api/auth'
import { clearStoredAuthToken, setStoredAuthToken } from '../api/client'
import { getProfile, updateProfile } from '../api/profile'
import { AuthProvider } from '../auth/AuthContext'
import ProfilePage from './ProfilePage'

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

const mockGetCurrentUser = vi.mocked(getCurrentUser)
const mockGetProfile = vi.mocked(getProfile)
const mockUpdateProfile = vi.mocked(updateProfile)

beforeEach(() => {
  clearStoredAuthToken()
  vi.clearAllMocks()
  setStoredAuthToken('profile-token')
  mockGetCurrentUser.mockResolvedValue({
    id: 'user-1',
    full_name: 'Chandu Esukula',
    email: 'chandu.demo@example.com',
    created_at: '2026-06-29T12:00:00Z',
    updated_at: '2026-06-29T12:00:00Z',
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
  mockUpdateProfile.mockResolvedValue({
    user_id: 'user-1',
    role: 'public_health_analyst',
    state: 'CA',
    zip_code: '94105',
    alert_interests: ['Food recalls', 'Medical devices'],
    alert_frequency: 'monthly',
    report_style: 'technical',
    created_at: '2026-06-29T12:00:00Z',
    updated_at: '2026-06-29T12:05:00Z',
  })
})

test('loads account basics and updates profile preferences', async () => {
  const user = userEvent.setup()

  render(
    <AuthProvider>
      <ProfilePage onLogout={vi.fn()} goToOnboarding={vi.fn()} />
    </AuthProvider>,
  )

  expect(await screen.findByText('chandu.demo@example.com')).toBeInTheDocument()

  await user.selectOptions(screen.getByLabelText(/Role \/ use case/i), [
    'public_health_analyst',
  ])
  await user.clear(screen.getByLabelText(/^State$/i))
  await user.type(screen.getByLabelText(/^State$/i), 'ca')
  await user.clear(screen.getByLabelText(/ZIP code optional/i))
  await user.type(screen.getByLabelText(/ZIP code optional/i), '94105')
  await user.click(screen.getByLabelText(/Medical devices/i))
  await user.selectOptions(screen.getByLabelText(/Alert frequency/i), ['monthly'])
  await user.selectOptions(screen.getByLabelText(/Report style/i), ['technical'])
  await user.click(screen.getByRole('button', { name: /Save profile/i }))

  await waitFor(() => {
    expect(mockUpdateProfile).toHaveBeenCalledWith({
      role: 'public_health_analyst',
      state: 'CA',
      zip_code: '94105',
      alert_interests: ['Food recalls', 'Medical devices'],
      alert_frequency: 'monthly',
      report_style: 'technical',
    })
  })
  expect(await screen.findByRole('status')).toHaveTextContent('Profile updated.')
})
