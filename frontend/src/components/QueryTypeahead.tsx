import { useMemo, useRef, useState } from 'react'
import {
  getQuerySuggestions,
  type QuerySuggestion,
  type SafetyQueryArea,
} from '../utils/queryNormalization'

type QueryTypeaheadProps = {
  id: string
  value: string
  onChange: (value: string) => void
  area?: SafetyQueryArea
  placeholder: string
  disabled?: boolean
  ariaDescribedBy?: string
  showWorkflow?: boolean
}

function QueryTypeahead({
  id,
  value,
  onChange,
  area,
  placeholder,
  disabled = false,
  ariaDescribedBy,
  showWorkflow = false,
}: QueryTypeaheadProps) {
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const wrapperRef = useRef<HTMLDivElement>(null)
  const suggestions = useMemo(() => getQuerySuggestions(value, area), [area, value])
  const listboxId = `${id}-suggestions`
  const isOpen = open && suggestions.length > 0

  function selectSuggestion(suggestion: QuerySuggestion) {
    onChange(suggestion.query)
    setOpen(false)
    setActiveIndex(-1)
  }

  return (
    <div
      className="query-typeahead"
      ref={wrapperRef}
      onBlur={(event) => {
        if (!wrapperRef.current?.contains(event.relatedTarget)) {
          setOpen(false)
          setActiveIndex(-1)
        }
      }}
    >
      <input
        id={id}
        value={value}
        disabled={disabled}
        placeholder={placeholder}
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={isOpen}
        aria-controls={isOpen ? listboxId : undefined}
        aria-activedescendant={
          isOpen && activeIndex >= 0 ? `${listboxId}-${activeIndex}` : undefined
        }
        aria-describedby={ariaDescribedBy}
        autoComplete="off"
        onFocus={() => setOpen(true)}
        onChange={(event) => {
          onChange(event.target.value)
          setOpen(true)
          setActiveIndex(-1)
        }}
        onKeyDown={(event) => {
          if (event.key === 'Escape') {
            setOpen(false)
            setActiveIndex(-1)
            return
          }

          if (event.key === 'ArrowDown' && suggestions.length > 0) {
            event.preventDefault()
            setOpen(true)
            setActiveIndex((current) =>
              current < suggestions.length - 1 ? current + 1 : 0,
            )
            return
          }

          if (event.key === 'ArrowUp' && suggestions.length > 0) {
            event.preventDefault()
            setOpen(true)
            setActiveIndex((current) =>
              current > 0 ? current - 1 : suggestions.length - 1,
            )
            return
          }

          if (event.key === 'Enter') {
            if (isOpen && activeIndex >= 0) {
              event.preventDefault()
              selectSuggestion(suggestions[activeIndex])
            } else {
              setOpen(false)
            }
          }
        }}
      />

      {isOpen && (
        <div className="query-typeahead__menu" id={listboxId} role="listbox">
          {suggestions.map((suggestion, index) => (
            <button
              key={`${suggestion.area}-${suggestion.query}`}
              id={`${listboxId}-${index}`}
              type="button"
              role="option"
              aria-label={
                showWorkflow
                  ? `${suggestion.query}, ${suggestion.workflowLabel}`
                  : suggestion.query
              }
              aria-selected={index === activeIndex}
              className={index === activeIndex ? 'is-active' : ''}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => selectSuggestion(suggestion)}
            >
              <span>{suggestion.query}</span>
              {showWorkflow && <small>{suggestion.workflowLabel}</small>}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default QueryTypeahead
