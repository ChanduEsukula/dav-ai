export const faqs = [
  {
    question: 'Is MedTrek AI FDA approved?',
    answer:
      'No. MedTrek AI is not FDA approved and does not claim to be a regulated medical device. It uses public FDA/openFDA data to help users review public safety information more easily.',
  },
  {
    question: 'Is this medical advice?',
    answer:
      'No. MedTrek AI is a public-data review and safety-intelligence tool. It does not diagnose, prescribe, recommend treatment, or tell users to start, stop, or change medication. Users should consult a qualified clinician or pharmacist for medical decisions.',
  },
  {
    question: 'Where does the recall data come from?',
    answer:
      'RecallRadar currently uses the openFDA Drug Enforcement API. The app shows recall records, classification, status, recall date, firm, retrieval timestamp, and audit details so the result can be traced back to the public source.',
  },
  {
    question: 'Where does DrugSignal data come from?',
    answer:
      'DrugSignal uses the openFDA Drug Event API, which exposes public FAERS adverse-event report data. These reports are useful for reporting-pattern review, but they do not prove that a drug caused a reaction.',
  },
  {
    question: 'How is the Recall Review Score calculated?',
    answer:
      'The score is a transparent review-priority score, not a medical risk score. It considers factors such as FDA recall classification, recall status, recency, and distribution scope. The goal is to help users prioritize which public records deserve review first.',
  },
  {
    question: 'Do FAERS reports prove that a drug caused a reaction?',
    answer:
      'No. FAERS reports do not prove causation. Reports may be incomplete, duplicated, delayed, influenced by reporting behavior, or missing clinical context. DrugSignal shows reporting patterns only.',
  },
  {
    question: 'What is Safety Briefing Engine v1?',
    answer:
      'Safety Briefing Engine v1 is a deterministic role-based briefing layer. It turns structured RecallRadar and DrugSignal response data into summaries, review checklists, limitations, and source/audit details for consumers, pharmacies, clinics, and public-health analysts.',
  },
  {
    question: 'Does a matched recall mean my product is unsafe?',
    answer:
      'Not automatically. A matched record may apply only to a specific lot, package, manufacturer, date range, or distribution area. Users must review the exact FDA record and product details before making decisions.',
  },
  {
    question: 'Who is MedTrek AI for?',
    answer:
      'The early users are consumers, pharmacy teams, clinic administrators, public-health teams, university health centers, and small healthcare organizations that need a clearer way to review public safety signals.',
  },
  {
    question: 'Why not just use the FDA website directly?',
    answer:
      'Public portals are useful, but they can be hard to review quickly. MedTrek AI adds a cleaner workflow: search, normalized cards, review-priority scoring, FAERS reporting-pattern summaries, role-based briefings, source timestamps, and audit details.',
  },
]