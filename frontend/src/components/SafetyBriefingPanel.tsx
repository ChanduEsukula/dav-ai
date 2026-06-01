import {
  briefingRoleLabels,
  type SafetyBriefing,
} from '../types/briefing'

type SafetyBriefingPanelProps = {
  briefing: SafetyBriefing
}

type BriefingListProps = {
  title: string
  items: string[]
  defaultOpen?: boolean
}

function SafetyBriefingPanel({ briefing }: SafetyBriefingPanelProps) {
  return (
    <section className="safety-briefing-panel" aria-label="Safety briefing">
      <div className="briefing-header">
        <div>
          <p className="eyebrow">
            {briefing.source === 'drug_event'
              ? 'Safety Briefing Engine v2'
              : 'Safety Briefing Engine v1'}
          </p>
          <h3>{briefingRoleLabels[briefing.role]} briefing</h3>
        </div>

        <span className="briefing-source-pill">
          {briefing.source === 'recall' ? 'RecallRadar' : 'DrugSignal'}
        </span>
      </div>

      <p className="briefing-summary">{briefing.summary}</p>

      <div className="briefing-accordion" aria-label="Briefing sections">
        <BriefingList
          title="What was found"
          items={briefing.whatWasFound}
          defaultOpen
        />

        <BriefingList title="What to verify" items={briefing.whatToVerify} />

        <BriefingList
          title="Suggested review checklist"
          items={briefing.suggestedReviewChecklist}
        />

        <BriefingList title="Limitations" items={briefing.limitations} />
      </div>

      <p className="disclaimer">{briefing.disclaimer}</p>
    </section>
  )
}

function BriefingList({ title, items, defaultOpen = false }: BriefingListProps) {
  return (
    <details className="briefing-card briefing-card--accordion" open={defaultOpen}>
      <summary>
        <h4>{title}</h4>

        <span className="briefing-card__count">
          {items.length} item{items.length === 1 ? '' : 's'}
        </span>

        <span className="briefing-card__chevron" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </span>
      </summary>

      <ul>
        {items.map((item, index) => (
          <li key={`${title}-${index}-${item}`}>{item}</li>
        ))}
      </ul>
    </details>
  )
}

export default SafetyBriefingPanel