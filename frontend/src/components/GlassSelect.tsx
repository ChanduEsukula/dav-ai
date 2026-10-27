import { useId, useState } from 'react'
import * as Select from '@radix-ui/react-select'
import type { ExperienceMode } from './experienceState'
import './glass-select.css'

type Option = { value: string; label: string }

/** Radix owns selection, typeahead, focus restoration and dismiss interactions. */
export default function GlassSelect({ label, value, options, onChange, mode }: {
  label: string; value: string; options: Option[]; onChange: (value: string) => void; mode: ExperienceMode
}) {
  const id = useId()
  const [topInset, setTopInset] = useState(160)
  // Index keys allow the existing empty-string "all" value without a sentinel collision.
  const selected = options.findIndex(option => option.value === value)
  return <div className="glass-select-field"><span id={`${id}-label`} className="glass-select-label">{label}</span>
    <Select.Root value={selected < 0 ? undefined : String(selected)} onValueChange={key => onChange(options[Number(key)].value)} onOpenChange={open => {
      if (open) setTopInset(parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--navigation-clearance')) || 160)
    }}>
      <Select.Trigger className="glass-select-trigger" aria-labelledby={`${id}-label`}><Select.Value /><Select.Icon aria-hidden="true"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="m4 6 4 4 4-4" /></svg></Select.Icon></Select.Trigger>
      <Select.Portal><Select.Content className="glass-select-menu" data-mode={mode} position="popper" sideOffset={8} align="start" collisionPadding={{ top: topInset, bottom: 12, left: 12, right: 12 }}>
        <Select.ScrollUpButton className="glass-select-scroll" aria-label="Scroll options up">⌃</Select.ScrollUpButton>
        <Select.Viewport className="glass-select-viewport">{options.map((option, index) => <Select.Item className="glass-select-option" value={String(index)} key={option.value} textValue={option.label} title={option.value || undefined}>
          <Select.ItemText>{option.label}</Select.ItemText><Select.ItemIndicator className="glass-select-check"><svg width="17" height="17" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="m4 10 4 4 8-8" /></svg></Select.ItemIndicator>
        </Select.Item>)}</Select.Viewport>
        <Select.ScrollDownButton className="glass-select-scroll" aria-label="Scroll options down">⌄</Select.ScrollDownButton>
      </Select.Content></Select.Portal>
    </Select.Root>
  </div>
}
