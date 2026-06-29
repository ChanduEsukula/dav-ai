import { isAxiosError } from 'axios'
import { useState, type FormEvent } from 'react'
import { useAuth } from '../auth/AuthContext'

type SignupPageProps = {
  onSignedUp: () => void
  goToLogin: () => void
}

function getSignupErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 409) {
      return 'An account already exists for that email. Try signing in instead.'
    }

    if (typeof detail === 'string') {
      return detail
    }

    if (status === 422) {
      return 'Check the highlighted fields and try again.'
    }
  }

  return 'Unable to create your account right now. Please try again in a moment.'
}

export default function SignupPage({ onSignedUp, goToLogin }: SignupPageProps) {
  const { signup } = useAuth()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [acknowledged, setAcknowledged] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const trimmedName = fullName.trim()
  const trimmedEmail = email.trim()
  const emailLooksValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)

  function validateForm(): string | null {
    if (!trimmedName) {
      return 'Full name is required.'
    }

    if (!emailLooksValid) {
      return 'Enter a valid email address.'
    }

    if (password.length < 8) {
      return 'Password must be at least 8 characters.'
    }

    if (password !== confirmPassword) {
      return 'Passwords must match.'
    }

    if (!acknowledged) {
      return 'Please acknowledge that DavAI uses public safety records and is not medical advice.'
    }

    return null
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage('')

    const validationError = validateForm()
    if (validationError) {
      setErrorMessage(validationError)
      return
    }

    setIsSubmitting(true)
    try {
      await signup({
        full_name: trimmedName,
        email: trimmedEmail,
        password,
      })
      onSignedUp()
    } catch (error) {
      setErrorMessage(getSignupErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="auth-page" aria-labelledby="signup-title">
      <div className="auth-hero-card">
        <p className="eyebrow">DavAI account</p>
        <h1 id="signup-title">Create your public safety intelligence workspace.</h1>
        <p>
          Save searches, personalize safety interests, and keep evidence boundaries clear
          while reviewing public-source records.
        </p>
      </div>

      <form className="auth-card" onSubmit={handleSubmit} noValidate>
        <div className="auth-card-header">
          <p className="eyebrow">Signup</p>
          <h2>Start with a privacy-safe profile</h2>
          <p>Use only account details here. Avoid private medical information.</p>
        </div>

        {errorMessage && (
          <div className="auth-alert auth-alert-error" role="alert">
            {errorMessage}
          </div>
        )}

        <label className="auth-field">
          <span>Full name</span>
          <input
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            autoComplete="name"
            placeholder="Chandu Esukula"
            required
          />
        </label>

        <label className="auth-field">
          <span>Email</span>
          <input
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            inputMode="email"
            placeholder="chandu.demo@example.com"
            required
          />
        </label>

        <label className="auth-field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="new-password"
            placeholder="At least 8 characters"
            required
          />
        </label>

        <label className="auth-field">
          <span>Confirm password</span>
          <input
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            autoComplete="new-password"
            placeholder="Re-enter your password"
            required
          />
        </label>

        <label className="auth-check">
          <input
            type="checkbox"
            checked={acknowledged}
            onChange={(event) => setAcknowledged(event.target.checked)}
          />
          <span>
            I understand DavAI reviews public safety records only and does not provide
            medical advice, legal advice, or proof that a product caused an event.
          </span>
        </label>

        <button className="auth-primary-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account…' : 'Create account'}
        </button>

        <p className="auth-switch">
          Already have an account?{' '}
          <button type="button" onClick={goToLogin}>
            Sign in
          </button>
        </p>
      </form>
    </section>
  )
}
