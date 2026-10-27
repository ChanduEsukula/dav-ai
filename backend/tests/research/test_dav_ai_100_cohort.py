import csv
import hashlib
import json
import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import build_dav_ai_100_cohort as cohort


def artifact():
    path=ROOT/'data/cohorts/dav_ai_100_v1.json'
    if not path.is_file(): pytest.skip('Offline cohort artifact is not mounted')
    return json.loads(path.read_text())


def test_exactly_100_unique_ranks_names_and_version():
    a=artifact();rows=a['entries']
    assert len(rows)==100
    assert [r['rank'] for r in rows]==list(range(1,101))
    assert [r['display_name'] for r in rows]==cohort.RANKED_NAMES
    assert len(set(r['display_name'] for r in rows))==100
    assert all(r['display_name'].strip() for r in rows)
    assert {r['cohort_version'] for r in rows}=={'DAV_AI_100_V1'}
    assert a['cohort_version']=='DAV_AI_100_V1'
    assert hashlib.sha256(cohort.stable(cohort.RANKED_NAMES).encode()).hexdigest()==a['provenance']['ranking_sha256']


def test_flags_and_status_enums():
    rows=artifact()['entries']
    assert [r['rank'] for r in rows if r['is_combination']]==[15,31,68,74,76,78,90,91]
    for r in rows:
        assert r['is_combination']==(';' in r['display_name'])
        assert r['status'] in cohort.STATUSES
        assert r['mapping_confidence'] in cohort.CONFIDENCES
        assert r['component_count']==len(r['display_name'].split(';'))


def test_csv_json_semantic_equivalence_and_stable_serialization():
    artifact()
    if not (ROOT/'data/cohorts/dav_ai_100_v1.csv').is_file(): pytest.skip('Offline cohort CSV is not mounted')
    with (ROOT/'data/cohorts/dav_ai_100_v1.csv').open() as f:csv_rows=list(csv.DictReader(f))
    for c,r in zip(csv_rows,artifact()['entries'],strict=True):
        for key,value in c.items():
            expected=cohort.stable(r[key]) if isinstance(r[key],(list,dict,bool)) else str(r[key])
            assert value==expected
    assert cohort.stable({'b':[2,1],'a':True})=='{"a":true,"b":[2,1]}'


def test_combination_product_sets_are_complete_and_never_silent_collapse():
    for r in artifact()['entries']:
        if r['is_combination']:
            assert len(r['component_evidence'])==r['component_count']>1
            assert all(len(set(g))==r['component_count'] for g in r['product_ingredient_sets'])
            if r['status']=='UNRESOLVED':assert r['product_count']==0
    hydro=artifact()['entries'][30]
    assert hydro['ingredient_names']==['acetaminophen','hydrocodone']
    assert hydro['product_count']==0 and hydro['status']=='SUPPORTED'


def test_shared_name_and_extra_coingredient_are_not_silent_matches(monkeypatch):
    monkeypatch.setattr(cohort,'RANKED_NAMES',['A','A; B','A; Missing'])
    mapping={'ingredients':{'a':'a','b':'b'},'aliases':{'name':{'a':[['a'],['salt'],['a','extra']]}}}
    products=[{'source_id':'single','ingredient_ids':['a'],'product_ndcs':['1'],'rxcuis':[]},
              {'source_id':'combo','ingredient_ids':['a','b'],'product_ndcs':['2'],'rxcuis':[]},
              {'source_id':'extra','ingredient_ids':['a','b','extra'],'product_ndcs':['3'],'rxcuis':[]}]
    rows=cohort.map_cohort(mapping,products,{'a':'a','b':'b','salt':'salt','extra':'extra'})
    assert rows[0]['status']=='AMBIGUOUS' and rows[0]['product_source_ids']==['single']
    assert rows[1]['product_source_ids']==['combo']
    assert rows[2]['status']=='UNRESOLVED' and rows[2]['product_count']==0


def test_semaglutide_identity_and_no_regulatory_generalization():
    r=artifact()['entries'][13]
    assert r['status']=='VERIFIED'
    assert r['ingredient_ids']==['ingredient:aceb6dacee359207f1939f8b']
    assert r['product_count']==142
    assert all('No regulatory applicability inferred' in r['regulatory_scope'] for r in artifact()['entries'])


def test_source_provenance_hashes_and_no_database_open():
    p=artifact()['provenance']
    assert p['research_database_opened'] is False
    assert p['research_database_size_mtime_unchanged'] is True
    for name,digest in p['input_sha256'].items():
        if not (ROOT/name).is_file(): pytest.skip('Offline cohort provenance input is not mounted: '+name)
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
