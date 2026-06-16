import { useState, type FormEvent } from 'react'

import { searchDocs, type StaticDocsSearchResponse } from '../api/docs'

const HELP_DOCS_MAX_RESULTS = 8

const DEFAULT_LIMITATIONS = [
  'Documentation search only. Results are snippets from Dav AI repository documentation.',
  'Not medical advice.',
  'Not a safety determination for any product, drug, food, supplement, or cosmetic.',
  'Verify official FDA/USDA sources before acting.',
]

function normalizeDocsQuery(value: string) {
  return value.trim().replace(/\s+/g, ' ')
}

function formatLineRange(lineStart: number, lineEnd: number) {
  if (lineStart === lineEnd) {
    return `Line ${lineStart}`
  }

  return `Lines ${lineStart}-${lineEnd}`
}

function HelpDocsSearch() {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState<StaticDocsSearchResponse | null>(null)
  const [validationMessage, setValidationMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const limitations =
    response?.limitations && response.limitations.length > 0
      ? response.limitations
      : DEFAULT_LIMITATIONS

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const cleanQuery = normalizeDocsQuery(query)
    if (cleanQuery.length < 2) {
      setResponse(null)
      setErrorMessage('')
      setValidationMessage(
        'Enter at least two non-whitespace characters to search documentation.',
      )
      return
    }

    setIsLoading(true)
    setErrorMessage('')
    setValidationMessage('')

    try {
      const docsResponse = await searchDocs(cleanQuery, HELP_DOCS_MAX_RESULTS)
      setResponse(docsResponse)
    } catch {
      setResponse(null)
      setErrorMessage(
        'Unable to search documentation. Check backend availability and try again.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <section className="help-docs-search reveal" aria-labelledby="help-docs-search-title">
      <div className="help-docs-search__header">
        <p className="eyebrow">Documentation search</p>
        <h3 id="help-docs-search-title">Find cited snippets from Dav AI docs.</h3>
        <p>
          Search the approved Markdown documentation set. Results are source snippets
          only, not generated answers or safety advice.
        </p>
      </div>

      <form className="help-docs-search__form" onSubmit={handleSubmit}>
        <label htmlFor="help-docs-search-input">Search Dav AI docs</label>
        <div className="help-docs-search__controls">
          <input
            id="help-docs-search-input"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Try ProductScan, RAG, FDA source, or audit"
            aria-describedby="help-docs-search-helper help-docs-search-limitations"
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Searching...' : 'Search docs'}
          </button>
        </div>
        <p id="help-docs-search-helper" className="help-docs-search__helper">
          {validationMessage ||
            'Use at least two characters. Dav AI returns matching documentation snippets with citations.'}
        </p>
      </form>

      <aside
        className="help-docs-search__limitations"
        aria-labelledby="help-docs-search-limitations-title"
      >
        <h4 id="help-docs-search-limitations-title">Search boundaries</h4>
        <ul id="help-docs-search-limitations">
          {limitations.map((limitation) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
      </aside>

      {isLoading && (
        <p className="help-docs-search__state" role="status">
          Searching documentation...
        </p>
      )}

      {errorMessage && (
        <p className="help-docs-search__state help-docs-search__state--error" role="alert">
          {errorMessage}
        </p>
      )}

      {response && !isLoading && !errorMessage && response.results.length === 0 && (
        <p className="help-docs-search__state" role="status">
          No matching documentation snippets found.
        </p>
      )}

      {response && !isLoading && !errorMessage && response.results.length > 0 && (
        <div
          className="help-docs-search__results"
          role="list"
          aria-label={`Documentation results for ${response.query}`}
        >
          {response.results.map((result, index) => (
            <article
              className="help-docs-search__result"
              role="listitem"
              key={`${result.source_path}-${result.line_start}-${index}`}
            >
              <div className="help-docs-search__result-heading">
                <h4>{result.title}</h4>
                <span>{formatLineRange(result.line_start, result.line_end)}</span>
              </div>
              <p className="help-docs-search__source">{result.source_path}</p>
              {result.section_heading && (
                <p className="help-docs-search__section">
                  Section: {result.section_heading}
                </p>
              )}
              <p className="help-docs-search__snippet">{result.snippet}</p>
              {result.matched_terms.length > 0 && (
                <ul className="help-docs-search__terms" aria-label="Matched terms">
                  {result.matched_terms.map((term) => (
                    <li key={term}>{term}</li>
                  ))}
                </ul>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

export default HelpDocsSearch
