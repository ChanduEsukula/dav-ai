"""Source-blind ranking evaluation with separately denominated abstention metrics."""
from collections import Counter
from typing import Literal
import statistics
from time import perf_counter

from pydantic import Field, model_validator

from .corpus import Contract, digest, document_key
from .evaluation import Question, exact_product, metrics, relevant_chunks
from .hybrid import policy_fingerprint, requested_sections


class HeldoutQuestion(Question):
    group: Literal['explicit', 'semantic']
    negative_kind: Literal['missing_section', 'no_label', 'unsupported_scope',
                           'unsupported_topic', 'foreign_product'] | None = None
    absent_terms: list[str] = Field(default_factory=list)


class HeldoutAnnotations(Contract):
    version: str
    annotation_method: str
    created_at: str
    policy_sha256: str
    corpus_sha256: str
    cases: list[HeldoutQuestion] = Field(min_length=1)

    @model_validator(mode='after')
    def unique_ids(self):
        if len({case.case_id for case in self.cases}) != len(self.cases):
            raise ValueError('Duplicate question IDs')
        return self


def validate_heldout(corpus, annotations):
    if annotations.policy_sha256 != policy_fingerprint():
        raise ValueError('Policy differs from held-out freeze')
    if annotations.corpus_sha256 != digest(corpus.model_dump(mode='json')):
        raise ValueError('Held-out corpus fingerprint mismatch')
    judgments = {}
    for case in annotations.cases:
        if (case.group == 'explicit') != bool(requested_sections(case.question)):
            raise ValueError('Explicit/semantic group contradicts literal section policy')
        product = exact_product(corpus, case.ndc)
        if case.relevant_spans:
            if case.negative_kind or case.missing_section or case.absent_terms:
                raise ValueError('Positive and negative judgments conflict')
            judgments[case.case_id] = relevant_chunks(corpus, case)
        else:
            if not case.negative_kind or not case.rationale.strip():
                raise ValueError('Negative requires an independently specified reason')
            if case.missing_section:
                relevant_chunks(corpus, case)  # Validates actual absence in source.
            elif case.negative_kind in ('no_label', 'missing_section'):
                raise ValueError('Missing-evidence cases require a source absence assertion')
            if case.negative_kind == 'unsupported_topic' and not case.absent_terms:
                raise ValueError('Unsupported-topic case requires source absence checks')
            text = '\n'.join(c.text for c in corpus.chunks if next(
                d.product_id for d in corpus.documents if document_key(d) == c.document_key
            ) == product.product_id).casefold()
            if any(term.casefold() in text for term in case.absent_terms):
                raise ValueError('Negative topic term occurs in source; reassess annotation')
            judgments[case.case_id] = set()
    return judgments


def summarize(cases):
    positives = [c for c in cases if c['relevant_chunk_ids']]
    negatives = [c for c in cases if not c['relevant_chunk_ids']]
    missing = [c for c in negatives if c['group'] == 'explicit'
               and c['negative_kind'] in ('missing_section', 'no_label')]
    unsupported = [c for c in negatives if c['negative_kind'] in (
        'unsupported_scope', 'unsupported_topic', 'foreign_product')]
    returned = sum(c['returned_results'] for c in cases)
    def fraction(rows, predicate):
        return sum(predicate(c) for c in rows) / len(rows) if rows else None
    return dict(cases=len(cases), positive_cases=len(positives), negative_cases=len(negatives),
        **{key: statistics.mean(c[key] for c in positives) if positives else None
           for key in ('recall_at_5', 'precision_at_5', 'mrr_at_5')},
        product_containment=sum(c['correct_product_results'] for c in cases)/returned if returned else None,
        correct_product_results=sum(c['correct_product_results'] for c in cases),returned_results=returned,
        missing_section_cases=len(missing),
        missing_section_abstention_accuracy=fraction(missing,lambda c:not c['ranked_chunk_ids']),
        false_abstention_rate=fraction(positives,lambda c:not c['ranked_chunk_ids']),
        unsupported_cases=len(unsupported),
        unsupported_evidence_acceptance_rate=fraction(unsupported,lambda c:bool(c['ranked_chunk_ids'])),
        all_negative_candidate_return_rate=fraction(negatives,lambda c:bool(c['ranked_chunk_ids'])),
        status_counts=dict(Counter(c['status'] for c in cases)),
        positive_status_counts=dict(Counter(c['status'] for c in positives)) if positives else {},
        negative_status_counts=dict(Counter(c['status'] for c in negatives)) if negatives else {},
        median_query_ms=statistics.median(c['query_ms'] for c in cases) if cases else None,
        p95_query_ms=sorted(c['query_ms'] for c in cases)[min(len(cases)-1,int(.95*len(cases)))] if cases else None,
        decision_reasons=dict(Counter(c['reason'] for c in cases)))


def evaluate_decisions(corpus, annotations, retrievers, *, heldout=True):
    # Every judgment is validated before the first retrieval, never inferred from ranking.
    judgments = validate_heldout(corpus, annotations) if heldout else {
        case.case_id: relevant_chunks(corpus,case) for case in annotations.cases}
    owners = {c.chunk_id:next(d.product_id for d in corpus.documents if document_key(d)==c.document_key)
              for c in corpus.chunks}
    results = {}
    for name, retrieve in retrievers.items():
        rows=[]
        for case in annotations.cases:
            pid=exact_product(corpus,case.ndc).product_id
            start=perf_counter(); decision=retrieve(case,pid); elapsed=(perf_counter()-start)*1000
            ids=list(decision.chunk_ids)
            if any(cid not in owners for cid in ids):
                raise ValueError('Retriever returned an unknown chunk')
            rows.append(dict(case_id=case.case_id,ndc=case.ndc,question=case.question,
                group=getattr(case,'group','explicit' if requested_sections(case.question) else 'semantic'),
                negative_kind=getattr(case,'negative_kind',None) or (
                    'missing_section' if not case.relevant_spans else None),
                relevant_chunk_ids=sorted(judgments[case.case_id]),ranked_chunk_ids=ids,
                **metrics(ids,judgments[case.case_id]),
                correct_product_results=sum(owners[cid]==pid for cid in ids),returned_results=len(ids),
                query_ms=elapsed,status=decision.status,reason=decision.reason,route=decision.route,
                degraded_reason=decision.degraded_reason,verified_answer=decision.verified_answer))
        results[name]={'summary':summarize(rows),'groups':{
            group:summarize([c for c in rows if c['group']==group]) for group in ('explicit','semantic')},'cases':rows}
    return {'annotation_version':annotations.version,'policy_sha256':policy_fingerprint(),'results':results,
        'metric_notes':[
            'R/P/MRR@5 are macro means on positive cases only; precision denominator always 5.',
            'Minimal source spans are not exhaustive relevance judgments; paired questions share facts.',
            'Missing-section abstention denominator: explicit negatives of kind missing_section/no_label.',
            'Unsupported-evidence acceptance is a conservative retrieval proxy: any candidates for an annotated unsupported scope/topic or foreign-product question count as acceptance, even when unverified.',
            'All-negative return rate also includes missing sections and no-label questions.',
            'No generator or verified answers; candidate relevance remains uncalibrated.',
            'Latency includes decision/source validation; SQL native is a first-five projection of full sections.',
            'Single assessor, retrieval-blind source annotation; independent human review remains pending.']}
