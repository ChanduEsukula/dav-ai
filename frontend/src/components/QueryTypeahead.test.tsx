import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import QueryTypeahead from './QueryTypeahead'

function TypeaheadHarness({
  area,
}: {
  area?: 'pharmacy' | 'food' | 'cosmetic'
}) {
  const [value, setValue] = useState('')

  return (
    <QueryTypeahead
      id="query"
      value={value}
      onChange={setValue}
      area={area}
      placeholder="Search"
      showWorkflow={!area}
    />
  )
}

function SubmitHarness() {
  const [value, setValue] = useState('')
  const [submittedValue, setSubmittedValue] = useState('')

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        setSubmittedValue(value)
      }}
    >
      <QueryTypeahead
        id="query"
        value={value}
        onChange={setValue}
        area="food"
        placeholder="Search"
      />
      <button type="submit">Search</button>
      <output aria-label="Submitted query">{submittedValue}</output>
    </form>
  )
}

test('supports arrow selection and Enter for a strawberry suggestion', async () => {
  const user = userEvent.setup()
  render(<TypeaheadHarness area="food" />)

  const input = screen.getByRole('combobox')
  await user.type(input, 'stra')

  expect(screen.getByRole('listbox')).toBeInTheDocument()
  await user.keyboard('{ArrowDown}{Enter}')

  expect(input).toHaveValue('strawberry')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
})

test('Escape closes suggestions without replacing the typed query', async () => {
  const user = userEvent.setup()
  render(<TypeaheadHarness area="cosmetic" />)

  const input = screen.getByRole('combobox')
  await user.type(input, 'haird')
  expect(screen.getByRole('option', { name: 'hair dye' })).toBeInTheDocument()

  await user.keyboard('{Escape}')

  expect(input).toHaveValue('haird')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
})

test('clicking a universal suggestion selects it and shows its workflow', async () => {
  const user = userEvent.setup()
  render(<TypeaheadHarness />)

  const input = screen.getByRole('combobox')
  await user.type(input, 'xan')

  await user.click(screen.getByRole('option', { name: /xanax.*Pharmacy Safety/i }))

  expect(input).toHaveValue('xanax')
})

test('shows expanded curated food suggestions', async () => {
  const user = userEvent.setup()
  render(<TypeaheadHarness area="food" />)

  const input = screen.getByRole('combobox')
  await user.type(input, 'gua')

  expect(screen.getByRole('option', { name: 'guava' })).toBeInTheDocument()

  await user.clear(input)
  await user.type(input, 'man')

  expect(screen.getByRole('option', { name: 'mango' })).toBeInTheDocument()
})

test('shows expanded curated cosmetic and pharmacy suggestions', async () => {
  const user = userEvent.setup()
  const { rerender } = render(<TypeaheadHarness area="cosmetic" />)

  const input = screen.getByRole('combobox')
  await user.type(input, 'sun')
  expect(screen.getByRole('option', { name: 'sunscreen' })).toBeInTheDocument()

  rerender(<TypeaheadHarness area="pharmacy" />)
  await user.clear(screen.getByRole('combobox'))
  await user.type(screen.getByRole('combobox'), 'ibu')

  expect(screen.getByRole('option', { name: 'ibuprofen' })).toBeInTheDocument()
})

test('shows an empty helper for unknown terms without blocking submit', async () => {
  const user = userEvent.setup()
  render(<SubmitHarness />)

  const input = screen.getByRole('combobox')
  await user.type(input, 'zzterm')

  expect(
    screen.getByText(
      'No saved suggestion yet. You can still search this public-record term.',
    ),
  ).toBeInTheDocument()
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()

  await user.keyboard('{Enter}')

  expect(screen.getByLabelText('Submitted query')).toHaveTextContent('zzterm')
})

test('caps visible suggestions and ranks prefix matches first', async () => {
  const user = userEvent.setup()
  render(<TypeaheadHarness />)

  const input = screen.getByRole('combobox')
  await user.type(input, 'er')

  expect(screen.getAllByRole('option')).toHaveLength(8)

  await user.clear(input)
  await user.type(input, 'but')

  const options = screen.getAllByRole('option')
  expect(options[0]).toHaveTextContent('butter')
  expect(
    options.findIndex((option) => option.textContent?.includes('peanut butter')),
  ).toBeGreaterThan(0)
})
