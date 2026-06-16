import { describe, expect, it } from 'vitest'

import {
  PRODUCTSCAN_IMAGE_QUALITY_MESSAGES,
  evaluateProductScanImageQuality,
} from './productScanImageQuality'

function createSolidPixels(width: number, height: number, value: number) {
  const data = new Uint8ClampedArray(width * height * 4)

  for (let index = 0; index < data.length; index += 4) {
    data[index] = value
    data[index + 1] = value
    data[index + 2] = value
    data[index + 3] = 255
  }

  return data
}

function createCheckerPixels(width: number, height: number) {
  const data = new Uint8ClampedArray(width * height * 4)

  for (let pixel = 0; pixel < width * height; pixel += 1) {
    const value = pixel % 2 === 0 ? 24 : 232
    const index = pixel * 4
    data[index] = value
    data[index + 1] = value
    data[index + 2] = value
    data[index + 3] = 255
  }

  return data
}

describe('evaluateProductScanImageQuality', () => {
  it('warns when an image is too small for reliable OCR', () => {
    const result = evaluateProductScanImageQuality({
      width: 320,
      height: 240,
      fileSizeBytes: 120_000,
      data: createCheckerPixels(8, 8),
    })

    expect(result.warnings).toEqual(
      expect.arrayContaining([
        {
          code: 'too-small',
          message: PRODUCTSCAN_IMAGE_QUALITY_MESSAGES.tooSmall,
        },
      ]),
    )
  })

  it('warns when an image is too dark for reliable OCR', () => {
    const result = evaluateProductScanImageQuality({
      width: 1200,
      height: 900,
      fileSizeBytes: 120_000,
      data: createSolidPixels(8, 8, 18),
    })

    expect(result.brightness).toBeLessThan(68)
    expect(result.warnings).toEqual(
      expect.arrayContaining([
        {
          code: 'too-dark',
          message: PRODUCTSCAN_IMAGE_QUALITY_MESSAGES.tooDark,
        },
      ]),
    )
  })

  it('warns when image contrast is low', () => {
    const result = evaluateProductScanImageQuality({
      width: 1200,
      height: 900,
      fileSizeBytes: 120_000,
      data: createSolidPixels(8, 8, 140),
    })

    expect(result.contrast).toBeLessThan(24)
    expect(result.warnings).toEqual(
      expect.arrayContaining([
        {
          code: 'low-contrast',
          message: PRODUCTSCAN_IMAGE_QUALITY_MESSAGES.lowContrast,
        },
      ]),
    )
  })

  it('warns when image file size is large enough to slow browser OCR', () => {
    const result = evaluateProductScanImageQuality({
      width: 1200,
      height: 900,
      fileSizeBytes: 13 * 1024 * 1024,
      data: createCheckerPixels(8, 8),
    })

    expect(result.warnings).toEqual(
      expect.arrayContaining([
        {
          code: 'file-too-large',
          message: PRODUCTSCAN_IMAGE_QUALITY_MESSAGES.fileTooLarge,
        },
      ]),
    )
  })

  it('returns no warnings for a readable, bright, high-contrast image sample', () => {
    const result = evaluateProductScanImageQuality({
      width: 1200,
      height: 900,
      fileSizeBytes: 120_000,
      data: createCheckerPixels(8, 8),
    })

    expect(result.warnings).toEqual([])
    expect(result.brightness).toBeGreaterThan(68)
    expect(result.contrast).toBeGreaterThan(24)
  })
})
