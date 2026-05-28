import { render, screen } from '@testing-library/react'
import App from './App'

beforeEach(() => {
  window.history.replaceState(null, '', '/')
})

test('renders Dav AI landing page', () => {
  render(<App />)

  expect(screen.getByRole('button', { name: /Dav AI/i })).toBeInTheDocument()

  expect(screen.getByRole('heading', { name: /Public safety/i })).toBeInTheDocument()

  expect(
    screen.getByRole('button', {
      name: /RecallRadar.*Search public FDA recall records/i,
    }),
  ).toBeInTheDocument()

  expect(
    screen.getByRole('button', {
      name: /DrugSignal.*FAERS adverse-event reporting patterns/i,
    }),
  ).toBeInTheDocument()

  expect(
    screen.getByRole('button', {
      name: /Health Pulse.*sample regional public-data signal reviews/i,
    }),
  ).toBeInTheDocument()

  expect(screen.getByRole('button', { name: /How it works/i })).toBeInTheDocument()

  expect(
    screen.getByRole('heading', { name: /Search public FDA recall signals/i }),
  ).toBeInTheDocument()

  expect(
    screen.getByRole('heading', {
      name: /Explore public FAERS adverse-event reporting patterns/i,
    }),
  ).toBeInTheDocument()
})

test('does not expose placeholder account pages in the main demo navigation', () => {
  render(<App />)

  expect(screen.queryByRole('button', { name: /Profile/i })).not.toBeInTheDocument()

  expect(screen.queryByRole('button', { name: /Sign Up/i })).not.toBeInTheDocument()
})

test('ignores old placeholder account page URLs', () => {
  window.history.replaceState(null, '', '/?page=signup')

  render(<App />)

  expect(screen.getByRole('heading', { name: /Public safety/i })).toBeInTheDocument()

  expect(screen.queryByText(/Early access placeholder/i)).not.toBeInTheDocument()
})