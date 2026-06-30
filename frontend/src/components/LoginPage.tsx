import { isAxiosError } from 'axios'
import { useState, type FormEvent } from 'react'
import { isProfileComplete } from '../api/profile'
import { useAuth } from '../auth/AuthContext'

type LoginPageProps = {
  onSignedIn: (destination: 'onboarding' | 'profile') => void
  goToSignup: () => void
}

function getLoginErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const status = error.response?.status

    if (status === 401) {
      return 'Invalid email or password.'
    }

    if (status === 422) {
      return 'Enter a valid email and password.'
    }
  }

  return 'Unable to sign in right now. Please check the backend connection and try again.'
}

export default function LoginPage({ onSignedIn, goToSignup }: LoginPageProps) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage('')

    if (!email.trim() || !password) {
      setErrorMessage('Email and password are required.')
      return
    }

    setIsSubmitting(true)
    try {
      const result = await login({
        email: email.trim(),
        password,
      })
      onSignedIn(isProfileComplete(result.profile) ? 'profile' : 'onboarding')
    } catch (error) {
      setErrorMessage(getLoginErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="auth-page auth-page-compact" aria-labelledby="login-title">
      <div className="auth-hero-card">
        <p className="eyebrow">Welcome back</p>
        <h1 id="login-title">Sign in to your saved safety workspace.</h1>
        <p>
          Continue reviewing public records with your saved searches, preferences, and
          source-aware profile.
        </p>
      </div>

      <form className="auth-card" onSubmit={handleSubmit} noValidate>
        <div className="auth-card-header">
          <p className="eyebrow">Login</p>
          <h2>Access DavAI</h2>
          <p>Authentication is portfolio-demo grade for this sprint.</p>
        </div>

        {errorMessage && (
          <div className="auth-alert auth-alert-error" role="alert">
            {errorMessage}
          </div>
        )}

        <label className="auth-field">
          <span>Email</span>
          <input
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            inputMode="email"
            placeholder="alex@example.com"
            required
          />
        </label>

        <label className="auth-field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
            placeholder="Your password"
            required
          />
        </label>

        <button className="auth-primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Signing in…' : 'Sign in'}
        </button>

        <p className="auth-switch">
          New to DavAI?{' '}
          <button type="button" onClick={goToSignup}>
            Create account
          </button>
        </p>
      </form>
    </section>
  )
}
