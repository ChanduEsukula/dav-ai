export const faqs = [
  {
    question: 'Is MedSignal AI FDA approved?',
    answer:
      'No. MedSignal AI is not FDA approved and does not claim to be a regulated medical device. It uses public FDA/openFDA recall data to help users review public safety information more easily.',
  },
  {
    question: 'Is this medical advice?',
    answer:
      'No. MedSignal AI is a public-data review and safety-intelligence tool. It does not diagnose, prescribe, or tell users to start, stop, or change medication. Users should consult a qualified clinician or pharmacist for medical decisions.',
  },
  {
    question: 'Where does the recall data come from?',
    answer:
      'The current MVP uses the openFDA Drug Enforcement API. The app shows recall records, classification, status, recall date, firm, retrieval timestamp, and audit details so the result can be traced back to the public source.',
  },
  {
    question: 'How is the Recall Review Score calculated?',
    answer:
      'The score is a transparent review-priority score, not a medical risk score. It considers factors such as FDA recall classification, recall status, recency, distribution scope, and source confidence. The goal is to help users prioritize which records deserve review first.',
  },
  {
    question: 'Does a matched recall mean my product is unsafe?',
    answer:
      'Not automatically. A matched record may apply only to a specific lot, package, manufacturer, date range, or distribution area. Users must review the exact FDA record and product details before taking action.',
  },
  {
    question: 'Who is MedSignal AI for?',
    answer:
      'The early users are consumers, pharmacy teams, clinic administrators, public-health teams, university health centers, and small healthcare organizations that need a clearer way to review public safety signals.',
  },
  {
    question: 'Why not just use the FDA website directly?',
    answer:
      'Public portals are useful, but they can be hard to review quickly. MedSignal AI adds a cleaner workflow: search, normalized cards, review-priority scoring, plain-English context, source timestamps, and audit details.',
  },
]