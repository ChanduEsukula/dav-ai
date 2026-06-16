import HelpDocsSearch from './HelpDocsSearch'

type InfoPageProps = {
  eyebrow: string
  title: string
  text: string
  showHelpDocsSearch?: boolean
}

function InfoPage({
  eyebrow,
  title,
  text,
  showHelpDocsSearch = false,
}: InfoPageProps) {
  return (
    <>
      <section className="trust reveal">
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        <p>{text}</p>
      </section>
      {showHelpDocsSearch && <HelpDocsSearch />}
    </>
  )
}

export default InfoPage
