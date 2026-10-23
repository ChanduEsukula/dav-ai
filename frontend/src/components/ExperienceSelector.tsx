import { useCallback } from 'react'
import {
  type ExperienceMode,
  saveExperienceModePreference,
} from './experienceState'

interface ExperienceSelectorProps {
  mode: ExperienceMode
  onChange: (mode: ExperienceMode) => void
}

export default function ExperienceSelector({ mode, onChange }: ExperienceSelectorProps) {
  const handleSelect = useCallback(
    (newMode: ExperienceMode) => {
      if (newMode !== mode) {
        saveExperienceModePreference(newMode)
        onChange(newMode)
      }
    },
    [mode, onChange]
  )

  const handleKeyDown = (e: React.KeyboardEvent, targetMode: ExperienceMode) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault()
      handleSelect(targetMode)
    } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
      e.preventDefault()
      handleSelect('research_pro')
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault()
      handleSelect('everyday')
    }
  }

  return (
    <div className="experience-toggle-wrapper">
      <span className="experience-toggle-label" id="experience-mode-label">
        Experience
      </span>
      <div
        className="experience-segmented-control"
        role="group"
        aria-labelledby="experience-mode-label"
      >
        <button
          type="button"
          className="experience-toggle-btn"
          aria-pressed={mode === 'everyday'}
          onClick={() => handleSelect('everyday')}
          onKeyDown={(e) => handleKeyDown(e, 'everyday')}
          title="Switch to Everyday: Simple, consumer-friendly medication information"
        >
          <span className="mode-icon-indicator" aria-hidden="true">🌱</span>
          <span>Everyday</span>
          {mode === 'everyday' && (
            <span className="mode-active-indicator" aria-hidden="true" />
          )}
        </button>

        <button
          type="button"
          className="experience-toggle-btn"
          aria-pressed={mode === 'research_pro'}
          onClick={() => handleSelect('research_pro')}
          onKeyDown={(e) => handleKeyDown(e, 'research_pro')}
          title="Switch to Research Pro: Professional multi-product cohort research workspace"
        >
          <span className="mode-icon-indicator" aria-hidden="true">🔬</span>
          <span>Research Pro</span>
          {mode === 'research_pro' && (
            <span className="mode-active-indicator" aria-hidden="true" />
          )}
        </button>
      </div>
    </div>
  )
}
