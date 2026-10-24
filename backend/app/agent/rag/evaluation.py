"""Fixed source-span judgments, SQL baselines, and transparent passage metrics."""
import hashlib
import re
import statistics
import sys
from time import perf_counter

from pydantic import Field, model_validator

from app.agent.briefing import LABEL_FIELDS
from app.agent.source_tools import get_drug_label_evidence
from .corpus import Contract, document_key


class Span(Contract):
    source_record_id: str
    section: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')


class Question(Contract):
    case_id: str
    tags: list[str] = Field(min_length=1)
    ndc: str
    question: str = Field(min_length=1)
    relevant_spans: list[Span]
    missing_section: str | None = None
    rationale: str


class Annotations(Contract):
    version: str
    annotation_method: str
    cases: list[Question] = Field(min_length=1)

    @model_validator(mode='after')
    def unique_ids(self):
        if len({case.case_id for case in self.cases}) != len(self.cases):
            raise ValueError('Duplicate question IDs')
        return self


def exact_product(corpus, ndc):
    products = [p for p in corpus.products if ndc in p.product_ndcs]
    if len(products) != 1:
        raise ValueError('Question must bind to one exact sampled product/NDC')
    return products[0]


def relevant_chunks(corpus, case):
    product = exact_product(corpus, case.ndc)
    documents = {document_key(d): d for d in corpus.documents if d.product_id == product.product_id}
    relevant = set()
    for span in case.relevant_spans:
        matches = [d for d in documents.values() if d.label.source_record_id == span.source_record_id]
        if len(matches) != 1 or span.section not in LABEL_FIELDS:
            raise ValueError('Annotation source or section is not admitted for this product')
        document = matches[0]
        text = getattr(document.label, span.section)
        if (not text or not 0 <= span.start < span.end <= len(text)
                or hashlib.sha256(text[span.start:span.end].encode()).hexdigest() != span.text_sha256):
            raise ValueError('Annotation span no longer matches frozen source text')
        for chunk in corpus.chunks:
            if (chunk.document_key == document_key(document) and chunk.section == span.section
                    and max(chunk.start, span.start) < min(chunk.end, span.end)):
                relevant.add(chunk.chunk_id)
    if not case.relevant_spans:
        if case.missing_section not in (*LABEL_FIELDS, 'all'):
            raise ValueError('Missing-evidence cases require an explicit absent section/all')
        if any(case.missing_section == 'all' or getattr(d.label, case.missing_section) for d in documents.values()):
            raise ValueError('Missing-evidence annotation contradicts admitted source')
    return relevant


def metrics(ranked_ids, relevant, k=5):
    if len(ranked_ids) != len(set(ranked_ids)):
        raise ValueError('Duplicate retrieval results')
    ranked_ids = ranked_ids[:k]
    if not relevant:
        return {'recall_at_5': None, 'precision_at_5': None, 'mrr_at_5': None,
                'empty_evidence_correct': not ranked_ids}
    hits = len(set(ranked_ids) & relevant)
    return {'recall_at_5': hits / len(relevant), 'precision_at_5': hits / k,
            'mrr_at_5': next((1 / rank for rank, cid in enumerate(ranked_ids, 1) if cid in relevant), 0.0),
            'empty_evidence_correct': None}


SECTION_PATTERNS = {
    'boxed_warning': r'\bboxed\b|\bblack box\b',
    'contraindications': r'\bcontraindicat|\bwho should not\b',
    'drug_interactions': r'\binteract|\bcombined with\b|\btogether with\b',
    'adverse_reactions': r'\badverse\b|\bside effects\b',
    'warnings_and_precautions': r'\bprecautions?\b',
}


