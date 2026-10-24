"""Synthetic source contracts: never load a model or pharmaceutical release."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

np = pytest.importorskip('numpy')
from test_retrieval import corpus, document
from app.agent.rag.corpus import document_key, save_corpus
from app.agent.rag.embeddings import MockEmbedder
from app.agent.rag.hybrid import HybridRetriever, fuse, requested_sections
from app.agent.rag.index import RetrievalIndex


def provider_for(c):
    def provider(pid):
        product = next(p for p in c.products if p.product_id == pid)
        docs = [d for d in c.documents if d.product_id == pid]
        return dict(product_id=pid, product_ndcs=product.product_ndcs,
                    release=c.documents[0].release.model_dump(),
                    evidence={'records':[d.label.model_dump() for d in docs]})
    return provider


def setup(mode='route'):
    c = corpus()
    embedder = MockEmbedder()
    index = RetrievalIndex.build(c, embedder, engine='numpy-test')
    return c, HybridRetriever(c, index=index, embedder=embedder, provider=provider_for(c), mode=mode)


def test_literal_section_resolution_not_general_medical_intent():
    assert requested_sections('Black-box warning and contraindications?') == ('boxed_warning', 'contraindications')
    assert requested_sections('Warnings and precautions section?') == ('warnings_and_precautions',)
    assert requested_sections('Family cancer history, side effects, and mixing medicines?') == ()


def test_missing_boxed_warning_and_no_label_do_not_call_model():
    c, h = setup()
    h.index.search = lambda *a, **k: pytest.fail('Absent sections must precede ranking')
    for pid, reason in [('a','section_absent'), ('missing','no_admitted_label')]:
        result = h.retrieve('What is the boxed warning?', confirmed_product_id=pid)
        assert result.status == 'insufficient_evidence'
        assert result.reason == reason
        assert result.missing_sections == ('boxed_warning',)
        assert not result.chunk_ids and not result.verified_answer
    assert h.retrieve('General safety information?', confirmed_product_id='missing').reason == 'no_admitted_label'


def test_exact_sections_and_semantic_candidates_remain_unverified():
    c, h = setup()
    explicit = h.retrieve('What are the contraindications?', confirmed_product_id='a')
    assert explicit.route == 'sql_explicit_sections'
    ids = {ch.chunk_id for ch in c.chunks if ch.section == 'contraindications'
           and h.documents[ch.document_key].product_id == 'a'}
    assert set(explicit.chunk_ids) <= ids and len(explicit.chunk_ids) == 5
    semantic = h.retrieve('Original safety source text?', confirmed_product_id='a')
    assert semantic.route == 'semantic_candidates'
    assert semantic.chunk_ids and not semantic.verified_answer
    assert semantic.confidence == 'uncalibrated'


def test_same_brand_different_formulations_and_scope_conflict():
    c, h = setup()
    # Both synthetic formulations deliberately have the same brand name.
    for pid in ('a','b'):
        result = h.retrieve('What are the contraindications?', confirmed_product_id=pid)
        assert all(h.documents[h.chunks[cid].document_key].product_id == pid for cid in result.chunk_ids)
    result = h.retrieve('Contraindications for 22222-2222?', confirmed_product_id='a')
    assert result.reason == 'product_scope_conflict' and not result.chunk_ids
    assert h.retrieve('Anything?', confirmed_product_id='foreign').reason == 'unknown_confirmed_product'


def test_unavailable_index_and_embeddings_fallback_only_explicit_sections(tmp_path):
    c, _ = setup()
    save_corpus(c, tmp_path/'corpus.json')
    for path in (tmp_path/'missing', tmp_path/'malformed'):
        if path.name == 'malformed':
            path.mkdir(); (path/'manifest.json').write_text('not json')
        h = HybridRetriever.from_paths(tmp_path/'corpus.json', path, provider=provider_for(c), mode='rrf')
        first = h.retrieve('Contraindications?', confirmed_product_id='a')
        assert first.route == 'sql_explicit_fallback' and first.degraded_reason == 'index_unavailable'
        assert first == h.retrieve('Contraindications?', confirmed_product_id='a')
        assert not h.retrieve('General clinical evidence?', confirmed_product_id='a').chunk_ids
    h = HybridRetriever.from_paths(tmp_path/'absent.json', tmp_path/'missing')
    assert h.retrieve('Contraindications?', confirmed_product_id='a').reason == 'corpus_unavailable'
    c, h = setup(mode='rrf'); h.embedder = None
    assert h.retrieve('Contraindications?', confirmed_product_id='a').route == 'sql_explicit_fallback'
    assert not h.retrieve('General clinical evidence?', confirmed_product_id='a').chunk_ids


@pytest.mark.parametrize('failure', ['foreign','unknown','nan','duplicate','model','corpus','provider','down'])
def test_corruption_and_cross_product_contamination_fail_closed(failure):
    c, h = setup()
    if failure in ('foreign','unknown','nan','duplicate'):
        own = next(ch.chunk_id for ch in c.chunks if h.documents[ch.document_key].product_id == 'a')
        foreign = next(ch.chunk_id for ch in c.chunks if h.documents[ch.document_key].product_id == 'b')
        hits = [{'chunk_id':own,'score':1.0}]
        if failure == 'foreign': hits.append({'chunk_id':foreign,'score':.9})
        if failure == 'unknown': hits.append({'chunk_id':'unknown','score':.9})
        if failure == 'nan': hits[0]['score'] = float('nan')
        if failure == 'duplicate': hits *= 2
        h.index.search = lambda *a, **k: hits
    elif failure == 'model': h.embedder = SimpleNamespace(metadata={'wrong':'model'})
    elif failure == 'corpus': h.index.corpus = corpus([document('other','33333-3333')])
    elif failure == 'provider':
        original = h.provider
        def bad(pid):
            value = deepcopy(original(pid)); value['product_id'] = 'b'; return value
        h.provider = bad
    elif failure == 'down':
        def down(_): raise RuntimeError('Frozen release unavailable')
        h.provider = down
    result = h.retrieve('General evidence?', confirmed_product_id='a')
    assert result.status == 'insufficient_evidence' and not result.chunk_ids


def test_fusion_deterministic_and_no_ranked_gold_inference():
    assert fuse(['a','b'],['b','a']) == ['a','b']
    with pytest.raises(ValueError): fuse(['a','a'],['b'])
    c, h = setup(mode='rrf')
    first = h.retrieve('Original safety text?', confirmed_product_id='a')
    assert first.route == 'rrf_candidates' and first.chunk_ids
    assert first == h.retrieve('Original safety text?', confirmed_product_id='a')


@pytest.mark.parametrize('engine', ['numpy-test','faiss'])
def test_section_and_product_filter_before_ranking(engine):
    if engine == 'faiss': pytest.importorskip('faiss')
    c = corpus(); vectors = np.zeros((len(c.chunks),64), np.float32)
    docs = {document_key(d):d for d in c.documents}
    for row, ch in enumerate(c.chunks):
        target = docs[ch.document_key].product_id == 'a' and ch.section == 'contraindications'
        vectors[row,1 if target else 0] = 1
    class Query(MockEmbedder):
        def encode(self,texts,*,query=False):
            values = np.zeros((len(texts),64),np.float32); values[:,0] = 1; return values
    index = RetrievalIndex(c,vectors,Query.metadata,engine=engine)
    args = dict(confirmed_product_id='a',embedder=Query(),sections=('contraindications',))
    hits = index.search('question',**args)
    assert len(hits) == 5
    assert all(next(ch for ch in c.chunks if ch.chunk_id == hit['chunk_id']).section == 'contraindications' for hit in hits)
    assert all(docs[next(ch for ch in c.chunks if ch.chunk_id == hit['chunk_id']).document_key].product_id == 'a' for hit in hits)
    assert hits == index.search('question',**args)
    for bad in ([],['unknown'],['contraindications','contraindications']):
        with pytest.raises(ValueError): index.search('question',**{**args,'sections':bad})


def test_multiple_sections_are_all_or_nothing_and_interleaved():
    c, h = setup()
    result = h.retrieve('Contraindications and boxed warning?', confirmed_product_id='a')
    assert result.reason == 'section_absent' and not result.chunk_ids
    result = h.retrieve('Contraindications and drug interactions?', confirmed_product_id='a')
    assert [h.chunks[cid].section for cid in result.chunk_ids] == [
        'contraindications','drug_interactions','contraindications','drug_interactions','contraindications']


@pytest.mark.parametrize('change', ['version','release','membership'])
def test_live_source_metadata_inconsistency_blocks_sql_and_semantic(change):
    c, h = setup(); original = h.provider
    def bad(pid):
        value = deepcopy(original(pid))
        if change == 'version': value['evidence']['records'][0]['label_version'] = '999'
        elif change == 'release': value['release']['release_id'] = 'unrecognized-release'
        else: value['evidence']['records'] = []
        return value
    h.provider = bad
    for question in ('Contraindications?', 'General evidence?'):
        assert not h.retrieve(question,confirmed_product_id='a').chunk_ids


def test_evaluation_validates_annotations_and_separate_negative_denominators():
    import hashlib
    from app.agent.rag.corpus import digest
    from app.agent.rag.evaluation import Span
    from app.agent.rag.hybrid import Decision, policy_fingerprint
    from app.agent.rag.hybrid_evaluation import (HeldoutAnnotations, HeldoutQuestion,
                                               evaluate_decisions, validate_heldout)
    c, h = setup(); doc = next(d for d in c.documents if d.product_id == 'a')
    quote = doc.label.contraindications[:24]
    positive = HeldoutQuestion(case_id='positive',tags=['test'],ndc='11111-1111',
        question='Contraindications?',relevant_spans=[Span(source_record_id=doc.label.source_record_id,
        section='contraindications',start=0,end=24,text_sha256=hashlib.sha256(quote.encode()).hexdigest())],
        rationale='Source-only synthetic judgment.',group='explicit')
    missing = HeldoutQuestion(case_id='missing',tags=['test'],ndc='11111-1111',
        question='Boxed warning?',relevant_spans=[],missing_section='boxed_warning',
        rationale='Absent source section.',group='explicit',negative_kind='missing_section')
    unsupported = HeldoutQuestion(case_id='unsupported',tags=['test'],ndc='11111-1111',
        question='Evidence about migraine aura?',relevant_spans=[],rationale='No such topic in synthetic source.',
        group='semantic',negative_kind='unsupported_topic',absent_terms=['migraine'])
    a = HeldoutAnnotations(version='synthetic',annotation_method='synthetic',created_at='2026-10-23',
        policy_sha256=policy_fingerprint(),corpus_sha256=digest(c.model_dump(mode='json')),
        cases=[positive,missing,unsupported])
    report = evaluate_decisions(c,a,{'hybrid':lambda q,pid:h.retrieve(q.question,confirmed_product_id=pid)})
    summary = report['results']['hybrid']['summary']
    assert summary['recall_at_5'] == summary['missing_section_abstention_accuracy'] == 1
    assert summary['false_abstention_rate'] == 0
    # Phase 1D: Unsupported medical topic correctly abstains with empty candidates
    assert summary['unsupported_evidence_acceptance_rate'] == 0
    assert summary['all_negative_candidate_return_rate'] == 0
    assert summary['decision_reasons']['unsupported_topic'] == 1
    assert summary['positive_status_counts']['supported'] == 1
    assert summary['negative_status_counts']['insufficient_evidence'] == 2
    for update in [{'policy_sha256':'0'*64},{'corpus_sha256':'0'*64}]:
        with pytest.raises(ValueError):validate_heldout(c,a.model_copy(update=update))
    bad = unsupported.model_copy(update={'absent_terms':['Original']})
    with pytest.raises(ValueError):validate_heldout(c,a.model_copy(update={'cases':[bad]}))
    contradictory = positive.model_copy(update={'group':'semantic'})
    with pytest.raises(ValueError):validate_heldout(c,a.model_copy(update={'cases':[contradictory]}))
    with pytest.raises(ValueError):
        evaluate_decisions(c,a,{'bad':lambda q,pid:Decision('candidates','test',pid,chunk_ids=('unknown',))})


def test_unsupported_medical_concepts_abstain_closed():
    c, h = setup()
    # "migraine aura" has zero mentions in synthetic product 'a'
    result = h.retrieve('Does this medication prevent migraine aura?', confirmed_product_id='a')
    assert result.status == 'insufficient_evidence'
    assert result.reason == 'unsupported_topic'
    assert not result.chunk_ids
    assert not result.verified_answer


def test_candidate_only_never_promoted_to_verified_answer():
    c, h = setup()
    # Open-ended query with mock embedder where top score/terms do not verify full support
    result = h.retrieve('Original safety source text?', confirmed_product_id='a')
    assert result.status == 'candidate_only'
    assert result.route == 'semantic_candidates'
    assert result.chunk_ids
    assert not result.verified_answer
    assert result.confidence == 'uncalibrated'


def test_grounded_explicit_sections_are_supported():
    c, h = setup()
    # Explicit section query for admitted section produces supported evidence
    result = h.retrieve('What are the contraindications?', confirmed_product_id='a')
    assert result.status == 'supported'
    assert result.verified_answer is True
    assert result.confidence == 'calibrated'
    assert result.route == 'sql_explicit_sections'
    assert len(result.chunk_ids) == 5


def test_candidate_score_floor_fails_closed():
    c, h = setup()
    # If nearest neighbor score is below candidate_score_floor (0.60), fail closed
    class LowScoreEmbedder(MockEmbedder):
        def encode(self, texts, *, query=False):
            arr = np.zeros((len(texts), 64), np.float32)
            arr[:, 10] = 0.3  # Very low similarity
            return arr

    h.embedder = LowScoreEmbedder()
    h.index.metadata = LowScoreEmbedder.metadata
    result = h.retrieve('Original safety source text?', confirmed_product_id='a')
    assert result.status == 'insufficient_evidence'
    assert result.reason == 'insufficient_similarity'
    assert not result.chunk_ids
