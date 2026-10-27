import { useEffect, useState } from 'react'
import { isAxiosError } from 'axios'
import { getDataInventory, validateDataInventory, type DataInventory as Inventory } from '../api/drugCatalog'
import type { ExperienceMode } from '../components/experienceState'
import { EvidenceIcon, type EvidenceKind } from './EvidenceIcon'

export default function DataInventory({ mode }: { mode: ExperienceMode }) {
  const [value, setValue] = useState<Inventory | null>(null)
  const [failed, setFailed] = useState(false)
  const [retry, setRetry] = useState(0)
  const [snapshot, setSnapshot] = useState(false)
  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      try {
        const result = await getDataInventory(controller.signal)
        if (!controller.signal.aborted) { setValue(result); setFailed(false); setSnapshot(false) }
      } catch (error) {
        if (controller.signal.aborted) return
        // An old/missing local API can use generated metadata, never clinical records.
        // Do not fall back on authorization, integrity or response-validation failures.
        if (import.meta.env.DEV && isAxiosError(error) && (!error.response || error.response.status === 404)) {
          try {
            const saved = await import('../generated/dev-inventory.json')
            const result = validateDataInventory(saved.default as unknown as Inventory)
            if (!controller.signal.aborted) { setValue(result); setSnapshot(true); setFailed(false) }
            console.info('[Dav AI inventory] Using validated development snapshot metadata; local inventory endpoint unavailable.')
            return
          } catch { /* Use the nonnumeric source descriptions below. */ }
        }
        console.warn('[Dav AI inventory] Metrics could not be loaded; source descriptions remain available.')
        if (!controller.signal.aborted) { setValue(null); setFailed(true) }
      }
    }
    void load()
    return () => controller.abort()
  }, [retry])
  const cards: { key: string; kind: EvidenceKind; title: string; description: string }[] = [
    { key: 'labels', kind: 'labels', title: 'FDA drug labeling', description: 'Stored label documents, including retained context. Exact-product admission still applies.' },
    { key: 'recalls', kind: 'recalls', title: 'Historical recalls', description: 'Historical records in the dataset, including records without consumer product links.' },
    { key: 'analytics', kind: 'faers', title: 'FAERS reporting', description: 'Ingredients with reporting analytics. Associations do not establish causation or personal risk.' },
  ]
  return <section className="immersive-section data-inventory" id="explore-data" aria-labelledby="inventory-title" aria-busy={!value && !failed}>
    <div className="section-heading-row"><div><p className="immersive-eyebrow">Evidence at a glance</p><h2 id="inventory-title">Inside Dav AI</h2></div><p>Explore the scope of the stored pharmaceutical evidence powering the platform.</p></div>
    <div className="inventory-grid">{cards.map(card => {
      const metric = value?.metrics.find(item => item.key === card.key)
      return <article key={card.key} className="glass-card inventory-metric"><span className="immersive-icon"><EvidenceIcon kind={card.kind} /></span><h3>{card.title}</h3>
        {metric && <><strong className="inventory-value">{metric.value.toLocaleString()}</strong><span>{card.key === 'analytics' ? 'ingredients with analytics' : card.key === 'labels' ? 'stored label documents' : 'stored recall records'}</span><small>{metric.window}</small></>}
        <p>{card.description}</p>{metric && <details><summary>What this counts</summary><p>{metric.definition}</p>{mode === 'research_pro' && <code>{metric.source}</code>}</details>}
      </article>
    })}</div>
    {value ? <><div className="inventory-coverage"><span className="coverage-seal" aria-hidden="true">◷</span><div><strong>Frozen-release coverage</strong><p>Reporting analysis: {value.release.window_start} to {value.release.window_end}. Historical snapshots, not a live safety feed.</p><p>Built {value.release.build_time_utc.slice(0, 10)}{snapshot ? ' · Verified development snapshot metadata' : ''} · Publication not authorized</p></div></div>
      <details className="inventory-provenance"><summary>Source dates, counting methods and release details</summary><p>Release {value.release.release_id}</p><ul>{value.release.sources.map(source => <li key={source.source_id}>{source.source_name} · export {source.export_date ?? 'not recorded'} · observed {source.observed_at ?? 'not recorded'}</li>)}</ul>{mode === 'research_pro' && <ul>{value.metrics.filter(metric => !cards.some(card => card.key === metric.key)).map(metric => <li key={metric.key}>{metric.label}: {metric.value.toLocaleString()} · {metric.definition}<br /><code>{metric.source}</code></li>)}</ul>}<ul>{value.limitations.map(item => <li key={item}>{item}</li>)}</ul></details>
    </> : <div className="inventory-status" role={failed ? 'alert' : undefined}><p>{failed ? 'Dataset metrics could not be loaded. You can still explore the source types and evidence tools above.' : 'Loading the verified dataset overview…'}</p>{failed && <button onClick={() => { setFailed(false); setRetry(count => count + 1) }}>Retry dataset metrics</button>}</div>}
  </section>
}