class SQLBaseline:
    """Existing admitted SQL evidence, expanded to passage IDs without embeddings.

    Native behavior returns all label sections, not question-ranked top-k. The
    first baseline uses its fixed section order; the optional lexical router is
    an explicit prototype comparator, NOT a feature of the existing workflow.
    """
    def __init__(self, corpus, *, keyword_sections=False, provider=get_drug_label_evidence):
        self.corpus, self.keyword_sections, self.provider = corpus, keyword_sections, provider

    def search(self, case):
        product = exact_product(self.corpus, case.ndc)
        evidence = self.provider(product.product_id)
        if (evidence['product_id'] != product.product_id
                or evidence['product_ndcs'] != product.product_ndcs):
            raise ValueError('SQL product binding mismatch')
        records = evidence['evidence']['records']
        documents = [d for d in self.corpus.documents if d.product_id == product.product_id]
        if len(records) != len(documents) or {r['id'] for r in records} != {d.label.id for d in documents}:
            raise ValueError('SQL sample label membership changed')
        for document in documents:
            record = next(r for r in records if r['id'] == document.label.id)
            if (any(record.get(section) != getattr(document.label, section) for section in LABEL_FIELDS)
                    or evidence['release'] != document.release.model_dump()):
                raise ValueError('SQL evidence no longer matches corpus')
        requested = [section for section, pattern in SECTION_PATTERNS.items() if re.search(pattern, case.question, re.I)]
        sections = requested if requested and self.keyword_sections else list(LABEL_FIELDS)
        ranked = []
        for record in records:
            key = document_key(next(d for d in documents if d.label.id == record['id']))
            for section in sections:
                ranked.extend(c.chunk_id for c in self.corpus.chunks if c.document_key == key and c.section == section)
        return ranked[:5]


def evaluate(corpus, annotations, retrievers):
    # Validate all judgments before any retriever runs: no gold generation from rankings.
    judgments = {case.case_id: relevant_chunks(corpus, case) for case in annotations.cases}
    owners = {c.chunk_id: next(d.product_id for d in corpus.documents if document_key(d) == c.document_key)
              for c in corpus.chunks}
    output = {}
    for name, retrieve in retrievers.items():
        cases = []
        for case in annotations.cases:
            timings = {}
            start = perf_counter()
            ids = retrieve(case, timings)
            timings['query_total_seconds'] = perf_counter() - start
            if any(cid not in owners for cid in ids):
                raise ValueError('Retriever returned unknown chunk')
            pid = exact_product(corpus, case.ndc).product_id
            correct = sum(owners[cid] == pid for cid in ids)
            cases.append({'case_id': case.case_id, 'ndc': case.ndc, 'question': case.question, 'tags': case.tags,
                          'ranked_chunk_ids': ids, 'relevant_chunk_ids': sorted(judgments[case.case_id]),
                          **metrics(ids, judgments[case.case_id]), **timings,
                          'correct_product_results': correct, 'returned_results': len(ids)})
        total_returned = sum(c['returned_results'] for c in cases)
        summary = {key: statistics.mean(values) if (values := [c[key] for c in cases if c[key] is not None]) else None
                   for key in ('recall_at_5', 'precision_at_5', 'mrr_at_5', 'empty_evidence_correct')}
        summary.update(positive_cases=sum(bool(judgments[c.case_id]) for c in annotations.cases),
                       negative_cases=sum(not judgments[c.case_id] for c in annotations.cases),
                       product_identity_accuracy=sum(c['correct_product_results'] for c in cases) / total_returned if total_returned else None,
                       returned_results=total_returned,
                       median_query_seconds=statistics.median(c['query_total_seconds'] for c in cases))
        output[name] = {'summary': summary, 'cases': cases}
    try:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_bytes = peak if sys.platform == 'darwin' else peak * 1024
    except ImportError:
        peak_bytes = None
    return {'annotation_version': annotations.version, 'annotation_method': annotations.annotation_method,
            'results': output, 'process_lifetime_peak_rss_bytes': peak_bytes,
            'limitations': ['Small source-span pilot, single assessor; external relevance review is pending.',
                            'MRR is truncated at rank 5. Precision denominator is 5 even for fewer results.',
                            'Ranking metrics exclude negative cases, reported separately as empty-evidence correctness.',
                            'Identity accuracy measures returned passage containment, not natural-language drug resolution.',
                            'Minimal support spans are not exhaustive relevance judgments; precision is against this annotation set only.',
                            'SQL native first-5 is an evaluation projection; the existing API returns full sections.',
                            'Peak RSS covers the entire process, not isolated per-retriever memory; latencies are one trial per case.']}
