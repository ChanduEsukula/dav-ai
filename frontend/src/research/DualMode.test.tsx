import { render, screen, fireEvent } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import App from '../App'
import { STORAGE_KEY_EXPERIENCE_MODE } from '../components/experienceState'

describe('Dual-Mode Experience (Everyday & Research Pro)', () => {
  beforeEach(() => {
    localStorage.clear()
    window.history.replaceState(null, '', '/ask')
  })

  it('renders Everyday mode by default with warm consumer headline and controls', () => {
    render(<App />)

    // Verify theme attribute
    expect(document.documentElement).toHaveAttribute('data-theme', 'everyday')

    // Verify Everyday heading and supporting text
    expect(
      screen.getByRole('heading', { name: 'Understand your medication information' })
    ).toBeInTheDocument()
    expect(
      screen.getByText(/explore fda-derived drug labeling, historical recalls/i)
    ).toBeInTheDocument()

    // Mode button state
    const everydayBtn = screen.getByRole('button', { name: /everyday/i })
    expect(everydayBtn).toHaveAttribute('aria-pressed', 'true')
  })

  it('switches to Research Pro dynamically without full page reload', () => {
    render(<App />)

    const researchBtn = screen.getByRole('button', { name: /research pro/i })
    fireEvent.click(researchBtn)

    // Verify theme attribute updated
    expect(document.documentElement).toHaveAttribute('data-theme', 'research_pro')

    // Verify Research Pro headline and enterprise subtitle
    expect(
      screen.getByRole('heading', { name: 'Pharmaceutical Evidence Workspace' })
    ).toBeInTheDocument()
    expect(
      screen.getByText(/investigate product-specific labeling, historical recall applicability/i)
    ).toBeInTheDocument()

    // Verify preference persisted to localStorage
    expect(localStorage.getItem(STORAGE_KEY_EXPERIENCE_MODE)).toBe('research_pro')

    // Verify Research Pro button is now pressed
    expect(researchBtn).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: /everyday/i })).toHaveAttribute(
      'aria-pressed',
      'false'
    )
  })

  it('preserves mode preference when navigating between routes', () => {
    localStorage.setItem(STORAGE_KEY_EXPERIENCE_MODE, 'research_pro')
    const { rerender } = render(<App />)

    expect(document.documentElement).toHaveAttribute('data-theme', 'research_pro')

    // Navigate to explorer
    window.history.replaceState(null, '', '/')
    rerender(<App />)

    // Theme remains research_pro
    expect(document.documentElement).toHaveAttribute('data-theme', 'research_pro')
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Explore the evidence')
  })
})
