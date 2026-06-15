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
