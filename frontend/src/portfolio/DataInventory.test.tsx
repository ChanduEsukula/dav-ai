import { render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import DataInventory from './DataInventory'
import { getDataInventory } from '../api/drugCatalog'
import fixture from '../test/data-inventory.fixture.json'

vi.mock('../api/drugCatalog', () => ({ getDataInventory: vi.fn() }))
it('uses verified API inventory rather than the earlier corpus statistic', async () => {
  vi.mocked(getDataInventory).mockResolvedValue(fixture as Awaited<ReturnType<typeof getDataInventory>>)
  render(<DataInventory mode="research_pro" />)
  expect(await screen.findByText('83,684')).toBeInTheDocument()
  expect(screen.queryByText('262,887')).not.toBeInTheDocument()
  expect(screen.getByText(/including retained context\/withheld documents/i)).toBeInTheDocument()
  expect(screen.getByText(/Publication not authorized/)).toBeInTheDocument()
})
it('does not invent public statistics when inventory is unavailable', async () => {
  vi.mocked(getDataInventory).mockRejectedValue(new Error('unavailable'))
  render(<DataInventory mode="everyday" />)
  expect(await screen.findByText(/Dataset metrics could not be loaded/)).toBeInTheDocument()
  expect(screen.queryByText('83,684')).not.toBeInTheDocument()
})

it('shows exactly three primary metrics and one separate frozen coverage indicator in both modes', async () => {
  vi.mocked(getDataInventory).mockResolvedValue(fixture as Awaited<ReturnType<typeof getDataInventory>>)
  const { container, rerender } = render(<DataInventory mode="everyday" />)
  await screen.findByText('83,684')
  expect(container.querySelectorAll('.inventory-metric')).toHaveLength(3)
  expect(screen.getByText('17,974')).toBeInTheDocument()
  expect(screen.getByText('3,174')).toBeInTheDocument()
  expect(screen.getByText('Frozen-release coverage')).toBeInTheDocument()
  expect(screen.queryByText(/Distinct product NDCs:/)).not.toBeInTheDocument()
  rerender(<DataInventory mode="research_pro" />)
  expect(container.querySelectorAll('.inventory-metric')).toHaveLength(3)
  expect(screen.getByText(/Distinct product NDCs:/)).toBeInTheDocument()
})

it('retries failed inventory without inventing counts', async () => {
  const { fireEvent } = await import('@testing-library/react')
  vi.mocked(getDataInventory).mockRejectedValueOnce(new Error('unavailable')).mockResolvedValue(fixture as Awaited<ReturnType<typeof getDataInventory>>)
  render(<DataInventory mode="everyday" />)
  fireEvent.click(await screen.findByRole('button', {name:'Retry dataset metrics'}))
  expect(await screen.findByText('83,684')).toBeInTheDocument()
})
