type SafeInsightCard = {
  title: string
  label: string
  detail: string
  tone?: 'source' | 'review' | 'safety'
}

type SafeInsightCardsProps = {
  cards: SafeInsightCard[]
}

function SafeInsightCards({ cards }: SafeInsightCardsProps) {
  if (cards.length === 0) return null

  return (
    <section className="safe-insight-cards" aria-label="Safe AI insight cards">
      <div className="safe-insight-cards__header">
        <p className="eyebrow">Safe Insight Cards</p>
        <h3>Source-grounded guidance, not medical advice.</h3>
        <p>
          DavAI summarizes what the public-data response can safely support and keeps
          limitations visible.
        </p>
      </div>

      <div className="safe-insight-cards__grid">
        {cards.map((card) => (
          <article
            className={`safe-insight-card safe-insight-card--${card.tone ?? 'source'}`}
            key={`${card.title}-${card.label}`}
          >
            <span>{card.label}</span>
            <strong>{card.title}</strong>
            <p>{card.detail}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

export type { SafeInsightCard }
export default SafeInsightCards
