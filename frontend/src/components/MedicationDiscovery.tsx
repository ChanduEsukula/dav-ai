import { Fragment, useState } from 'react'
import type { CatalogDrug, MedicationOverview } from '../api/drugCatalog'
import type { ExperienceMode } from './experienceState'
import { EvidencePanel, EvidenceBar } from './EvidencePanel'
import { isOfficialFdaUrl } from '../utils/sourceUrl'
import GlassSelect from './GlassSelect'

function SourceLink({ url }: { url: string | null | undefined }) {
  return isOfficialFdaUrl(url) ? <a href={url!} target="_blank" rel="noopener noreferrer">Original FDA source ↗</a> : <span>Official source link unavailable</span>
}

export function MedicationSummary({ value, mode }: { value: MedicationOverview; mode: ExperienceMode }) {
  const pro = mode === 'research_pro'
  const labelSummary = <><p className="summary-number">{value.labels.distinct_admitted_records}<small>distinct admitted label documents</small></p><p>{value.labels.products_with_labels} of {value.matched_product_count} matching products have admitted labels.</p><p className="summary-limit">Not a warning or safety score. Missing labels do not mean no warnings exist.</p></>
  const recallSummary = <><p className="summary-number">{value.recalls.distinct_linked_records}<small>distinct linked historical records</small></p>
    {value.recalls.records.slice(0, 2).map(row => <p className="recall-reason-preview" key={row.id}><strong>{row.reason_for_recall}</strong><small>{row.recall_number} · {row.recall_initiation_date ?? row.report_date ?? 'Date not recorded'}</small></p>)}
    <p className="summary-limit">Across these matching products only. Historical coverage is incomplete; package/lot applicability varies.</p></>
  const faersSummary = <>{value.ingredients.slice(0, 2).map(ingredient => <div key={ingredient.ingredient_id}>
    <p className="ingredient-scope"><strong>{ingredient.ingredient_name}</strong> · ingredient-level</p>
    {ingredient.report_count !== null ? <><p className="summary-associations">{ingredient.report_count.toLocaleString()} <small>stored ingredient-report associations</small></p>
      <p className="summary-window">{ingredient.window_start} → {ingredient.window_end}</p>
      {ingredient.reactions.slice(0, 2).map(row => <EvidenceBar key={row.rank} label={row.reaction} value={row.co_report_activity} max={Math.max(...ingredient.reactions.slice(0, 2).map(reaction => reaction.co_report_activity))} unit="reaction co-report activity" />)}</> : <p>Stored reporting analytics unavailable.</p>}
  </div>)}{value.ingredients.length > 2 && <p>Additional ingredient records in details.</p>}<p className="summary-limit">Bars show reaction co-report activity, relative within each ingredient. Not brand-specific patients, incidence or causation.</p></>
  return <section className="medication-discovery" aria-labelledby="medication-discovery-title">
    <div className="medication-discovery-heading"><div><p className="eyebrow">Medication discovery · not an exact-product confirmation</p><h2 id="medication-discovery-title">{value.query}<span>{[...new Set(value.products.flatMap(product => product.active_ingredients))].join(' · ')}</span></h2></div>
      <p>{value.matched_product_count} matching products · {value.formulations.length} stored formulation identifiers{value.truncated ? ' · bounded results' : ''}</p></div>
    <div className="evidence-panels medication-overview-panels" key={value.query}>
      <EvidencePanel kind="labels" title="FDA drug labeling" scope="Admitted exact-product links" summary={labelSummary}>
        <p>Documents are deduplicated by label_id only after consumer-admission checks. {value.labels.product_label_links} product-to-label links remain distinct.</p>
        <p>Select a formulation below to inspect original label sections and source versions.</p>
        {pro && <p>Release {value.release.release_id} · Export {value.release.label_export_date}</p>}
      </EvidencePanel>
      <EvidencePanel kind="recalls" title="Historical recalls" scope="Linked to matching products" summary={recallSummary}>
        {!value.recalls.records.length && <p>No linked records were returned for these matching products. This does not establish an absence of recalls.</p>}
        {value.recalls.records.map(row => <article className="record" key={row.id}><h3>{row.recall_number} · {row.classification ?? 'Unclassified'}</h3>
          <p><strong>Reason:</strong> {row.reason_for_recall}</p><p>{row.product_description}</p><p>Recalling firm: {row.recalling_firm ?? 'Not recorded'}</p>
          <p>Initiated {row.recall_initiation_date ?? 'Not recorded'} · Reported {row.report_date ?? 'Not recorded'} · Source-reported status: {row.reported_status ?? 'Not recorded'}</p>
          {row.product_links.map(link => <div className="recall-product-link" key={link.product_id}><p>NDC {link.product_ndcs.join(', ')} · Lot scope: {link.lot_scope} · {link.lot_information ?? 'Lot information not recorded'}</p>
            {pro && <p>{link.applicability_class} · {link.match_method} · {link.matched_value}</p>}</div>)}
          <SourceLink url={row.source_url} /></article>)}
        <p>Records are deduplicated by sealed recall ID, not FDA event ID. {value.recalls.product_recall_links} product links; do not sum links as events. No inference that all lots were affected.</p>
      </EvidencePanel>
      <EvidencePanel kind="faers" title="FAERS reporting" scope="Ingredients listed once" summary={faersSummary}>
        {value.ingredients.map(ingredient => <article className="record" key={ingredient.ingredient_id}><h3>{ingredient.ingredient_name}</h3><p>Coverage: {ingredient.coverage.state} · {ingredient.window_start ?? 'Unknown window'} → {ingredient.window_end ?? 'Unknown window'}</p>
          <p>Association unit: {ingredient.count_unit ?? 'Unavailable'}; reaction bars use co-report activity, not patient counts.</p>
          {ingredient.reactions.map(row => <p key={row.rank}>{row.reaction}: {row.co_report_activity.toLocaleString()} reaction co-report activity</p>)}
          <SourceLink url={ingredient.source?.source_url} />{pro && <p>{ingredient.ingredient_id} · {ingredient.source?.source_name} · Export {ingredient.source?.export_date ?? 'Unknown'}</p>}
        </article>)}<p>Ingredient associations are not product-specific incidence or confirmed side effects. Never add ingredient counts into a product total.</p>
      </EvidencePanel>
    </div>
    <details className="discovery-limitations"><summary>What this overview can—and cannot—tell you</summary><ul>{value.limitations.map(item => <li key={item}>{item}</li>)}</ul>
      <p>Search match: {value.match_scope} · {value.truncated ? 'Only the first 100 matching products are summarized.' : 'Returned search matches only; not comprehensive brand coverage.'}</p></details>
  </section>
}

