const faqs = [
  ['Is Dav AI FDA approved?', 'No. Dav AI uses stored public FDA/openFDA evidence. It is not FDA approved and does not claim to be a regulated medical device.'],
  ['Is this medical advice?', 'No. Dav AI does not diagnose, prescribe, recommend treatment or tell you to start, stop or change a medication. Consult a qualified clinician or pharmacist for medical decisions.'],
  ['Where does the evidence come from?', 'The frozen pharmaceutical release contains NDC product identities, admitted drug labels, historical recall records and ingredient-level FAERS reporting data. Source dates, provenance and limitations are shown with the evidence. The app is not a live safety feed.'],
  ['Why must I confirm an exact product?', 'Similar names can refer to different strengths, dosage forms or packages. Ask Dav AI requires an explicit product confirmation before retrieving evidence. Check the NDC and formulation against the product you intend to research.'],
  ['How do grounded AI answers work?', 'When you opt in, a local model selects identifiers for admitted label statements. Python reconstructs the exact original text, including headings, and adds clickable citations. Unsupported identifiers or invalid output are discarded; the structured briefing remains available. Citation checks do not establish clinical completeness or factual support.'],
  ['Do FAERS reports prove that a drug caused a reaction?', 'No. These are ingredient-level reporting associations, not selected-NDC observations, incidence, comparative safety or individual risk. Reporting behavior and missing context affect interpretation. Ingredient counts must not be added into a product total.'],
  ['Does a matched recall apply to every package?', 'Not necessarily. A record may apply only to particular lots or packages. Review the stored applicability, lot scope and original FDA source. An absent linked record does not prove a product has never been recalled.'],
  ['What is the difference between Everyday and Research Pro?', 'Everyday emphasizes guided product confirmation and readable evidence cards. Research Pro adds denser source detail and cohort organization. The evidence and authorization boundaries are shared. Adding products to a cohort does not automatically research them.'],
  ['Can I use the app without a local AI model?', 'The Evidence Explorer does not require a model or account. Ask Dav AI requires the local research server and its ephemeral pairing capability. Explicit deterministic execution can retrieve structured evidence without Ollama. Optional AI answers require an already installed supported local model.'],
  ['Can I download an evidence report?', 'Yes. Select a product in the Evidence Explorer and choose Generate PDF Report. Name and optional age identify that report only; they are not used to estimate medical risk.'],
]

export default function FaqPage() {
  return <main id="main-content" className="portfolio-page faq-page">
    <section className="faq-hero page-entrance"><p className="eyebrow">Frequently asked questions</p><h1>Clear answers.<br />Visible boundaries.</h1><p>What Dav AI does, how its evidence works, and what you can—and cannot—conclude.</p></section>
    <div className="faq-list">{faqs.map(([question, answer]) => <details className="faq-item section-reveal" key={question}>
      <summary><span>{question}</span><strong className="faq-toggle-icon" aria-hidden="true" /></summary><p>{answer}</p>
    </details>)}</div>
    <p className="portfolio-bottom-note">Start with the source. <a href="/">Open the Evidence Explorer →</a></p>
  </main>
}
