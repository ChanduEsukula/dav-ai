/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  getCurrentUser,
  login as loginRequest,
  signup as signupRequest,
  type AuthUser,
  type LoginPayload,
  type SignupPayload,
} from '../api/auth'
import {
  getProfile,
  updateProfile as updateProfileRequest,
  type UserProfile,
  type UserProfileUpdate,
} from '../api/profile'
import {
  clearStoredAuthToken,
  getStoredAuthToken,
  setStoredAuthToken,
} from '../api/client'

type AuthResult = {
  user: AuthUser
  profile: UserProfile | null
}

type AuthContextValue = {
  token: string | null
  currentUser: AuthUser | null
  profile: UserProfile | null
  isLoading: boolean
  signup: (payload: SignupPayload) => Promise<AuthResult>
  login: (payload: LoginPayload) => Promise<AuthResult>
  logout: () => void
  refreshCurrentUser: () => Promise<AuthUser | null>
  refreshProfile: () => Promise<UserProfile | null>
  updateProfile: (payload: UserProfileUpdate) => Promise<UserProfile>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredAuthToken())
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const clearSession = useCallback(() => {
    clearStoredAuthToken()
    setToken(null)
    setCurrentUser(null)
    setProfile(null)
  }, [])

  const refreshProfile = useCallback(async () => {
    if (!getStoredAuthToken()) {
      setProfile(null)
      return null
    }

    const nextProfile = await getProfile()
    setProfile(nextProfile)
    return nextProfile
  }, [])

  const refreshCurrentUser = useCallback(async () => {
    if (!getStoredAuthToken()) {
      clearSession()
      return null
    }

    try {
      const nextUser = await getCurrentUser()
      setCurrentUser(nextUser)
      return nextUser
    } catch (error) {
      clearSession()
      throw error
    }
  }, [clearSession])

  const hydrateSession = useCallback(async () => {
    const storedToken = getStoredAuthToken()
    if (!storedToken) {
      clearSession()
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setToken(storedToken)

    try {
      const [nextUser, nextProfile] = await Promise.all([
        getCurrentUser(),
        getProfile(),
      ])
      setCurrentUser(nextUser)
      setProfile(nextProfile)
    } catch {
      clearSession()
    } finally {
      setIsLoading(false)
    }
  }, [clearSession])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void hydrateSession()
  }, [hydrateSession])

  const signup = useCallback(async (payload: SignupPayload) => {
    const response = await signupRequest(payload)
    setStoredAuthToken(response.access_token)
    setToken(response.access_token)
    setCurrentUser(response.user)

    const nextProfile = await getProfile()
    setProfile(nextProfile)

    return {
      user: response.user,
      profile: nextProfile,
    }
  }, [])

  const login = useCallback(async (payload: LoginPayload) => {
    const response = await loginRequest(payload)
    setStoredAuthToken(response.access_token)
    setToken(response.access_token)
    setCurrentUser(response.user)

    const nextProfile = await getProfile()
    setProfile(nextProfile)

    return {
      user: response.user,
      profile: nextProfile,
    }
  }, [])

  const logout = useCallback(() => {
    clearSession()
  }, [clearSession])

  const updateProfile = useCallback(async (payload: UserProfileUpdate) => {
    const nextProfile = await updateProfileRequest(payload)
    setProfile(nextProfile)
    return nextProfile
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      currentUser,
      profile,
      isLoading,
      signup,
      login,
      logout,
      refreshCurrentUser,
      refreshProfile,
      updateProfile,
    }),
    [
      token,
      currentUser,
      profile,
      isLoading,
      signup,
      login,
      logout,
      refreshCurrentUser,
      refreshProfile,
      updateProfile,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider.')
  }

  return context
}