export function CompactProducts({ products, query, mode, onSelect }: { products: CatalogDrug[]; query: string; mode: ExperienceMode; onSelect: (product: CatalogDrug) => void }) {
  const [strength, setStrength] = useState(''), [form, setForm] = useState(''), [labeler, setLabeler] = useState(''), [ndc, setNdc] = useState('')
  const [sort, setSort] = useState('labeler')
  const pro = mode === 'research_pro'
  const options = (key: 'strength' | 'dosage_form') => [...new Set(products.map(product => product[key]).filter((item): item is string => !!item))].sort()
  const readableStrength = (value: string) => value.replace(/(^|\s|\/)(\.\d)/g, (_match, prefix: string, decimal: string) => `${prefix}0${decimal}`).replace(/\s*\/\s*/g, ' / ')
  const rows = products.filter(product => (!strength || product.strength === strength) && (!form || product.dosage_form === form)
    && (!labeler || product.manufacturers.some(name => name.toLowerCase().includes(labeler.toLowerCase())))
    && (!ndc || [...product.product_ndcs, ...product.package_ndcs].some(value => value.includes(ndc))))
    .sort((left, right) => {
      const pick = (product: CatalogDrug) => sort === 'strength' ? product.strength : sort === 'ndc' ? product.product_ndcs.join(', ') : product.manufacturers.join(', ')
      return (pick(left) ?? '').localeCompare(pick(right) ?? '', undefined, { numeric: true }) || left.id.localeCompare(right.id)
    })
  const advanced = <><label>Labeler<input value={labeler} onChange={event => setLabeler(event.target.value)} placeholder="Recorded company name" /></label><label>Product or package NDC<input value={ndc} onChange={event => setNdc(event.target.value)} placeholder="Identifier" /></label></>
  return <section className="selection compact-product-selection" aria-labelledby="selection-heading"><div className="selection-heading-row"><div><p className="eyebrow">Next: choose a formulation</p><h2 id="selection-heading">Select an exact product</h2></div><p>{rows.length} of {products.length} matching rows</p></div>
    <p className="compact-helper">Check strength, dosage form and the recorded labeler against your package. Manufacturer is not independently verified. Product filters affect these rows; the overview keeps its stated matching-product scope.</p>
    <div className="product-filters"><GlassSelect label="Strength" value={strength} onChange={setStrength} mode={mode} options={[{value:'',label:'All strengths'},...options('strength').map(value => ({value,label:readableStrength(value)}))]} />
      <GlassSelect label="Dosage form" value={form} onChange={setForm} mode={mode} options={[{value:'',label:'All forms'},...options('dosage_form').map(value => ({value,label:value}))]} />
      {pro && <GlassSelect label="Sort products" value={sort} onChange={setSort} mode={mode} options={[{value:'labeler',label:'Labeler'},{value:'strength',label:'Strength'},{value:'ndc',label:'Product NDC'}]} />}
      {pro ? advanced : <details className="advanced-product-filters"><summary>More product filters</summary><div className="advanced-filter-toolbar">{advanced}</div></details>}
    </div>
    {pro ? <div className="technical-product-table-wrap"><table className="technical-products-table"><caption className="immersive-sr-only">Matching products and exact source identifiers</caption>
      <thead><tr><th scope="col" aria-sort={sort === 'labeler' ? 'ascending' : undefined}>Recorded labeler</th><th scope="col" aria-sort={sort === 'strength' ? 'ascending' : undefined}>Strength · form</th><th scope="col" aria-sort={sort === 'ndc' ? 'ascending' : undefined}>Product NDC</th><th scope="col">Exact-product evidence</th></tr></thead>
      <tbody>{rows.map(product => <Fragment key={product.id}><tr><th scope="row">{product.manufacturers.join(', ') || 'Labeler not supplied'}{product.brand_names.some(name => name.toLowerCase() !== query.toLowerCase()) && <small>{product.brand_names.join(', ')} · separate named formulation</small>}</th>
        <td>{product.strength ?? 'Unknown strength'} · {product.dosage_form ?? 'Unknown form'}</td><td>{product.product_ndcs.join(', ')}</td>
        <td><button aria-label={`Select ${product.manufacturers.join(', ') || 'unlisted labeler'}, ${product.strength}, ${product.dosage_form}, NDC ${product.product_ndcs.join(', ')}`} onClick={() => onSelect(product)}>View evidence →</button></td></tr>
        <tr className="product-provenance-row"><td colSpan={4}><details><summary>Identifiers and source provenance</summary><p>Product ID: {product.id}<br />Formulation ID: {product.formulation_id ?? 'Not established'} · Package NDC: {product.package_ndcs.join(', ') || 'Not supplied'}</p><p>Source record: {product.provenance.source_record_id} · Ingredient: {product.active_ingredients.join(', ')} · Route: {product.routes.join(', ')}</p><SourceLink url={product.provenance.source_url} /></details></td></tr></Fragment>)}</tbody>
    </table></div> : <div className="compact-product-rows">{rows.map(product => <article className="compact-product-row" key={product.id}>
      <div><strong>{product.manufacturers.join(', ') || 'Labeler not supplied'}</strong>{product.brand_names.some(name => name.toLowerCase() !== query.toLowerCase()) && <small>{product.brand_names.join(', ')} · separate named formulation</small>}</div>
      <p>{product.strength ?? 'Strength not supplied'} <span>· {product.dosage_form ?? 'Form not supplied'}</span></p><small className="product-ndc">{product.product_ndcs.join(', ')}</small>
      <button aria-label={`Select ${product.manufacturers.join(', ') || 'unlisted labeler'}, ${product.strength}, ${product.dosage_form}, NDC ${product.product_ndcs.join(', ')}`} onClick={() => onSelect(product)}>View evidence <span aria-hidden="true">→</span></button>
      <details><summary>More product details</summary><p>Product NDC: {product.product_ndcs.join(', ')} · Package NDC: {product.package_ndcs.join(', ') || 'Not supplied'}</p><p>Ingredient: {product.active_ingredients.join(', ')} · Route: {product.routes.join(', ')}</p><SourceLink url={product.provenance.source_url} /></details>
    </article>)}</div>}
    {!rows.length && <p>No matching product rows. Clear filters or search another medication.</p>}
  </section>
}
