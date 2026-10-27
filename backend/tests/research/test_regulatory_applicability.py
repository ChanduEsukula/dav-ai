import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from regulatory_applicability import classify, product_index


def product(sid='p', ingredients=None, ndc='1', rx='r'):
    return {'source_id':sid,'ingredient_ids':ingredients or ['a'],'product_ndcs':[ndc], 'package_ndcs':[ndc+'-1'],'rxcuis':[rx]}

@pytest.mark.parametrize('kind',['labels','recalls'])
def test_exact_ndc_and_package_scoped_evidence(kind):
    for key,value in [('product_ndc','1'),('package_ndc','1-1')]:
        r=classify(kind,'a',{'openfda':{key:[value]}},product_index([product()]))
        assert r['classification']=='EXACT_PRODUCT' and r['scope']=='PRODUCT-SPECIFIC'
        assert r['ingredient_wide'] is False

@pytest.mark.parametrize('kind',['labels','recalls'])
def test_combination_never_generalized(kind):
    r=classify(kind,'a',{'openfda':{'product_ndc':['1']}},product_index([product(ingredients=['a','b'])]))
    assert r['classification']=='COMBINATION_PRODUCT' and not r['ingredient_wide']
    assert r['products'][0]['ingredient_ids']==['a','b']


def test_shared_ingredient_does_not_expand_product_scope():
    r=classify('labels','a',{'openfda':{'product_ndc':['1']}},product_index([product(),product('p2',ndc='2')]))
    assert [p['source_id'] for p in r['products']]==['p']


def test_shared_rxcui_is_ambiguous():
    r=classify('labels','a',{'openfda':{'rxcui':['r']}},product_index([product(),product('p2',ndc='2')]))
    assert r['classification']=='AMBIGUOUS' and r['scope']=='UNKNOWN'


def test_semaglutide_report_name_without_identifiers_is_not_product_identity():
    r=classify('labels','a',{'medicinalproduct':'WEGOVY','openfda':{'brand_name':['WEGOVY']}},product_index([product()]))
    assert r['classification']=='INGREDIENT_SUPPORTED_PRODUCT_UNKNOWN' and not r['products']


def test_acetaminophen_combination_fanout_stays_per_product():
    products=[product(),product('codeine',['a','c'],'2'),product('oxycodone',['a','o'],'3')]
    r=classify('recalls','a',{'openfda':{'product_ndc':['2']}},product_index(products))
    assert [p['source_id'] for p in r['products']]==['codeine']


def test_identifier_conflict_and_wrong_ingredient():
    index=product_index([product()])
    assert classify('labels','a',{'openfda':{'product_ndc':['1'],'rxcui':['wrong']}},index)['classification']=='AMBIGUOUS'
    assert classify('labels','b',{'openfda':{'product_ndc':['1']}},index)['classification']=='NOT_APPLICABLE'


def test_missing_source_is_unknown():
    r=classify('recalls','a',None,product_index([product()]))
    assert r['scope']=='UNKNOWN' and r['classification']=='INGREDIENT_ASSOCIATED_ONLY'
