import { formatTimestamp } from '../utils/recallFormatters'
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
}

function SafetyBriefingPanel({ briefing }: SafetyBriefingPanelProps) {
  return (
    <section className="safety-briefing-panel" aria-label="Safety briefing">
      <div className="briefing-header">
        <div>
          <p className="eyebrow">Safety Briefing Engine v1</p>
          <h3>{briefingRoleLabels[briefing.role]} briefing</h3>
        </div>

        <span className="briefing-source-pill">
          {briefing.source === 'recall' ? 'RecallRadar' : 'DrugSignal'}
        </span>
      </div>

      <p className="briefing-summary">{briefing.summary}</p>

      <div className="briefing-grid">
        <BriefingList title="What was found" items={briefing.whatWasFound} />
        <BriefingList title="What to verify" items={briefing.whatToVerify} />
        <BriefingList
          title="Suggested review checklist"
          items={briefing.suggestedReviewChecklist}
        />
        <BriefingList title="Limitations" items={briefing.limitations} />
      </div>

      <div className="briefing-audit-box">
        <h4>Source and audit details</h4>

        <div className="metadata-grid">
          <div>
            <small>Source</small>
            <span>{briefing.sourceDetails.sourceName}</span>
          </div>

          <div>
            <small>Endpoint</small>
            <span>{briefing.sourceDetails.endpoint}</span>
          </div>

          <div>
            <small>Retrieved</small>
            <span>{formatTimestamp(briefing.sourceDetails.retrievalTimestamp)}</span>
          </div>

          <div>
            <small>Audit ID</small>
            <span>{briefing.sourceDetails.auditId}</span>
          </div>

          <div>
            <small>Record Count</small>
            <span>{briefing.sourceDetails.recordCount}</span>
          </div>
        </div>
      </div>

      <p className="disclaimer">{briefing.disclaimer}</p>
    </section>
  )
}

function BriefingList({ title, items }: BriefingListProps) {
  return (
    <div className="briefing-card">
      <h4>{title}</h4>

      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

export default SafetyBriefingPanel