import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from 'react'
import type { ActivePage } from '../types/navigation'
import {
  extractProductScanCandidates,
  type ProductScanCandidate,
} from '../utils/productScanExtraction'
import {
  analyzeProductScanImageQuality,
  type ProductScanImageQualityResult,
} from '../utils/productScanImageQuality'
import { runProductScanOcr } from '../utils/productScanOcr'
import { normalizeSearchTerm } from '../utils/queryNormalization'

type ProductScanPageProps = {
  goToPage: (page: ActivePage, query?: string, rawQuery?: string) => void
}

type ProductScanWorkflow = 'pharmacy' | 'food' | 'cosmetic'
type ProductScanOcrStatus = 'idle' | 'running' | 'completed' | 'failed'
type ProductScanImageQualityStatus = 'idle' | 'checking' | 'checked' | 'failed'

const OCR_REVIEW_WARNING = 'OCR can misread labels. Review extracted text before continuing.'

const workflowOptions: Array<{
  id: ProductScanWorkflow
  label: string
  page: Extract<ActivePage, 'pharmacy-safety' | 'food-safety' | 'cosmetic-safety'>
}> = [
  { id: 'pharmacy', label: 'Pharmacy Safety', page: 'pharmacy-safety' },
  { id: 'food', label: 'Food Safety', page: 'food-safety' },
  { id: 'cosmetic', label: 'Cosmetic Safety', page: 'cosmetic-safety' },
]

function ProductScanCandidateCard({
  candidate,
  selected,
  onSelect,
}: {
  candidate: ProductScanCandidate
  selected: boolean
  onSelect: (candidate: ProductScanCandidate) => void
}) {
  return (
    <article className={selected ? 'productscan-candidate is-selected' : 'productscan-candidate'}>
      <div>
        <span>{candidate.label}</span>
        <strong>{candidate.value}</strong>
        <p>{candidate.detail}</p>
      </div>

      <button
        type="button"
        aria-pressed={selected}
        aria-label={`Use ${candidate.value} as search term`}
        onClick={() => onSelect(candidate)}
      >
        Use term
      </button>
    </article>
  )
}

