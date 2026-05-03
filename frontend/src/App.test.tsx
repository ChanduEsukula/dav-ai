import { render, screen } from '@testing-library/react'
import App from './App'

test('renders MedSignal AI landing page', () => {
  render(<App />)

  expect(
    screen.getByRole('button', { name: /MedSignal AI/i })
  ).toBeInTheDocument()

  expect(
    screen.getByRole('heading', { name: /Public safety/i })
  ).toBeInTheDocument()

  expect(
    screen.getByRole('button', { name: /Search RecallRadar/i })
  ).toBeInTheDocument()

  expect(
    screen.getByRole('heading', { name: /Search public FDA recall signals/i })
  ).toBeInTheDocument()

  expect(
    screen.getByRole('heading', {
      name: /Explore public FAERS adverse-event reporting patterns/i,
    })
  ).toBeInTheDocument()
})