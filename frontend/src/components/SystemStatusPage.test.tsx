import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import SystemStatusPage from './SystemStatusPage'
import { getSystemStatus } from '../api/systemStatus'

vi.mock('../api/systemStatus', () => ({
  getSystemStatus: vi.fn(),
}))

describe('SystemStatusPage', () => {
  it('renders system status details', async () => {
    vi.mocked(getSystemStatus).mockResolvedValue({
      status: 'ok',
      app: 'MedTrek AI API',
      version: '0.1.0',
      database: {
        configured: true,
        audit_readable: true,
      },
      sources: {
        registered_count: 2,
        available: true,
      },
      modules: ['RecallRadar', 'DrugSignal', 'Sources', 'Audit History'],
    })

    render(<SystemStatusPage />)

    expect(screen.getByText('Checking system status...')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('System Status')).toBeInTheDocument()
      expect(screen.getByText('API: ok')).toBeInTheDocument()
      expect(screen.getByText('Database configured: Yes')).toBeInTheDocument()
      expect(screen.getByText('Audit readable: Yes')).toBeInTheDocument()
      expect(screen.getByText('MedTrek AI API')).toBeInTheDocument()
      expect(screen.getByText('RecallRadar, DrugSignal, Sources, Audit History')).toBeInTheDocument()
    })
  })

  it('renders an error message when status cannot be loaded', async () => {
    vi.mocked(getSystemStatus).mockRejectedValue(new Error('network error'))

    render(<SystemStatusPage />)

    await waitFor(() => {
      expect(
        screen.getByText('Unable to load system status. Please check the backend deployment.'),
      ).toBeInTheDocument()
    })
  })
})
