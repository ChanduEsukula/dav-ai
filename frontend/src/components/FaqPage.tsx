import { faqs } from '../data/faqs'

function FaqPage() {
  return (
    <section className="faq-page reveal">
      <div className="faq-hero">
        <p className="eyebrow">Frequently Asked Questions</p>
        <h2>Clear answers without crowding the page.</h2>
        <p>
          These questions explain what MedSignal AI is, what it is not, where the data comes
          from, and how to interpret recall search results safely.
        </p>
      </div>

      <div className="faq-list">
        {faqs.map((item) => (
          <details className="faq-item" key={item.question}>
            <summary>
              <span>{item.question}</span>
              <strong>⌄</strong>
            </summary>
            <p>{item.answer}</p>
          </details>
        ))}
      </div>
    </section>
  )
}

export default FaqPage