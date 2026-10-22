import { render, screen } from '@testing-library/react'
import { expect, it } from 'vitest'
import App from './App'

it('presents an accessible search-first experience with no account requirement', () => {
  window.history.replaceState(null, '', '/')
  render(<App />)
  expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Explore the evidence')
  expect(screen.getByRole('search')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /login|chat|monitor/i })).not.toBeInTheDocument()
})
