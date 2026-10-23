import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Source } from './Evidence'

describe('Evidence Source Component with FDA URL Validation', () => {
  it('renders official download.open.fda.gov URLs as accessible active links', () => {
    const recallDownloadUrl =
      'https://download.open.fda.gov/drug/enforcement/drug-enforcement-0001-of-0001.json.zip'
    render(<Source url={recallDownloadUrl} label="FDA Recall Source Archive" />)

    const link = screen.getByRole('link', { name: /FDA Recall Source Archive/i })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', recallDownloadUrl)
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('renders official api.fda.gov URLs as active links', () => {
    const apiUrl = 'https://api.fda.gov/drug/enforcement.json'
    render(<Source url={apiUrl} label="FDA API Enforcement" />)

    const link = screen.getByRole('link', { name: /FDA API Enforcement/i })
    expect(link).toHaveAttribute('href', apiUrl)
  })

  it('renders non-clickable fallback text preserving provenance when URL is unsafe or untrusted', () => {
    const untrustedUrl = 'https://malicious-fda.com/fake-recall.json'
    render(<Source url={untrustedUrl} label="Suspicious Source" />)

    expect(screen.queryByRole('link')).not.toBeInTheDocument()
    expect(screen.getByText(/Source URL unavailable · Suspicious Source/)).toBeInTheDocument()
  })

  it('handles empty or malformed URLs safely by preserving label provenance', () => {
    render(<Source url="" label="Empty URL Source" />)
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
    expect(screen.getByText(/Source URL unavailable · Empty URL Source/)).toBeInTheDocument()
  })
})
