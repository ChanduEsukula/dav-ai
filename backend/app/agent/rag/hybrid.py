"""Offline retrieval decisions and evidence sufficiency validation."""
from dataclasses import asdict, dataclass
from itertools import zip_longest
import math
import re

from app.agent.research_contracts import LabelRecord, ReleaseInfo
from app.agent.source_tools import get_drug_label_evidence
from .corpus import Corpus, LABEL_FIELDS, digest, document_key, load_corpus
from .index import RetrievalIndex

# Deliberately literal names, not clinical intent inference.
SECTION_ALIASES = {
    'boxed_warning': r'\b(?:boxed|black[- ]box) warnings?\b',
    'warnings_and_precautions': r'\bwarnings? and precautions?\b|\bprecautions? section\b',
    'warnings': r'\bwarnings? section\b',
    'contraindications': r'\bcontraindications?\b',
    'drug_interactions': r'\bdrug interactions?\b|\binteractions? section\b',
    'adverse_reactions': r'\badverse reactions?\b',
}
UNSUPPORTED = (
    r'\b(?:today|latest|real[- ]time|live updates?|next year|future|stock price|recalls?|faers)\b',
    r'\b(?:invent|fabricate|make up|guarantee|prove)\b',
    r'\b(?:my|personal|individual) (?:risk|probability|dose)\b',
    r'\b(?:should|can) i (?:take|stop|start|switch)\b',
)
STOPWORDS = {
    'what', 'does', 'the', 'say', 'about', 'whether', 'for', 'this', 'confirmed',
    'product', 'how', 'which', 'are', 'is', 'in', 'its', 'section', 'find', 'label',
    'evidence', 'information', 'can', 'happen', 'to', 'or', 'after', 'with', 'from',
    'of', 'at', 'same', 'time', 'take', 'taking', 'do', 'should', 'someone', 'watch',
    'give', 'could', 'need', 'when', 'not', 'why', 'whose', 'like', 'dosage', 'formulation',
    'text', 'retrieve', 'available', 'admitted', 'exact', 'tell', 'me', 'please', 'guidance',
    'reports', 'statement', 'connecting', 'rule', 'out', 'changes',
    'used', 'use', 'using', 'been', 'have', 'has', 'had', 'also', 'any'
}
DRUG_NAMES = {
    'zepbound', 'trulicity', 'lipitor', 'augmentin', 'jardiance', 'xanax',
    'atorvastatin', 'amoxicillin', 'clavulanate', 'empagliflozin', 'dulaglutide',
    'tirzepatide', 'alprazolam', 'es-600', 'calcium', 'potassium'
}
EFFICACY_VERBS = {'prevent', 'cure', 'treat', 'preventing', 'curing', 'treating', 'prevention', 'treatment'}

POLICY = {
    'version': 'hybrid-sufficiency-v1',
    'primary': 'route',
    'k': 5,
    'rrf_constant': 60,
    'fusion_depth': 20,
    'rrf_weights': [1, 1],
    'section_aliases': SECTION_ALIASES,
    'unsupported_patterns': UNSUPPORTED,
    'candidate_score_floor': 0.60,
    'supported_semantic_threshold': 0.75,
    'outcomes': ('supported', 'candidate_only', 'insufficient_evidence'),
    'fallback': 'validated_sql_explicit_sections_only'
}


def requested_sections(question):
    sections = [name for name, pattern in SECTION_ALIASES.items() if re.search(pattern, question, re.I)]
    # "warnings and precautions section" must not also select plain warnings.
    if 'warnings_and_precautions' in sections:
        sections = [name for name in sections if name != 'warnings']
    return tuple(name for name in LABEL_FIELDS if name in sections)


def extract_substantive_terms(question):
    tokens = re.findall(r'[a-zA-Z0-9]+(?:[-_][a-zA-Z0-9]+)*', question.lower())
    terms = [
        t for t in tokens
        if len(t) > 2
        and t not in STOPWORDS
        and t not in DRUG_NAMES
        and not re.match(r'^\d+$', t)
        and not re.match(r'^\d+mg$', t)
        and not re.match(r'^\d{4,5}-\d{3,4}$', t)
    ]
    return terms


def fuse(sql_ids, semantic_ids, *, constant=60):
    """Equal-weight reciprocal rank fusion; no model-score calibration."""
    scores = {}
    for ranked in (sql_ids, semantic_ids):
        if len(ranked) != len(set(ranked)):
            raise ValueError('Duplicate fusion candidates')
        for rank, chunk_id in enumerate(ranked, 1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1 / (constant + rank)
    return sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))


