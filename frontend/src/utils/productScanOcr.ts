import { recognize } from 'tesseract.js'

export async function runProductScanOcr(image: File): Promise<string> {
  const result = await recognize(image, 'eng')
  return result.data.text.trim()
}
