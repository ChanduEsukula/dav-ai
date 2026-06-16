import HelpDocsSearch from './HelpDocsSearch'

type InfoPageProps = {
  eyebrow: string
  title: string
  text: string
}

function InfoPage({ eyebrow, title, text }: InfoPageProps) {
  return (
    <>
      <section className="trust reveal">
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        <p>{text}</p>
      </section>
      <HelpDocsSearch />
    </>
  )
}

export default InfoPage