function ProductScanPage({ goToPage }: ProductScanPageProps) {
  const [labelText, setLabelText] = useState('')
  const [confirmedQuery, setConfirmedQuery] = useState('')
  const [selectedCandidateId, setSelectedCandidateId] = useState('')
  const [workflow, setWorkflow] = useState<ProductScanWorkflow | ''>('')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreviewUrl, setImagePreviewUrl] = useState('')
  const [imageName, setImageName] = useState('')
  const [ocrStatus, setOcrStatus] = useState<ProductScanOcrStatus>('idle')
  const [ocrMessage, setOcrMessage] = useState(
    'OCR not started. Upload a label image to enable browser-side text extraction.',
  )
  const [imageQualityStatus, setImageQualityStatus] =
    useState<ProductScanImageQualityStatus>('idle')
  const [imageQualityResult, setImageQualityResult] =
    useState<ProductScanImageQualityResult | null>(null)
  const candidates = useMemo(() => extractProductScanCandidates(labelText), [labelText])
  const cleanConfirmedQuery = normalizeSearchTerm(confirmedQuery)
  const imageQualityWarnings = imageQualityResult?.warnings ?? []

  useEffect(() => {
    return () => {
      if (imagePreviewUrl) {
        URL.revokeObjectURL(imagePreviewUrl)
      }
    }
  }, [imagePreviewUrl])

  useEffect(() => {
    if (!imageFile) {
      return
    }

    let isCurrentImage = true

    analyzeProductScanImageQuality(imageFile)
      .then((result) => {
        if (!isCurrentImage) return

        setImageQualityResult(result)
        setImageQualityStatus('checked')
      })
      .catch(() => {
        if (!isCurrentImage) return

        setImageQualityResult(null)
        setImageQualityStatus('failed')
        setOcrStatus('failed')
        setOcrMessage('Image could not be loaded for OCR. You can still paste or type label text manually.')
      })

    return () => {
      isCurrentImage = false
    }
  }, [imageFile])

  function handleImageUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return

    setImageName(file.name)
    setImageFile(file)
    setImagePreviewUrl(URL.createObjectURL(file))
    setOcrStatus('idle')
    setOcrMessage('OCR not started. Select Extract text from image when you are ready.')
    setImageQualityStatus('checking')
    setImageQualityResult(null)
  }

  async function handleExtractText() {
    if (!imageFile) return

    setOcrStatus('running')
    setOcrMessage('OCR running. Extracting visible label text in your browser...')

    try {
      const extractedText = await runProductScanOcr(imageFile)
      const cleanExtractedText = normalizeSearchTerm(extractedText)

      if (!cleanExtractedText) {
        throw new Error('No OCR text returned.')
      }

      setLabelText(extractedText)
      setSelectedCandidateId('')
      setConfirmedQuery('')
      setOcrStatus('completed')
      setOcrMessage('OCR completed. Review and edit the extracted text before continuing.')
    } catch {
      setOcrStatus('failed')
      setOcrMessage('OCR failed. You can still paste or type label text manually.')
    }
  }

  function handleCandidateSelect(candidate: ProductScanCandidate) {
    setSelectedCandidateId(candidate.id)
    setConfirmedQuery(candidate.value)
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!workflow || !cleanConfirmedQuery) return

    const selectedWorkflow = workflowOptions.find((option) => option.id === workflow)
    if (!selectedWorkflow) return

    goToPage(selectedWorkflow.page, cleanConfirmedQuery)
  }

  return (
    <section className="productscan-page" aria-labelledby="productscan-title">
      <header className="productscan-header">
        <p className="eyebrow">Experimental ProductScan</p>
        <h1 id="productscan-title">Review label text before searching public records.</h1>
        <p>
          ProductScan is an input-assistance scaffold. It helps organize visible label text into
          candidate terms, then sends your confirmed term to an existing Dav AI workflow.
        </p>
      </header>

      <div className="productscan-shell">
        <section className="productscan-panel productscan-upload-panel">
          <div className="productscan-panel__heading">
            <p className="eyebrow">Local preview</p>
            <h2>Upload a product-label image</h2>
            <p>
              The image preview is created in your browser for review. This scaffold does not
              upload or store image files.
            </p>
          </div>

          <label className="productscan-file-drop" htmlFor="productscan-image">
            <input
              id="productscan-image"
              type="file"
              accept="image/*"
              aria-label="Upload product label image"
              onChange={handleImageUpload}
            />
            <span>Choose label image</span>
            <small>PNG, JPG, or other browser-supported image files</small>
          </label>

          {imagePreviewUrl ? (
            <figure className="productscan-preview">
              <img src={imagePreviewUrl} alt={`Uploaded label preview for ${imageName}`} />
              <figcaption>{imageName}</figcaption>
            </figure>
          ) : (
            <div className="productscan-preview-empty">
              <strong>No image selected</strong>
              <span>Upload is optional. You can paste visible label text below.</span>
            </div>
          )}

          {imageFile && (
            <section
              className="productscan-image-quality"
              aria-labelledby="productscan-image-quality-title"
            >
              <div className="productscan-image-quality__heading">
                <h3 id="productscan-image-quality-title">Image OCR readiness</h3>
                {imageQualityStatus === 'checking' && <span>Checking image...</span>}
                {imageQualityStatus === 'checked' && imageQualityWarnings.length === 0 && (
                  <span>No quality warnings</span>
                )}
                {imageQualityStatus === 'checked' && imageQualityWarnings.length > 0 && (
                  <span>{imageQualityWarnings.length} warning(s)</span>
                )}
                {imageQualityStatus === 'failed' && <span>Image load failed</span>}
              </div>

              {imageQualityStatus === 'failed' ? (
                <p className="productscan-image-quality__error" role="alert">
                  Image could not be loaded for OCR. Choose another image or paste label text
                  manually.
                </p>
              ) : (
                <ul>
                  {imageQualityWarnings.map((warning) => (
                    <li key={warning.code}>{warning.message}</li>
                  ))}
                  <li>{OCR_REVIEW_WARNING}</li>
                </ul>
              )}
            </section>
          )}

          {imageFile && (
            <button
              className="productscan-ocr-button"
              type="button"
              disabled={ocrStatus === 'running' || imageQualityStatus === 'failed'}
              onClick={handleExtractText}
            >
              {ocrStatus === 'running' ? 'Extracting text...' : 'Extract text from image'}
            </button>
          )}

          <p
            className={`productscan-ocr-status productscan-ocr-status--${ocrStatus}`}
            role="status"
          >
            {ocrMessage}
          </p>
        </section>

        <form className="productscan-panel productscan-review-panel" onSubmit={handleSubmit}>
          <div className="productscan-panel__heading">
            <p className="eyebrow">Text review</p>
            <h2>Paste or review extracted label text</h2>
            <p>
              Browser-side OCR can populate this field from the uploaded image. OCR can misread
              labels. Review and edit the extracted text before continuing.
            </p>
          </div>

          <label className="productscan-text-field" htmlFor="productscan-label-text">
            <span>Paste or review extracted label text</span>
            <textarea
              id="productscan-label-text"
              value={labelText}
              rows={9}
              placeholder="Example: Product Name: Mango Coconut Water&#10;UPC: 012345678905&#10;Lot A1B2C3&#10;Best by 05/2026"
              onChange={(event) => setLabelText(event.target.value)}
            />
          </label>

          <section className="productscan-candidates" aria-labelledby="productscan-candidates">
            <div className="productscan-candidates__heading">
              <h3 id="productscan-candidates">Review candidate terms</h3>
              <span>{candidates.length} found</span>
            </div>

            {candidates.length > 0 ? (
              <div className="productscan-candidate-grid">
                {candidates.map((candidate) => (
                  <ProductScanCandidateCard
                    key={candidate.id}
                    candidate={candidate}
                    selected={selectedCandidateId === candidate.id}
                    onSelect={handleCandidateSelect}
                  />
                ))}
              </div>
            ) : (
              <p className="productscan-empty-candidates">
                No candidate terms yet. Paste visible label text or type the term you want to
                search.
              </p>
            )}
          </section>

          <label className="productscan-confirm-field" htmlFor="productscan-confirmed-query">
            <span>Confirmed search term</span>
            <input
              id="productscan-confirmed-query"
              value={confirmedQuery}
              placeholder="Choose a candidate or type a search term"
              onChange={(event) => {
                setConfirmedQuery(event.target.value)
                setSelectedCandidateId('')
              }}
            />
          </label>

          <fieldset className="productscan-workflows">
            <legend>Choose where to search</legend>
            {workflowOptions.map((option) => (
              <label key={option.id}>
                <input
                  type="radio"
                  name="productscan-workflow"
                  value={option.id}
                  checked={workflow === option.id}
                  onChange={() => setWorkflow(option.id)}
                />
                <span>{option.label}</span>
              </label>
            ))}
          </fieldset>

          <button
            className="productscan-submit"
            type="submit"
            disabled={!workflow || !cleanConfirmedQuery}
          >
            Open selected workflow
          </button>
        </form>
      </div>

      <aside className="productscan-limitations" aria-labelledby="productscan-limitations">
        <h2 id="productscan-limitations">ProductScan limitations</h2>
        <ul>
          <li>OCR or pasted text can be wrong. Review the exact label before searching.</li>
          <li>OCR can misread labels. Review and edit the extracted text before continuing.</li>
          <li>Verify product name, package, lot, date, and official source records yourself.</li>
          <li>ProductScan does not determine whether a product is safe or unsafe.</li>
          <li>No image is stored by Dav AI; OCR runs in the browser for this scaffold.</li>
        </ul>
      </aside>
    </section>
  )
}

export default ProductScanPage
