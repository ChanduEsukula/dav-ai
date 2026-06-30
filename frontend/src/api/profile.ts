import { apiClient } from './client'

export type UserRole =
  | 'consumer'
  | 'pharmacy'
  | 'clinic'
  | 'public_health_analyst'
  | 'student_researcher'

export type AlertFrequency = 'none' | 'weekly' | 'monthly'
export type ReportStyle = 'simple' | 'technical' | 'pharmacy_clinic'

export type UserProfile = {
  user_id: string
  role: UserRole | null
  state: string | null
  zip_code: string | null
  alert_interests: string[]
  alert_frequency: AlertFrequency | null
  report_style: ReportStyle | null
  created_at: string
  updated_at: string
}

export type UserProfileUpdate = {
  role?: UserRole | null
  state?: string | null
  zip_code?: string | null
  alert_interests?: string[]
  alert_frequency?: AlertFrequency | null
  report_style?: ReportStyle | null
}

export function isProfileComplete(profile: UserProfile | null): boolean {
  return Boolean(
    profile?.role &&
      profile.alert_interests.length > 0 &&
      profile.alert_frequency &&
      profile.report_style,
  )
}

export async function getProfile(): Promise<UserProfile> {
  const response = await apiClient.get<UserProfile>('/api/v1/profile')
  return response.data
}

export async function updateProfile(
  payload: UserProfileUpdate,
): Promise<UserProfile> {
  const response = await apiClient.put<UserProfile>('/api/v1/profile', payload)
  return response.data
}
