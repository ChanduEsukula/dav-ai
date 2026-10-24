"""Isolated synthetic regression tests. No release access, downloads or generation."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

np = pytest.importorskip('numpy', reason='Optional offline RAG experiment requires numpy')
from app.agent.evaluation.fixtures import synthetic_release_metadata
from app.agent.research_contracts import LabelRecord, ReleaseInfo
from app.agent.rag.corpus import (Corpus, Document, Product, LABEL_FIELDS, canonical, digest,
    document_key, external_output, load_corpus, make_chunks, save_corpus, split_section)
from app.agent.rag.embeddings import LocalBGE, MockEmbedder, normalize
from app.agent.rag.evaluation import (Annotations, Question, SQLBaseline, Span, evaluate, metrics, relevant_chunks)
from app.agent.rag.index import RetrievalIndex


def document(pid='a', ndc='11111-1111', text=None):
    text = text or ('Original first paragraph.\n\n' + 'Original safety source text with words. ' * 14)
    release = synthetic_release_metadata()
    label = dict(id='label1', label_set_id='set1', label_version='1', effective_date='2025-01-01',
        applicability_class='EXACT_PRODUCT', evidence_scope='PRODUCT', selection_status='SELECTED_STORED',
        match_method='EXACT_NDC', matched_value=ndc, source='openfda_drug_label', source_record_id='source-record-1',
        source_url='https://api.fda.gov/drug/label.json', section_states={})
    for field, name in LABEL_FIELDS.items():
        value = text if field in ('contraindications', 'drug_interactions') else None
        label[field] = value
        label['section_states'][name] = dict(text=value, field_present=value is not None,
            state='READY' if value is not None else 'UNAVAILABLE', reason_code='SYNTHETIC')
    return Document(product_id=pid, formulation_id='formulation-'+pid, product_ndcs=[ndc],
        strength='10 mg', dosage_form='TABLET', routes=['ORAL'], active_ingredients=['synthetic ingredient'],
        package_ndcs=[ndc+'-01'], brand_names=['Similar brand'], source_id='source1',
        source_snapshot_date='2025-09-25', release=ReleaseInfo.model_validate({k:release[k] for k in ReleaseInfo.model_fields}),
        label=LabelRecord.model_validate(label))


def corpus(documents=None):
    documents = documents if documents is not None else [document(), document('b', '22222-2222')]
    products = [Product(product_id=d.product_id, formulation_id=d.formulation_id, product_ndcs=d.product_ndcs,
                        brand_names=d.brand_names, label_coverage={'state':'READY'}) for d in documents]
    products.append(Product(product_id='missing', formulation_id='missing-form', product_ndcs=['99999-9999'],
                            brand_names=['Missing'], label_coverage={'state':'UNKNOWN'}))
    return Corpus(release_artifact_sha256='0'*64,max_chars=128, products=products, documents=sorted(documents, key=document_key),
                  chunks=make_chunks(documents,128))


def test_lossless_section_boundaries_ids_and_order():
    c=corpus()
    assert c.chunks == make_chunks(list(reversed(c.documents)),128)
    assert len({ch.chunk_id for ch in c.chunks}) == len(c.chunks)
    for d in c.documents:
        for field in LABEL_FIELDS:
            chunks=[ch for ch in c.chunks if ch.document_key==document_key(d) and ch.section==field]
            assert ''.join(ch.text for ch in chunks) == (getattr(d.label,field) or '')
            assert [ch.ordinal for ch in chunks] == list(range(len(chunks)))
            assert all(len(ch.text)<=128 and ch.text==getattr(d.label,field)[ch.start:ch.end] for ch in chunks)
    assert list(split_section('first paragraph\n\n'+'x'*140,128))[0][2]=='first paragraph\n\n'
    assert ''.join(part[2] for part in split_section('x'*300,128))=='x'*300
    assert document_key(c.documents[0]) != document_key(c.documents[1])


@pytest.mark.parametrize('change', ['text','section','chunk_id','offset','order','binding','source_url','admission','date','state'])
def test_rejects_invalid_metadata(change):
    raw=corpus().model_dump(mode='json')
    if change=='text':raw['chunks'][0]['text']='fabricated'
    elif change=='section':raw['chunks'][0]['section']='another_section'
    elif change=='chunk_id':raw['chunks'][0]['chunk_id']='bad'
    elif change=='offset':raw['chunks'][0]['start']=1
    elif change=='order':raw['chunks'].reverse()
    elif change=='binding':raw['documents'][0]['product_ndcs']=['33333-3333']
    elif change=='source_url':raw['documents'][0]['label']['source_url']='https://evil.example'
    elif change=='admission':raw['documents'][0]['label']['applicability_class']='INGREDIENT_CONTEXT'
    elif change=='date':raw['documents'][0]['source_snapshot_date']='2024-01-01'
    elif change=='state':raw['documents'][0]['label']['section_states']['contraindications']['state']='UNKNOWN'
    with pytest.raises(ValueError):Corpus.model_validate_json(json.dumps(raw))


def test_deterministic_read_only_roundtrip_and_no_overwrite(tmp_path):
    c=corpus(); embedder=MockEmbedder()
    index=RetrievalIndex.build(c,embedder,engine='numpy-test')
    first=index.save(tmp_path/'first');second=index.save(tmp_path/'second')
    assert first==second
    assert (tmp_path/'first'/'vectors.npy').read_bytes()==(tmp_path/'second'/'vectors.npy').read_bytes()
    before={p.name:p.read_bytes() for p in (tmp_path/'first').iterdir()}
    loaded=RetrievalIndex.load(tmp_path/'first')
    assert not loaded.vectors.flags.writeable
    with pytest.raises(ValueError):loaded.vectors[0,0]=1
    args=dict(confirmed_product_id='a',embedder=embedder)
    assert loaded.search('safety words',**args)==index.search('safety words',**args)
    assert before=={p.name:p.read_bytes() for p in (tmp_path/'first').iterdir()}
    with pytest.raises(FileExistsError):index.save(tmp_path/'first')
    save_corpus(c,tmp_path/'corpus.json')
    assert load_corpus(tmp_path/'corpus.json')==c
    with pytest.raises(ValueError):external_output(Path(__file__).resolve().parents[3]/'data'/'not-allowed')


@pytest.mark.parametrize('file',['corpus.json','vectors.npy','manifest.json'])
def test_corrupt_artifact_rejected(tmp_path,file):
    index=RetrievalIndex.build(corpus(),MockEmbedder(),engine='numpy-test')
    index.save(tmp_path/'index')
    path=tmp_path/'index'/file
    path.chmod(0o600)
    path.write_bytes(path.read_bytes()+b'bad')
    with pytest.raises(ValueError):RetrievalIndex.load(tmp_path/'index')


def test_product_filter_before_ranking_not_global_top_k():
    c=corpus();dim=64
    vectors=np.zeros((len(c.chunks),dim),np.float32)
    docs={document_key(d):d for d in c.documents}
    # Every foreign product outranks the target globally; the target still gets 5 hits.
    for row,ch in enumerate(c.chunks):
        vectors[row,0 if docs[ch.document_key].product_id=='b' else 1]=1
    class Query(MockEmbedder):
        def encode(self,texts,*,query=False):
            result=np.zeros((len(texts),dim),np.float32);result[:,0]=1;return result
    index=RetrievalIndex(c,vectors,Query.metadata,engine='numpy-test')
    hits=index.search('query',confirmed_product_id='a',embedder=Query())
    assert len(hits)==5
    ids={ch.chunk_id for ch in c.chunks if docs[ch.document_key].product_id=='a'}
    assert all(hit['chunk_id'] in ids for hit in hits)
    assert hits==index.search('query',confirmed_product_id='a',embedder=Query())
    assert [h['chunk_id'] for h in hits]==sorted(ids)[:5]


def test_empty_evidence_unknown_product_model_mismatch_and_invalid_vectors():
    c=corpus([]);index=RetrievalIndex.build(c,MockEmbedder(),engine='numpy-test')
    assert index.search('anything',confirmed_product_id='missing',embedder=MockEmbedder())==[]
    with pytest.raises(ValueError):index.search('anything',confirmed_product_id='foreign',embedder=MockEmbedder())
    class Changed(MockEmbedder):metadata={**MockEmbedder.metadata,'model':'different'}
    with pytest.raises(ValueError):index.search('anything',confirmed_product_id='missing',embedder=Changed())
    for bad in [np.zeros((1,64)), np.full((1,64),np.nan), np.ones((1,3))]:
        with pytest.raises(ValueError):normalize(bad,64)
    with pytest.raises(ValueError):RetrievalIndex(c,np.empty((0,64),np.float32),{'dimension':0},engine='numpy-test')


def test_local_bge_never_accepts_remote_model_identifier(tmp_path):
    with pytest.raises(ValueError):LocalBGE('BAAI/bge-small-en-v1.5')
    (tmp_path/'config.json').write_text('{}')
    from app.agent.rag import embeddings
    from unittest.mock import Mock
    model=Mock();model.get_sentence_embedding_dimension.return_value=384
    model.max_seq_length=512;model.tokenizer.return_value={'input_ids':[[1]*513]}
    loader=Mock(return_value=model)
    torch=SimpleNamespace(manual_seed=lambda _:None,set_num_threads=lambda _:None,use_deterministic_algorithms=lambda _:None)
    from pytest import MonkeyPatch
    with MonkeyPatch.context() as patch:
        patch.setenv('HF_HUB_OFFLINE','0')
        patch.setenv('TRANSFORMERS_OFFLINE','0')
        patch.setattr(embeddings,'compatibility',lambda:{'semantic_ready':True,'packages':{}})
        patch.setitem(sys.modules,'sentence_transformers',SimpleNamespace(SentenceTransformer=loader))
        patch.setitem(sys.modules,'torch',torch)
        embedder=LocalBGE(tmp_path)
        assert loader.call_args.kwargs['local_files_only'] is True
        assert loader.call_args.kwargs['trust_remote_code'] is False
        with pytest.raises(ValueError,match='token budget'):embedder.encode(['long'])
        model.encode.assert_not_called()


def test_judgments_metrics_and_sql_baselines():
    c=corpus();d=next(d for d in c.documents if d.product_id=='a')
    text=d.label.contraindications[:24]
    q=Question(case_id='q',tags=['contraindications'],ndc=d.product_ndcs[0],
        question='What is in the contraindications section?',rationale='Synthetic source judgment',
        relevant_spans=[Span(source_record_id=d.label.source_record_id,section='contraindications',start=0,end=24,
                             text_sha256=hashlib.sha256(text.encode()).hexdigest())])
    gold=relevant_chunks(c,q)
    assert len(gold)==1
    hit=next(iter(gold))
    assert metrics(['irrelevant',hit],gold)==dict(recall_at_5=1,precision_at_5=.2,mrr_at_5=.5,empty_evidence_correct=None)
    assert metrics([],set())['empty_evidence_correct'] is True
    assert metrics(['other'],set())['empty_evidence_correct'] is False
    with pytest.raises(ValueError):metrics([hit,hit],gold)
    bad=q.model_copy(update={'relevant_spans':[q.relevant_spans[0].model_copy(update={'text_sha256':'0'*64})]})
    with pytest.raises(ValueError):relevant_chunks(c,bad)
    def provider(pid):
        doc=next(d for d in c.documents if d.product_id==pid)
        return dict(product_id=pid,product_ndcs=doc.product_ndcs,release=doc.release.model_dump(),
                    evidence={'records':[doc.label.model_dump()]})
    sql=SQLBaseline(c,keyword_sections=True,provider=provider)
    annotations=Annotations(version='synthetic',annotation_method='synthetic',cases=[q])
    report=evaluate(c,annotations,{'sql':lambda case,_:sql.search(case)})
    assert report['results']['sql']['summary']['product_identity_accuracy']==1
    assert report['results']['sql']['summary']['recall_at_5']==1
    missing=q.model_copy(update={'case_id':'missing','relevant_spans':[],'missing_section':'boxed_warning'})
    assert relevant_chunks(c,missing)==set()
    contradictory=missing.model_copy(update={'missing_section':'contraindications'})
    with pytest.raises(ValueError):relevant_chunks(c,contradictory)


def test_faiss_matches_exact_cosine_and_filters_products(tmp_path):
    pytest.importorskip('faiss',reason='FAISS not installed; real vector engine remains unverified')
    c=corpus();embedder=MockEmbedder()
    faiss=RetrievalIndex.build(c,embedder)
    numpy=RetrievalIndex.build(c,embedder,engine='numpy-test')
    for pid in ['a','b','missing']:
        actual=faiss.search('safety source',confirmed_product_id=pid,embedder=embedder)
        expected=numpy.search('safety source',confirmed_product_id=pid,embedder=embedder)
        assert [h['chunk_id'] for h in actual]==[h['chunk_id'] for h in expected]
        assert np.allclose([h['score'] for h in actual],[h['score'] for h in expected],atol=1e-6)
    faiss.save(tmp_path/'faiss')
    assert RetrievalIndex.load(tmp_path/'faiss').search('safety source',confirmed_product_id='a',embedder=embedder)==faiss.search('safety source',confirmed_product_id='a',embedder=embedder)


def test_fixed_annotations_cover_required_categories_without_embedded_source_text():
    path=Path(__file__).resolve().parents[2]/'app'/'agent'/'rag'/'questions_v1.json'
    annotations=Annotations.model_validate_json(path.read_bytes())
    assert len(annotations.cases)==21
    tags={tag for case in annotations.cases for tag in case.tags}
    assert {'contraindications','boxed_warning','drug_interactions','adverse_reactions',
            'missing_evidence','similar_product_names','combination_formulations','paraphrase'} <= tags
    assert all(span.text_sha256 and span.end>span.start for case in annotations.cases for span in case.relevant_spans)


def test_cli_refuses_mock_semantic_comparison(tmp_path):
    from app.agent.rag.cli import main
    c=corpus()
    save_corpus(c,tmp_path/'corpus.json')
    RetrievalIndex.build(c,MockEmbedder(),engine='numpy-test').save(tmp_path/'index')
    annotations=Path(__file__).resolve().parents[2]/'app'/'agent'/'rag'/'questions_v1.json'
    with pytest.raises(SystemExit) as stopped:
        main(['evaluate','--corpus',str(tmp_path/'corpus.json'),'--index',str(tmp_path/'index'),
              '--annotations',str(annotations),'--out',str(tmp_path/'report.json')])
    assert stopped.value.code==2
    assert not (tmp_path/'report.json').exists()