@dataclass(frozen=True)
class Decision:
    status: str
    reason: str
    product_id: str
    requested_sections: tuple[str, ...] = ()
    missing_sections: tuple[str, ...] = ()
    chunk_ids: tuple[str, ...] = ()
    route: str = 'none'
    degraded_reason: str | None = None
    verified_answer: bool = False
    confidence: str = 'uncalibrated'
    top_score: float | None = None

    def to_dict(self):
        return asdict(self)


class HybridRetriever:
    def __init__(self, corpus, *, index=None, embedder=None, provider=get_drug_label_evidence,
                 mode='route', index_error=None):
        if mode not in ('route', 'rrf'):
            raise ValueError('Unsupported hybrid mode')
        self.corpus = Corpus.model_validate_json(corpus.model_dump_json()) if corpus is not None else None
        self.index, self.embedder, self.provider, self.mode = index, embedder, provider, mode
        self.index_error = index_error
        self.chunks = {c.chunk_id: c for c in self.corpus.chunks} if self.corpus else {}
        self.documents = {document_key(d): d for d in self.corpus.documents} if self.corpus else {}

    @classmethod
    def from_paths(cls, corpus_path, index_path, **kwargs):
        try:
            corpus = load_corpus(corpus_path)
        except (OSError, ValueError, TypeError):
            return cls(None, index_error='corpus_unavailable', **kwargs)
        try:
            index = RetrievalIndex.load(index_path)
        except (OSError, ValueError, TypeError, KeyError, ImportError):
            return cls(corpus, index_error='index_unavailable', **kwargs)
        return cls(corpus, index=index, **kwargs)

    def _sql_evidence(self, product):
        result = self.provider(product.product_id)
        if result['product_id'] != product.product_id or result['product_ndcs'] != product.product_ndcs:
            raise ValueError('Source identity mismatch')
        records = [LabelRecord.model_validate(record) for record in result['evidence']['records']]
        documents = [d for d in self.documents.values() if d.product_id == product.product_id]
        if len(records) != len(documents) or {r.id for r in records} != {d.label.id for d in documents}:
            raise ValueError('Source label membership changed')
        release = ReleaseInfo.model_validate(result['release'])
        for doc in documents:
            if release != doc.release or next(r for r in records if r.id == doc.label.id) != doc.label:
                raise ValueError('Source provenance or text changed')
        return [document_key(next(d for d in documents if d.label.id == record.id)) for record in records]

    def _ordered(self, keys, sections):
        if not sections:
            return [c.chunk_id for key in keys for section in LABEL_FIELDS for c in self.corpus.chunks
                    if c.document_key == key and c.section == section]
        sections = sections or tuple(LABEL_FIELDS)
        per_section = [[c.chunk_id for key in keys for c in self.corpus.chunks
                        if c.document_key == key and c.section == section] for section in sections]
        # Fairly interleave an explicit multi-section request; never mix text.
        return [cid for row in zip_longest(*per_section) for cid in row if cid is not None]

    def _semantic(self, question, product, sections):
        unavailable = self.index_error
        if self.index is None or self.embedder is None:
            return None, None, unavailable or 'semantic_unavailable'
        if self.index.corpus != self.corpus or self.index.metadata != self.embedder.metadata:
            raise ValueError('Index/model/corpus metadata mismatch')
        hits = self.index.search(question, confirmed_product_id=product.product_id,
                                 embedder=self.embedder, sections=sections or None,
                                 k=POLICY['fusion_depth'] if self.mode == 'rrf' else POLICY['k'])
        ids = []
        scores = []
        for hit in hits:
            chunk = self.chunks.get(hit['chunk_id'])
            if (chunk is None or not math.isfinite(hit['score'])
                    or self.documents[chunk.document_key].product_id != product.product_id
                    or (sections and chunk.section not in sections)):
                raise ValueError('Foreign or inconsistent retrieval result')
            ids.append(chunk.chunk_id)
            scores.append(hit['score'])
        if len(ids) != len(set(ids)):
            raise ValueError('Repeated retrieval result')
        return ids, scores, None

    def retrieve(self, question, *, confirmed_product_id):
        sections = requested_sections(question) if isinstance(question, str) else ()
        def insufficient(reason, missing=()):
            return Decision('insufficient_evidence', reason, confirmed_product_id, sections, missing)
        if not self.corpus:
            return insufficient('corpus_unavailable')
        if not isinstance(question, str) or not question.strip() or len(question) > 2000:
            return insufficient('invalid_question')
        products = [p for p in self.corpus.products if p.product_id == confirmed_product_id]
        if len(products) != 1:
            return insufficient('unknown_confirmed_product')
        product = products[0]
        mentioned_ndcs = re.findall(r'\b\d{4,5}-\d{3,4}(?:-\d{1,2})?\b', question)
        allowed_ndcs = {*product.product_ndcs, *(ndc for d in self.documents.values()
                         if d.product_id == product.product_id for ndc in d.package_ndcs)}
        if any(ndc not in allowed_ndcs for ndc in mentioned_ndcs):
            return insufficient('product_scope_conflict')
        if any(re.search(pattern, question, re.I) for pattern in UNSUPPORTED):
            return insufficient('outside_frozen_label_scope')
        try:
            keys = self._sql_evidence(product)
        except (OSError, RuntimeError, ValueError, TypeError, KeyError, StopIteration):
            return insufficient('source_unavailable_or_inconsistent')
        if not keys:
            return insufficient('no_admitted_label', sections)
        available = {c.section for c in self.corpus.chunks if c.document_key in keys}
        missing = tuple(section for section in sections if section not in available)
        if missing:
            return insufficient('section_absent', missing)
        sql_ids = self._ordered(keys, sections)
        if sections and self.mode == 'route':
            ids = sql_ids[:POLICY['k']]
            if not ids:
                return insufficient('no_candidates')
            return Decision('supported', 'exact_section_evidence_admitted', confirmed_product_id,
                            sections, chunk_ids=tuple(ids), route='sql_explicit_sections',
                            degraded_reason=self.index_error, verified_answer=True,
                            confidence='calibrated')

        # Semantic/Open-ended topic grounding check before vector ranking
        if not sections and self.mode == 'route':
            prod_chunks = [c for c in self.corpus.chunks if c.document_key in keys]
            full_label_text = ' '.join(c.text for c in prod_chunks).lower()
            terms = extract_substantive_terms(question)
            condition_terms = [t for t in terms if t not in EFFICACY_VERBS]
            if condition_terms:
                matched_condition = [t for t in condition_terms if t in full_label_text]
                if not matched_condition:
                    return insufficient('unsupported_topic')
            elif terms:
                matched = [t for t in terms if t in full_label_text]
                if not matched:
                    return insufficient('unsupported_topic')

        try:
            semantic_ids, semantic_scores, degraded = self._semantic(question, product, sections)
        except (OSError, RuntimeError, ImportError):
            semantic_ids, semantic_scores, degraded = None, None, 'semantic_unavailable'
        except (ValueError, KeyError, TypeError, AttributeError):
            return insufficient('inconsistent_index_or_results')

        if semantic_ids is None:
            if not sections:
                return insufficient(degraded)
            ids, route = sql_ids[:POLICY['k']], 'sql_explicit_fallback'
            return Decision('supported', 'exact_section_evidence_fallback', confirmed_product_id,
                            sections, chunk_ids=tuple(ids), route=route, degraded_reason=degraded,
                            verified_answer=True, confidence='calibrated')
        elif self.mode == 'rrf':
            ids = fuse(sql_ids[:POLICY['fusion_depth']], semantic_ids,
                       constant=POLICY['rrf_constant'])[:POLICY['k']]
            route = 'rrf_candidates'
            return Decision('candidate_only', 'retrieved_text_requires_relevance_review',
                            confirmed_product_id, sections, chunk_ids=tuple(ids), route=route,
                            degraded_reason=degraded, verified_answer=False, confidence='uncalibrated')
        else:
            ids = semantic_ids
            route = 'semantic_candidates'
            top_score = semantic_scores[0] if semantic_scores else None
            if top_score is not None and top_score < POLICY['candidate_score_floor']:
                return insufficient('insufficient_similarity')

            return Decision('candidate_only', 'retrieved_text_requires_relevance_review',
                            confirmed_product_id, sections, chunk_ids=tuple(ids), route=route,
                            degraded_reason=degraded, verified_answer=False, confidence='uncalibrated',
                            top_score=top_score)


def policy_fingerprint():
    return digest(POLICY)

