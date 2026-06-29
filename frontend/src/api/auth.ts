import { apiClient } from './client'

export type AuthUser = {
  id: string
  full_name: string
  email: string
  created_at: string
  updated_at: string
}

export type AuthResponse = {
  access_token: string
  token_type: 'bearer'
  user: AuthUser
}

export type SignupPayload = {
  full_name: string
  email: string
  password: string
}

export type LoginPayload = {
  email: string
  password: string
}

export async function signup(payload: SignupPayload): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/api/v1/auth/signup', payload)
  return response.data
}

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', payload)
  return response.data
}

export async function getCurrentUser(): Promise<AuthUser> {
  const response = await apiClient.get<AuthUser>('/api/v1/auth/me')
  return response.data
}
