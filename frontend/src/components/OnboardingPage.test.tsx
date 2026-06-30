import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import { getCurrentUser } from '../api/auth'
import { getProfile, updateProfile } from '../api/profile'
import { AuthProvider } from '../auth/AuthContext'
import { clearStoredAuthToken, setStoredAuthToken } from '../api/client'
import OnboardingPage from './OnboardingPage'

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
  setStoredAuthToken('onboarding-token')
  mockGetCurrentUser.mockResolvedValue({
    id: 'user-1',
    full_name: 'Chandu Esukula',
    email: 'chandu.demo@example.com',
    created_at: '2026-06-29T12:00:00Z',
    updated_at: '2026-06-29T12:00:00Z',
  })
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
  mockUpdateProfile.mockResolvedValue({
    user_id: 'user-1',
    role: 'public_health_analyst',
    state: 'MN',
    zip_code: '55114',
    alert_interests: ['Food recalls', 'Medical devices'],
    alert_frequency: 'weekly',
    report_style: 'technical',
    created_at: '2026-06-29T12:00:00Z',
    updated_at: '2026-06-29T12:05:00Z',
  })
})

test('saves onboarding profile preferences', async () => {
  const user = userEvent.setup()
  const onComplete = vi.fn()

  render(
    <AuthProvider>
      <OnboardingPage onComplete={onComplete} />
    </AuthProvider>,
  )

  await waitFor(() => {
    expect(mockGetProfile).toHaveBeenCalled()
  })

  expect(screen.getByLabelText(/^State$/i)).toHaveValue('MN')
  expect(screen.getByLabelText(/ZIP code optional/i)).toHaveValue('55114')

  await user.click(screen.getByLabelText(/Food safety/i))
  const safetyInterestsGroup = screen.getByRole('group', {
    name: /Safety interests/i,
  })
  await user.click(within(safetyInterestsGroup).getByLabelText(/Food recalls/i))
  await user.click(within(safetyInterestsGroup).getByLabelText(/Medical devices/i))
  await user.click(screen.getByLabelText(/Technical\/source-focused/i))
  await user.click(screen.getByRole('button', { name: /Save preferences/i }))

  await waitFor(() => {
    expect(onComplete).toHaveBeenCalled()
  })
  expect(mockUpdateProfile).toHaveBeenCalledWith({
    role: 'public_health_analyst',
    state: 'MN',
    zip_code: '55114',
    alert_interests: ['Food recalls', 'Medical devices'],
    alert_frequency: 'weekly',
    report_style: 'technical',
  })
})
