"""Conservative ingredient/formulation/product hierarchy from the official NDC snapshot."""
from collections import defaultdict
import gzip
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from app.research.bulk import norm, fingerprint, texts, now


def snapshot(root,kind):
    return Path(json.loads((Path(root)/(kind+'-latest.json')).read_text())['snapshot_path'])


def records(root,kind):
    for file in sorted(snapshot(root,kind).glob('files/quarter=*/*/'+kind+'.parquet')):
        if file.parent.name.endswith('.partial') or not (file.parent/'receipt.json').exists():continue
        for batch in pq.ParquetFile(file).iter_batches(batch_size=500):
            yield from batch.to_pylist()


def build_identity(root):
    root=Path(root);out=root/'identity';out.mkdir(exist_ok=True)
    ingredients={};formulations={};products=[];aliases=defaultdict(set)
    raw_count=0;missing=0
    source_snapshot=json.loads((snapshot(root,'ndc')/'snapshot.json').read_text())
    seen=set()
    for row in records(root,'ndc'):
        raw_count+=1
        r=json.loads(row['raw_json']);source_id=r['product_id']
        if source_id in seen:raise ValueError('Duplicate NDC source product identity')
        seen.add(source_id)
        active=r.get('active_ingredients') or []
        names=sorted({norm(i.get('name')) for i in active if isinstance(i,dict) and norm(i.get('name'))})
        complete=bool(names) and len(active)>0 and all(isinstance(i,dict) and norm(i.get('name')) for i in active)
        named_ids=['ingredient:'+fingerprint(n)[:24] for n in names] if complete else []
        ids=tuple(sorted(named_ids))
        for name,identifier in zip(names,named_ids):
            ingredients[identifier]={'ingredient_id':identifier,'canonical_name':name,'source':'openfda_ndc_directory',
                'identity_rule':'exact whitespace/case normalization; salts not collapsed',
                'observed_at':source_snapshot['observed_at']}
        strength=sorted((norm(i.get('name')),norm(i.get('strength'))) for i in active if isinstance(i,dict))
        form=norm(r.get('dosage_form'));routes=sorted(norm(v) for v in texts(r.get('route')))
        formulation_id=None
        if complete and all(s for _,s in strength) and form and routes:
            formulation_id='formulation:'+fingerprint([strength,form,routes])[:24]
            formulations[formulation_id]={'formulation_id':formulation_id,'ingredient_ids':list(ids),
                'strengths_json':json.dumps(strength),'dosage_form':form,'routes':routes}
        o=r.get('openfda') or {}
        product_ndcs=texts([r.get('product_ndc')]);packages=texts([p.get('package_ndc') for p in r.get('packaging',[])])
        names_alias=texts([r.get('generic_name'),r.get('brand_name'),r.get('brand_name_base')])
        if ids:
            for kind,values in [('rxcui',texts(o.get('rxcui'))),('ndc',product_ndcs+packages),('name',names_alias)]:
                for value in values:aliases[(kind,norm(value))].add(ids)
        else:missing+=1
        products.append({'source_id':source_id,'formulation_id':formulation_id,'ingredient_ids':list(ids),
            'generic_name':r.get('generic_name'),'brand_name':r.get('brand_name'),'labeler_name':r.get('labeler_name'),
            'product_ndcs':product_ndcs,'package_ndcs':packages,'rxcuis':texts(o.get('rxcui')),
            'source_url':row['source_url'],'observed_at':row['observed_at']})
    for name,rows in [('ingredients',list(ingredients.values())),('formulations',list(formulations.values())),('products',products)]:
        pq.write_table(pa.Table.from_pylist(rows),out/(name+'.parquet'),compression='zstd')
    encoded={kind:{} for kind in ['rxcui','ndc','name']}
    for (kind,value),groups in aliases.items():encoded[kind][value]=[list(g) for g in sorted(groups)]
    mapping={'aliases':encoded,'ingredients':{v['canonical_name']:k for k,v in ingredients.items()},
             'observed_at':source_snapshot['observed_at'],'source_dataset_key':source_snapshot['dataset_key']}
    with gzip.open(out/'mapping.json.gz','wt') as f:json.dump(mapping,f,sort_keys=True)
    result={'raw_product_records':raw_count,'canonical_ingredients':len(ingredients),'formulations':len(formulations),
        'marketed_products':len(products),'unique_brand_names':len({norm(p['brand_name']) for p in products if norm(p['brand_name'])}),
        'unique_ndc_products':len({v for p in products for v in p['product_ndcs']}),
        'unique_ndc_packages':len({v for p in products for v in p['package_ndcs']}),
        'resolved_products':len(products)-missing,'unresolved_products':missing,
        'products_without_complete_formulation':sum(p['formulation_id'] is None for p in products),
        'ambiguous_aliases':sum(len(groups)>1 for groups in aliases.values()),'mapping_hash':fingerprint(mapping),
        'observed_at':source_snapshot['observed_at'],'created_at':now()}
    (out/'summary.json').write_text(json.dumps(result,indent=2));return result


