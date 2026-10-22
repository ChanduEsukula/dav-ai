import base from './playwright.config'
import { defineConfig } from '@playwright/test'
export default defineConfig({ ...base, testIgnore: [], testMatch: 'pharma-offline.spec.ts' })
