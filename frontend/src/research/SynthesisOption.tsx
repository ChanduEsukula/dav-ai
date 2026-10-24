export function SynthesisOption({ enabled = false, onChange, disabled }: {
  enabled?: boolean; onChange?: (enabled: boolean) => void; disabled: boolean
}) {
  if (!onChange) return null
  return <div className="pro-form-group">
    <label><input type="checkbox" checked={enabled} disabled={disabled}
      onChange={event => onChange(event.target.checked)} /> Include a grounded AI answer (local Ollama)</label>
    <p>Optional AI-selected label statements with citations. Unsupported questions retain the structured evidence.</p>
  </div>
}
