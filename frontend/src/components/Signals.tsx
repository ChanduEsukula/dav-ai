import { signals } from '../data/signals'

function Signals() {
  return (
    <section className="signals reveal">
      {signals.map((signal) => (
        <article key={signal.title}>
          <span>{signal.number}</span>
          <h2>{signal.title}</h2>
          <p>{signal.text}</p>
        </article>
      ))}
    </section>
  )
}

export default Signals