import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import GlassSelect from './GlassSelect'

for (const mode of ['everyday','research_pro'] as const) {
  it(`keeps empty and stored values distinct, selects and restores focus in ${mode}`, async () => {
    const change=vi.fn()
    render(<GlassSelect mode={mode} label="Strength" value="" options={[{value:'',label:'All strengths'},{value:'.25 mg/1',label:'0.25 mg / 1'}]} onChange={change} />)
    const trigger=screen.getByRole('combobox',{name:'Strength'})
    expect(trigger).toHaveAttribute('aria-expanded','false')
    trigger.focus()
    fireEvent.keyDown(trigger,{key:'ArrowDown'})
    const option=await screen.findByRole('option',{name:'0.25 mg / 1'})
    expect(screen.getByRole('option',{name:'All strengths'})).toHaveAttribute('aria-selected','true')
    expect(screen.getByRole('listbox')).toHaveAttribute('data-mode',mode)
    fireEvent.click(option)
    expect(change).toHaveBeenCalledWith('.25 mg/1')
    await waitFor(()=>expect(trigger).toHaveFocus())
  })
}

it('supports Escape without changing the stored value',async()=>{
 const change=vi.fn()
 render(<GlassSelect mode="everyday" label="Dosage form" value="TABLET" options={[{value:'',label:'All forms'},{value:'TABLET',label:'TABLET'}]} onChange={change} />)
 const trigger=screen.getByRole('combobox',{name:'Dosage form'})
 trigger.focus();fireEvent.keyDown(trigger,{key:'Enter'})
 await screen.findByRole('listbox')
 fireEvent.keyDown(document.activeElement!,{key:'Escape'})
 await waitFor(()=>expect(trigger).toHaveAttribute('aria-expanded','false'))
 expect(change).not.toHaveBeenCalled()
})
