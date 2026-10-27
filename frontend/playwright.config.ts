import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testIgnore: 'pharma-offline.spec.ts',
  timeout: 60_000,
  use: { baseURL: 'http://127.0.0.1:15173', trace: 'on-first-retry' },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 15173 --strictPort',
    url: 'http://127.0.0.1:15173',
    env: { VITE_API_BASE_URL: process.env.PHARMA_API_URL || 'http://127.0.0.1:18000' },
    reuseExistingServer: !process.env.CI,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
