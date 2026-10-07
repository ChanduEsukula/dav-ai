import { useState, type ComponentProps } from 'react'
import PharmacySafetyPage from './PharmacySafetyPage'
import StoredDrugCatalog from './StoredDrugCatalog'

export default function PharmacyCatalogPage(props: ComponentProps<typeof PharmacySafetyPage>) {
  const [live, setLive] = useState(() => new URLSearchParams(window.location.search).get('pharmacy_mode') === 'live')
  return <><div className="stored-mode"><button onClick={() => {
    const next = !live
    const url = new URL(window.location.href)
    if (next) url.searchParams.set('pharmacy_mode', 'live')
    else url.searchParams.delete('pharmacy_mode')
    window.history.replaceState(null, '', url)
    props.setAssistantContext?.(null)
    setLive(next)
  }}>{live ? 'Open stored drug catalog' : 'Open existing live pharmacy tools'}</button></div>
    {live ? <PharmacySafetyPage {...props} /> : <StoredDrugCatalog initialQuery={props.initialQuery} />}</>
}
