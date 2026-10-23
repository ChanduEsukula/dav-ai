export type ExperienceMode = 'everyday' | 'research_pro'

export const STORAGE_KEY_EXPERIENCE_MODE = 'dav_ai_experience_mode'

export function getInitialExperienceMode(): ExperienceMode {
  try {
    const saved = localStorage.getItem(STORAGE_KEY_EXPERIENCE_MODE)
    if (saved === 'everyday' || saved === 'research_pro') {
      return saved
    }
  } catch {
    // Gracefully handle storage disabled/sandboxed environments
  }
  return 'everyday'
}

export function saveExperienceModePreference(mode: ExperienceMode): void {
  try {
    // Only non-sensitive UI preference is stored. Never store pairing or bearer credentials.
    localStorage.setItem(STORAGE_KEY_EXPERIENCE_MODE, mode)
  } catch {
    // Ignore storage quota or permission errors
  }
}
