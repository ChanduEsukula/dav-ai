import '@testing-library/jest-dom'
import { vi } from 'vitest'

Object.defineProperty(window, 'scrollTo', {
  value: vi.fn(),
  writable: true,
})

// Polyfill window.localStorage for Node 24 / jsdom environment
let store: Record<string, string> = {}
const storageMock = {
  getItem: (key: string) => store[key] ?? null,
  setItem: (key: string, value: string) => {
    store[key] = value.toString()
  },
  removeItem: (key: string) => {
    delete store[key]
  },
  clear: () => {
    store = {}
  },
  key: (idx: number) => Object.keys(store)[idx] ?? null,
  get length() {
    return Object.keys(store).length
  },
}

Object.defineProperty(window, 'localStorage', {
  value: storageMock,
  writable: true,
})
