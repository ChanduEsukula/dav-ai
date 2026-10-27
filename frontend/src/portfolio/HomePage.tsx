import { motion, MotionConfig } from 'motion/react'
import { saveExperienceModePreference } from '../components/experienceState'
import { EvidenceIcon, type EvidenceKind } from './EvidenceIcon'
import ImmersiveOrb from './scene/ImmersiveOrb'
import DataInventory from './DataInventory'
import { ArchitecturePreview } from './OperationalOverview'
import type { ExperienceMode } from '../components/experienceState'
import { useMotionPreference } from './useMotionPreference'

const evidence: { kind: EvidenceKind; title: string; detail: string; description: string }[] = [
  { kind: 'labels', title: 'FDA drug labels', detail: 'Exact-product evidence', description: 'Read admitted label text, with its source, version and limitations.' },
  { kind: 'recalls', title: 'Historical recalls', detail: 'Product links. Lot limits.', description: 'Explore linked historical records. A match does not establish that every lot was affected.' },
  { kind: 'faers', title: 'FAERS reporting', detail: 'Ingredient-level associations', description: 'Explore reported events. Reports do not establish causation, incidence or personal risk.' },
]

export default function HomePage({ mode = 'everyday' }: { mode?: ExperienceMode }) {
  const pro = mode === 'research_pro'
  const reduced = useMotionPreference()
  const reveal = { initial: { opacity: reduced ? 1 : 0, y: reduced ? 0 : 14 }, animate: { opacity: 1, y: 0 },
    transition: { duration: reduced ? 0 : .8, ease: 'easeOut' as const } }
  const hover = reduced ? undefined : { y: -3 }
  return <MotionConfig reducedMotion={reduced ? 'always' : 'never'}><main id="main-content" className="immersive-main">
    <section className="immersive-hero" aria-labelledby="home-title">
      <div className="immersive-horizon" aria-hidden="true" />
      <div className="immersive-hero-grid">
        <motion.div className="immersive-copy" {...reveal}>
          <p className="immersive-eyebrow"><span aria-hidden="true" /> {pro ? 'Research Pro · source-scoped investigation' : 'Stored FDA evidence, explained'}</p>
          <h1 id="home-title">{pro ? 'Deeper evidence.' : 'Real FDA data.'}<br />{' '}<span>{pro ? 'Greater insight.' : 'Clearer answers.'}</span></h1>
          <p className="immersive-intro">{pro ? 'Inspect medication families, exact-product provenance, recall applicability and ingredient-level reporting in a bounded research workspace.' : 'Explore stored FDA drug labels, historical recall records, and ingredient-level adverse-event reports. Inspect the original evidence behind every supported finding.'}</p>
          <div className="immersive-actions">
            <motion.a href="/" className="immersive-primary" whileHover={hover} whileFocus={reduced ? undefined : { scale: 1.02 }}>Explore medications <span aria-hidden="true">↗</span></motion.a>
            <motion.a href="/ask" className="immersive-secondary" whileHover={hover} whileFocus={reduced ? undefined : { scale: 1.02 }}>Ask Dav AI <span aria-hidden="true">→</span></motion.a>
          </div>
          <form action="/" method="get" role="search" aria-label="Find a medication" className="immersive-search">
            <label htmlFor="home-medication" className="immersive-sr-only">Medication name or NDC</label>
            <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.6"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></svg>
            <input id="home-medication" name="q" type="search" placeholder="Medication name or NDC" required maxLength={200} autoComplete="off" />
            <motion.button type="submit" aria-label="Search medications" whileHover={reduced ? undefined : { scale: 1.04 }} whileTap={reduced ? undefined : { scale: .97 }}><span aria-hidden="true">→</span></motion.button>
          </form>
          <p className="immersive-trust">Frozen FDA/openFDA sources <span aria-hidden="true">·</span> Not medical advice</p>
        </motion.div>
        <motion.div className="immersive-scene" {...reveal} transition={{ ...reveal.transition, delay: reduced ? 0 : .12 }}>
          <ImmersiveOrb mode={mode} />
        </motion.div>
      </div>
      <motion.div className="immersive-evidence" {...reveal} transition={{ ...reveal.transition, delay: reduced ? 0 : .2 }}>
        {evidence.map(item => <motion.a key={item.kind} href="#explore-data" className={`immersive-evidence-card evidence-${item.kind}`} whileHover={hover}>
          <span className="immersive-icon"><EvidenceIcon kind={item.kind} /></span>
          <span><strong>{item.title}</strong><small>{item.detail}</small></span>
          <span className="evidence-card-arrow" aria-hidden="true">↗</span>
        </motion.a>)}
      </motion.div>
      <a href="#explore-data" className="immersive-scroll">Explore the platform <span aria-hidden="true">↓</span></a>
    </section>

    <DataInventory mode={mode} />
    <section className="immersive-section capability-section" aria-labelledby="capability-title">
      <p className="immersive-eyebrow">What the application does</p><h2 id="capability-title">Evidence tools with explicit boundaries.</h2>
      <div className="capability-grid">{[
        ['labels', 'Identify an exact product', 'Compare NDCs, recorded labelers, strengths and dosage forms. Similar names remain separate.'],
        ['recalls', 'Inspect historical recall reasons', 'Read linked records, dates, classifications and lot limitations.'],
        ['faers', 'Review reporting associations', 'Ingredient-level reporting charts retain their source window and count units.'],
        ['labels', 'Research within local controls', 'Optional local synthesis uses admitted label statements, citations and an authorized session.'],
      ].map(([kind, title, copy]) => <article className="glass-card" key={title}><EvidenceIcon kind={kind as EvidenceKind} /><h3>{title}</h3><p>{copy}</p></article>)}</div>
    </section>
    <section className="immersive-section immersive-perspectives" aria-labelledby="perspectives-title">
      <div><p className="immersive-eyebrow">Explore your way</p><h2 id="perspectives-title">Guided or technical.<br />{' '}The same source boundaries.</h2></div>
      <div className="immersive-lanes">
        {[
          { mode: 'everyday' as const, name: 'Everyday', title: 'Guided exploration.', copy: 'Larger controls, plain-language summaries, simple charts and suggested questions.' },
          { mode: 'research_pro' as const, name: 'Research Pro', title: 'Technical investigation.', copy: 'Cohort organization, exact-product identifiers, provenance, retrieval details and evidence display filters.' },
        ].map(item => <motion.a key={item.mode} href="/ask" className={`immersive-lane lane-${item.mode}`} whileHover={hover}
          onClick={() => saveExperienceModePreference(item.mode)}>
          <span className="immersive-lane-name">{item.name}</span><h3>{item.title}</h3><p>{item.copy}</p><strong>Open {item.name} <span aria-hidden="true">↗</span></strong>
        </motion.a>)}
      </div>
    </section>

    <section className="immersive-section architecture-preview-section" aria-labelledby="engineering-title"><p className="immersive-eyebrow">How Dav AI is engineered</p><h2 id="engineering-title">From FDA snapshots to source-linked outputs.</h2><ArchitecturePreview /><a href="/overview" className="immersive-text-link">Explore the architecture →</a></section>
    <section className="immersive-section compact-home-limitations"><details><summary>Evidence limitations — read before drawing conclusions</summary><ul><li>Stored snapshots are not a live safety feed.</li><li>Historical recall links may not establish package or lot applicability.</li><li>FAERS reports do not establish causation, incidence or individual patient risk.</li><li>Missing data does not mean an event or warning never existed.</li><li>Dav AI is not FDA approved and does not provide individualized medical advice. Human review is required.</li></ul></details></section>
  </main></MotionConfig>
}
