export type ProductScanImageQualityWarningCode =
  | 'too-small'
  | 'too-dark'
  | 'low-contrast'
  | 'file-too-large'

export type ProductScanImageQualityWarning = {
  code: ProductScanImageQualityWarningCode
  message: string
}

export type ProductScanImageQualityResult = {
  width: number
  height: number
  fileSizeBytes: number
  brightness: number
  contrast: number
  warnings: ProductScanImageQualityWarning[]
}

type ProductScanImageQualityOptions = {
  minWidth: number
  minHeight: number
  minBrightness: number
  minContrast: number
  maxFileSizeBytes: number
}

type ProductScanPixelInput = {
  width: number
  height: number
  fileSizeBytes: number
  data: Uint8ClampedArray
}

const DEFAULT_QUALITY_OPTIONS: ProductScanImageQualityOptions = {
  minWidth: 640,
  minHeight: 480,
  minBrightness: 68,
  minContrast: 24,
  maxFileSizeBytes: 12 * 1024 * 1024,
}

const SAMPLE_MAX_EDGE = 160

export const PRODUCTSCAN_IMAGE_QUALITY_MESSAGES = {
  tooSmall: 'Image may be too small; try a closer label photo.',
  tooDark: 'Image may be too dark for reliable OCR.',
  lowContrast: 'Image contrast may be too low for reliable OCR.',
  fileTooLarge: 'Image file is large; OCR may run slowly in your browser.',
}

function getLuminance(red: number, green: number, blue: number) {
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue
}

export function evaluateProductScanImageQuality(
  input: ProductScanPixelInput,
  options: ProductScanImageQualityOptions = DEFAULT_QUALITY_OPTIONS,
): ProductScanImageQualityResult {
  const warnings: ProductScanImageQualityWarning[] = []
  let sampleCount = 0
  let luminanceSum = 0
  let luminanceSquaredSum = 0

  for (let index = 0; index < input.data.length; index += 4) {
    const alpha = input.data[index + 3]
    if (alpha === 0) continue

    const luminance = getLuminance(
      input.data[index],
      input.data[index + 1],
      input.data[index + 2],
    )
    sampleCount += 1
    luminanceSum += luminance
    luminanceSquaredSum += luminance * luminance
  }

  const brightness = sampleCount > 0 ? luminanceSum / sampleCount : 0
  const variance =
    sampleCount > 0 ? luminanceSquaredSum / sampleCount - brightness * brightness : 0
  const contrast = Math.sqrt(Math.max(0, variance))

  if (input.width < options.minWidth || input.height < options.minHeight) {
    warnings.push({
      code: 'too-small',
      message: PRODUCTSCAN_IMAGE_QUALITY_MESSAGES.tooSmall,
    })
  }

  if (brightness < options.minBrightness) {
    warnings.push({
      code: 'too-dark',
      message: PRODUCTSCAN_IMAGE_QUALITY_MESSAGES.tooDark,
    })
  }

  if (contrast < options.minContrast) {
    warnings.push({
      code: 'low-contrast',
      message: PRODUCTSCAN_IMAGE_QUALITY_MESSAGES.lowContrast,
    })
  }

  if (input.fileSizeBytes > options.maxFileSizeBytes) {
    warnings.push({
      code: 'file-too-large',
      message: PRODUCTSCAN_IMAGE_QUALITY_MESSAGES.fileTooLarge,
    })
  }

  return {
    width: input.width,
    height: input.height,
    fileSizeBytes: input.fileSizeBytes,
    brightness,
    contrast,
    warnings,
  }
}

function loadImageFromFile(imageFile: File) {
  return new Promise<HTMLImageElement>((resolve, reject) => {
    const imageUrl = URL.createObjectURL(imageFile)
    const image = new Image()

    image.onload = () => {
      URL.revokeObjectURL(imageUrl)
      resolve(image)
    }

    image.onerror = () => {
      URL.revokeObjectURL(imageUrl)
      reject(new Error('ProductScan image could not be loaded.'))
    }

    image.src = imageUrl
  })
}

export async function analyzeProductScanImageQuality(
  imageFile: File,
): Promise<ProductScanImageQualityResult> {
  const image = await loadImageFromFile(imageFile)
  const width = image.naturalWidth || image.width
  const height = image.naturalHeight || image.height

  if (!width || !height) {
    throw new Error('ProductScan image has no readable dimensions.')
  }

  const scale = Math.min(1, SAMPLE_MAX_EDGE / Math.max(width, height))
  const sampleWidth = Math.max(1, Math.round(width * scale))
  const sampleHeight = Math.max(1, Math.round(height * scale))
  const canvas = document.createElement('canvas')
  canvas.width = sampleWidth
  canvas.height = sampleHeight

  const context = canvas.getContext('2d', { willReadFrequently: true })
  if (!context) {
    throw new Error('ProductScan image quality check could not read canvas data.')
  }

  context.drawImage(image, 0, 0, sampleWidth, sampleHeight)
  const imageData = context.getImageData(0, 0, sampleWidth, sampleHeight)

  return evaluateProductScanImageQuality({
    width,
    height,
    fileSizeBytes: imageFile.size,
    data: imageData.data,
  })
}