class IdentityIndex:
    def __init__(self,mapping):self.mapping=mapping

    @classmethod
    def load(cls,root):
        with gzip.open(Path(root)/'identity/mapping.json.gz','rt') as f:return cls(json.load(f))

    def resolve(self,mention):
        aliases=self.mapping['aliases'];signals=[];unknown=False
        for kind,fields in [('rxcui',['rxcui']),('ndc',['product_ndc','package_ndc'])]:
            for field in fields:
                for value in mention.get(field) or []:
                    groups=aliases[kind].get(norm(value))
                    if not groups:unknown=True
                    else:signals.append({tuple(g) for g in groups})
        substances=mention.get('substance_name') or []
        if substances:
            resolved=[self.mapping['ingredients'].get(norm(s)) for s in substances]
            if all(resolved):signals.append({tuple(sorted(set(resolved)))})
            else:unknown=True
        # An unknown identifier is not bypassed through a brand/generic guess.
        if unknown:return [],'unresolved_identifier'
        if not signals:
            for field in ['generic_name','brand_name']:
                for value in mention.get(field) or []:
                    groups=aliases['name'].get(norm(value))
                    if groups:signals.append({tuple(g) for g in groups})
            if not signals:
                groups=aliases['name'].get(norm(mention.get('medicinalproduct')))
                if groups:signals.append({tuple(g) for g in groups})
        if not signals:return [],'unresolved_name'
        candidates=set.intersection(*signals)
        if len(candidates)!=1:return [],'conflicting_or_ambiguous'
        return list(next(iter(candidates))),'exact_source_identity'


def publish_application_products(root):
    """Add official source products without replacing existing UUIDs or evidence."""
    from psycopg import sql
    from psycopg.types.json import Jsonb
    from app.db.pharma.connection import connect
    from app.db.pharma.drug_repository import FIELDS
    from app.db.pharma.ingestion_run_repository import IngestionRunRepository
    from app.services.pharma.ndc_ingestion import normalize_ndc_record,SOURCE
    runs=IngestionRunRepository();run=runs.start(SOURCE,{'mode':'official_bulk','identity_snapshot':str(snapshot(root,'ndc')),
        'curated_cohort':'backend/app/config/drug_catalog.json remains regression/demo only'})
    columns=sql.SQL(',').join(map(sql.Identifier,FIELDS))
    updates=sql.SQL(',').join(sql.SQL('{}=EXCLUDED.{}').format(sql.Identifier(f),sql.Identifier(f)) for f in FIELDS if f not in ('source','source_record_id'))
    query=sql.SQL('INSERT INTO pharma.drugs ({}) VALUES ({}) ON CONFLICT(source,source_record_id) DO UPDATE SET {}').format(columns,sql.SQL(',').join(sql.Placeholder() for _ in FIELDS),updates)
    counts={'fetched':0,'inserted':0,'updated':0,'unresolved':0,'failed':0}
    rejects=[]
    with connect() as conn:
        existing={r['source_record_id'] for r in conn.execute('SELECT source_record_id FROM pharma.drugs WHERE source=%s',(SOURCE,))}
        batch=[]
        for row in records(root,'ndc'):
            counts['fetched']+=1
            try:
                drug=normalize_ndc_record(json.loads(row['raw_json']),run)
            except (ValueError,TypeError,KeyError,AttributeError) as exc:
                counts['unresolved']+=1;rejects.append({'source_id':row['source_id'],'reason':str(exc)});continue
            batch.append([Jsonb(drug[f]) if f=='raw_json' else drug[f] for f in FIELDS])
            counts['updated' if row['source_id'] in existing else 'inserted']+=1
            if len(batch)==500:
                with conn.cursor() as c:c.executemany(query,batch)
                batch=[]
        if batch:
            with conn.cursor() as c:c.executemany(query,batch)
    runs.finish(run,status='partial' if rejects else 'succeeded',counts=counts,coverage={'raw_records_preserved_in_research':True,'unresolved':rejects})
    (Path(root)/'identity/application-publish.json').write_text(json.dumps(counts,indent=2));return counts
