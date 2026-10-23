import { render, screen, fireEvent } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import ExperienceSelector from './ExperienceSelector'
import {
  STORAGE_KEY_EXPERIENCE_MODE,
  getInitialExperienceMode,
  saveExperienceModePreference,
} from './experienceState'

describe('ExperienceSelector Component', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('renders the segmented control with accessible ARIA semantics', () => {
    render(<ExperienceSelector mode="everyday" onChange={vi.fn()} />)

    const group = screen.getByRole('group', { name: /experience/i })
    expect(group).toBeInTheDocument()

    const everydayBtn = screen.getByRole('button', { name: /everyday/i })
    const researchBtn = screen.getByRole('button', { name: /research pro/i })

    expect(everydayBtn).toHaveAttribute('aria-pressed', 'true')
    expect(researchBtn).toHaveAttribute('aria-pressed', 'false')
  })

  it('switches to research_pro when clicked and persists preference', () => {
    const handleChange = vi.fn()
    render(<ExperienceSelector mode="everyday" onChange={handleChange} />)

    const researchBtn = screen.getByRole('button', { name: /research pro/i })
    fireEvent.click(researchBtn)

    expect(handleChange).toHaveBeenCalledWith('research_pro')
    expect(localStorage.getItem(STORAGE_KEY_EXPERIENCE_MODE)).toBe('research_pro')
  })

  it('supports arrow key navigation between modes', () => {
    const handleChange = vi.fn()
    const { rerender } = render(<ExperienceSelector mode="everyday" onChange={handleChange} />)

    const everydayBtn = screen.getByRole('button', { name: /everyday/i })

    // Arrow Right switches from everyday to research_pro
    fireEvent.keyDown(everydayBtn, { key: 'ArrowRight' })
    expect(handleChange).toHaveBeenCalledWith('research_pro')

    // Rerender with research_pro active
    rerender(<ExperienceSelector mode="research_pro" onChange={handleChange} />)
    const researchBtn = screen.getByRole('button', { name: /research pro/i })

    // Arrow Left switches from research_pro to everyday
    fireEvent.keyDown(researchBtn, { key: 'ArrowLeft' })
    expect(handleChange).toHaveBeenCalledWith('everyday')
  })

  it('initializes from localStorage preference safely', () => {
    localStorage.setItem(STORAGE_KEY_EXPERIENCE_MODE, 'research_pro')
    expect(getInitialExperienceMode()).toBe('research_pro')

    localStorage.setItem(STORAGE_KEY_EXPERIENCE_MODE, 'invalid_mode')
    expect(getInitialExperienceMode()).toBe('everyday')

    localStorage.clear()
    expect(getInitialExperienceMode()).toBe('everyday')
  })

  it('never stores sensitive tokens or capabilities in localStorage', () => {
    saveExperienceModePreference('everyday')
    expect(localStorage.getItem(STORAGE_KEY_EXPERIENCE_MODE)).toBe('everyday')
    expect(localStorage.getItem('capability')).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('session')).toBeNull()
    expect(localStorage.getItem('pairing')).toBeNull()
  })
})
