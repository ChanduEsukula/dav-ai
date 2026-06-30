import { useEffect, useState, type FormEvent } from 'react'
import type {
  AlertFrequency,
  ReportStyle,
  UserRole,
} from '../api/profile'
import { useAuth } from '../auth/AuthContext'

type OnboardingPageProps = {
  onComplete: () => void
}

type UseCaseId =
  | 'consumer'
  | 'caregiver'
  | 'healthcare_pharmacy'
  | 'food_safety'
  | 'product_safety'
  | 'research'

type UseCaseOption = {
  id: UseCaseId
  label: string
  description: string
  role: UserRole
}

const useCaseOptions: UseCaseOption[] = [
  {
    id: 'consumer',
    label: 'Consumer',
    description: 'Track products, medications, food, or devices you care about.',
    role: 'consumer',
  },
  {
    id: 'caregiver',
    label: 'Parent or caregiver',
    description: 'Keep a calmer watchlist for household or family safety topics.',
    role: 'consumer',
  },
  {
    id: 'healthcare_pharmacy',
    label: 'Healthcare or pharmacy',
    description: 'Review public records with clinical and pharmacy context in mind.',
    role: 'pharmacy',
  },
  {
    id: 'food_safety',
    label: 'Food safety',
    description: 'Follow food recalls and outbreak-context topics.',
    role: 'public_health_analyst',
  },
  {
    id: 'product_safety',
    label: 'Product safety',
    description: 'Watch consumer-product, device, vehicle, or household risks.',
    role: 'public_health_analyst',
  },
  {
    id: 'research',
    label: 'Research or data analysis',
    description: 'Explore source-aware signals and evidence boundaries.',
    role: 'student_researcher',
  },
]

const safetyInterestOptions = [
  'Food recalls',
  'Drug recalls',
  'Medical devices',
  'Consumer products',
  'Vehicles',
  'Cosmetics',
]

const alertFrequencyOptions: Array<{
  value: AlertFrequency
  label: string
  description: string
}> = [
  {
    value: 'none',
    label: 'Important only',
    description: 'Keep alerts quiet while preserving your profile interests.',
  },
  {
    value: 'weekly',
    label: 'Weekly digest',
    description: 'A portfolio-demo cadence for reviewing saved public-data checks.',
  },
  {
    value: 'monthly',
    label: 'Monthly digest',
    description: 'A slower summary cadence for low-pressure monitoring.',
  },
]

const reportStyleOptions: Array<{
  value: ReportStyle
  label: string
  description: string
}> = [
  {
    value: 'simple',
    label: 'Short summary',
    description: 'Plain-language highlights with clear caveats.',
  },
  {
    value: 'pharmacy_clinic',
    label: 'Detailed evidence review',
    description: 'More context for healthcare or pharmacy-style review.',
  },
  {
    value: 'technical',
    label: 'Technical/source-focused',
    description: 'Prioritize source names, identifiers, and provenance.',
  },
]

function getUseCaseFromRole(role: UserRole | null | undefined): UseCaseId {
  if (role === 'pharmacy' || role === 'clinic') {
    return 'healthcare_pharmacy'
  }

  if (role === 'public_health_analyst') {
    return 'food_safety'
  }

  if (role === 'student_researcher') {
    return 'research'
  }

  return 'consumer'
}

export default function OnboardingPage({ onComplete }: OnboardingPageProps) {
  const { profile, updateProfile } = useAuth()
  const [useCase, setUseCase] = useState<UseCaseId>(() =>
    getUseCaseFromRole(profile?.role),
  )
  const [stateCode, setStateCode] = useState(profile?.state ?? 'MN')
  const [zipCode, setZipCode] = useState(profile?.zip_code ?? '55114')
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
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    if (!profile) {
      return
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setUseCase(getUseCaseFromRole(profile.role))
    setStateCode(profile.state ?? 'MN')
    setZipCode(profile.zip_code ?? '55114')
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage('')

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

    const selectedUseCase = useCaseOptions.find((option) => option.id === useCase)
    if (!selectedUseCase) {
      setErrorMessage('Choose a role or use case.')
      return
    }

    setIsSaving(true)
    try {
      await updateProfile({
        role: selectedUseCase.role,
        state: stateCode.trim() ? stateCode.trim().toUpperCase() : null,
        zip_code: zipCode.trim() || null,
        alert_interests: safetyInterests,
        alert_frequency: alertFrequency,
        report_style: reportStyle,
      })
      onComplete()
    } catch {
      setErrorMessage('Unable to save onboarding preferences right now.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="auth-page auth-page-wide" aria-labelledby="onboarding-title">
      <div className="auth-hero-card">
        <p className="eyebrow">Onboarding</p>
        <h1 id="onboarding-title">Tune DavAI to the public safety topics you monitor.</h1>
        <p>
          Only choose topics you want DavAI to monitor. Avoid entering private medical
          details.
        </p>
      </div>

      <form className="auth-card profile-form-card" onSubmit={handleSubmit}>
        {errorMessage && (
          <div className="auth-alert auth-alert-error" role="alert">
            {errorMessage}
          </div>
        )}

        <fieldset className="auth-fieldset">
          <legend>Role or use case</legend>
          <div className="auth-option-grid">
            {useCaseOptions.map((option) => (
              <label className="auth-option-card" key={option.id}>
                <input
                  type="radio"
                  name="use-case"
                  value={option.id}
                  checked={useCase === option.id}
                  onChange={() => setUseCase(option.id)}
                />
                <span>
                  <strong>{option.label}</strong>
                  <small>{option.description}</small>
                </span>
              </label>
            ))}
          </div>
        </fieldset>

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

        <fieldset className="auth-fieldset">
          <legend>Alert frequency</legend>
          <div className="auth-option-grid auth-option-grid-three">
            {alertFrequencyOptions.map((option) => (
              <label className="auth-option-card" key={option.value}>
                <input
                  type="radio"
                  name="alert-frequency"
                  value={option.value}
                  checked={alertFrequency === option.value}
                  onChange={() => setAlertFrequency(option.value)}
                />
                <span>
                  <strong>{option.label}</strong>
                  <small>{option.description}</small>
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset className="auth-fieldset">
          <legend>Report style</legend>
          <div className="auth-option-grid auth-option-grid-three">
            {reportStyleOptions.map((option) => (
              <label className="auth-option-card" key={option.value}>
                <input
                  type="radio"
                  name="report-style"
                  value={option.value}
                  checked={reportStyle === option.value}
                  onChange={() => setReportStyle(option.value)}
                />
                <span>
                  <strong>{option.label}</strong>
                  <small>{option.description}</small>
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        <button className="auth-primary-button" type="submit" disabled={isSaving}>
          {isSaving ? 'Saving preferences…' : 'Save preferences'}
        </button>
      </form>
    </section>
  )
}
