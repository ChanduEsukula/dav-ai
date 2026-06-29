import { useEffect, useState, type FormEvent } from 'react'
import type {
  AlertFrequency,
  ReportStyle,
  UserRole,
} from '../api/profile'
import { useAuth } from '../auth/AuthContext'

type ProfilePageProps = {
  onLogout: () => void
  goToOnboarding: () => void
}

const roleOptions: Array<{ value: UserRole; label: string }> = [
  { value: 'consumer', label: 'Consumer / caregiver' },
  { value: 'pharmacy', label: 'Healthcare or pharmacy' },
  { value: 'clinic', label: 'Clinic' },
  { value: 'public_health_analyst', label: 'Food or product safety' },
  { value: 'student_researcher', label: 'Research or data analysis' },
]

const safetyInterestOptions = [
  'Food recalls',
  'Drug recalls',
  'Medical devices',
  'Consumer products',
  'Vehicles',
  'Cosmetics',
]

const alertFrequencyOptions: Array<{ value: AlertFrequency; label: string }> = [
  { value: 'none', label: 'Important only' },
  { value: 'weekly', label: 'Weekly digest' },
  { value: 'monthly', label: 'Monthly digest' },
]

const reportStyleOptions: Array<{ value: ReportStyle; label: string }> = [
  { value: 'simple', label: 'Short summary' },
  { value: 'pharmacy_clinic', label: 'Detailed evidence review' },
  { value: 'technical', label: 'Technical/source-focused' },
]

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return 'Not available'
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
  }).format(new Date(value))
}

export default function ProfilePage({
  onLogout,
  goToOnboarding,
}: ProfilePageProps) {
  const { currentUser, profile, updateProfile, logout } = useAuth()
  const [role, setRole] = useState<UserRole>(profile?.role ?? 'consumer')
  const [stateCode, setStateCode] = useState(profile?.state ?? '')
  const [zipCode, setZipCode] = useState(profile?.zip_code ?? '')
  const [safetyInterests, setSafetyInterests] = useState<string[]>(
    profile?.alert_interests ?? [],
  )
  const [alertFrequency, setAlertFrequency] = useState<AlertFrequency>(
    profile?.alert_frequency ?? 'weekly',
  )
  const [reportStyle, setReportStyle] = useState<ReportStyle>(
    profile?.report_style ?? 'simple',
  )
  const [isSaving, setIsSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    if (!profile) {
      return
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setRole(profile.role ?? 'consumer')
    setStateCode(profile.state ?? '')
    setZipCode(profile.zip_code ?? '')
    setSafetyInterests(profile.alert_interests)
    setAlertFrequency(profile.alert_frequency ?? 'weekly')
    setReportStyle(profile.report_style ?? 'simple')
  }, [profile])

  function toggleSafetyInterest(interest: string) {
    setSafetyInterests((current) =>
      current.includes(interest)
        ? current.filter((value) => value !== interest)
        : [...current, interest],
    )
  }

  function handleLogout() {
    logout()
    onLogout()
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage('')
    setSuccessMessage('')

    if (stateCode.trim() && stateCode.trim().length !== 2) {
      setErrorMessage('Use a two-letter state code, such as MN or CA.')
      return
    }

    if (zipCode.trim() && zipCode.trim().length < 5) {
      setErrorMessage('ZIP code should be at least 5 characters when provided.')
      return
    }

    if (safetyInterests.length === 0) {
      setErrorMessage('Choose at least one safety interest.')
      return
    }

    setIsSaving(true)
    try {
      await updateProfile({
        role,
        state: stateCode.trim() ? stateCode.trim().toUpperCase() : null,
        zip_code: zipCode.trim() || null,
        alert_interests: safetyInterests,
        alert_frequency: alertFrequency,
        report_style: reportStyle,
      })
      setSuccessMessage('Profile updated.')
    } catch {
      setErrorMessage('Unable to update profile right now.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="auth-page auth-page-wide" aria-labelledby="profile-title">
      <div className="auth-hero-card profile-summary-card">
        <p className="eyebrow">Profile</p>
        <h1 id="profile-title">Your DavAI safety profile</h1>
        <p>
          Keep this profile privacy-safe. It personalizes public-source review; it
          should not contain private medical details.
        </p>

        <div className="profile-basics">
          <div>
            <span>Name</span>
            <strong>{currentUser?.full_name ?? 'Signed-in user'}</strong>
          </div>
          <div>
            <span>Email</span>
            <strong>{currentUser?.email ?? 'Not available'}</strong>
          </div>
          <div>
            <span>Member since</span>
            <strong>{formatDate(currentUser?.created_at)}</strong>
          </div>
        </div>

        <div className="profile-actions">
          <button type="button" className="auth-secondary-button" onClick={goToOnboarding}>
            Revisit onboarding
          </button>
          <button type="button" className="auth-ghost-button" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </div>

      <form className="auth-card profile-form-card" onSubmit={handleSubmit}>
        <div className="auth-card-header">
          <p className="eyebrow">Preferences</p>
          <h2>Edit safety interests</h2>
          <p>
            These settings shape saved-search defaults and future report tone. Public
            records are not proof of causation.
          </p>
        </div>

        {errorMessage && (
          <div className="auth-alert auth-alert-error" role="alert">
            {errorMessage}
          </div>
        )}

        {successMessage && (
          <div className="auth-alert auth-alert-success" role="status">
            {successMessage}
          </div>
        )}

        <label className="auth-field">
          <span>Role / use case</span>
          <select
            value={role}
            onChange={(event) => setRole(event.target.value as UserRole)}
          >
            {roleOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <div className="auth-two-column">
          <label className="auth-field">
            <span>State</span>
            <input
              value={stateCode}
              onChange={(event) => setStateCode(event.target.value.toUpperCase())}
              maxLength={2}
              placeholder="MN"
            />
          </label>

          <label className="auth-field">
            <span>ZIP code optional</span>
            <input
              value={zipCode}
              onChange={(event) => setZipCode(event.target.value)}
              inputMode="numeric"
              placeholder="55114"
            />
          </label>
        </div>

        <fieldset className="auth-fieldset">
          <legend>Safety interests</legend>
          <div className="auth-chip-grid">
            {safetyInterestOptions.map((interest) => (
              <label className="auth-chip" key={interest}>
                <input
                  type="checkbox"
                  checked={safetyInterests.includes(interest)}
                  onChange={() => toggleSafetyInterest(interest)}
                />
                <span>{interest}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="auth-two-column">
          <label className="auth-field">
            <span>Alert frequency</span>
            <select
              value={alertFrequency}
              onChange={(event) =>
                setAlertFrequency(event.target.value as AlertFrequency)
              }
            >
              {alertFrequencyOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="auth-field">
            <span>Report style</span>
            <select
              value={reportStyle}
              onChange={(event) => setReportStyle(event.target.value as ReportStyle)}
            >
              {reportStyleOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <button className="auth-primary-button" type="submit" disabled={isSaving}>
          {isSaving ? 'Saving profile…' : 'Save profile'}
        </button>
      </form>
    </section>
  )
}
