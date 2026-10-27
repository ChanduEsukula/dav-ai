"""Exact source identifiers and whole normalized names; never link from query text."""
from app.services.pharma.normalization import normalize_name, resolve_drug


class CatalogIndex:
    def __init__(self, drugs):
        self.drugs = drugs

    def find_by_rxcui(self, value):
        return [d for d in self.drugs if d['rxcui'] == value]

    def find_by_ndc(self, value):
        return [d for d in self.drugs if value in d['product_ndcs'] or value in d['package_ndcs']]

    def find_by_normalized_name(self, value):
        return [d for d in self.drugs if normalize_name(value) in d['normalized_names']]


def values(obj, key):
    value = obj.get(key) or []
    return [v for v in value if isinstance(v, str) and v.strip()] if isinstance(value, list) else []


def match_mentions(index, kind, raw):
    mentions = (raw.get('patient') or {}).get('drug', []) if kind == 'adverse_events' else [raw]
    found = {}
    for mention in mentions:
        of = mention.get('openfda') or {}
        rxcuis = values(of, 'rxcui')
        ndcs = values(of, 'product_ndc') + values(of, 'package_ndc')
        names = values(of, 'generic_name') + values(of, 'brand_name')
        if kind == 'adverse_events' and isinstance(mention.get('medicinalproduct'), str):
            names.append(mention['medicinalproduct'])
        # An explicit list of NDCs can legitimately scope a label/recall to many products.
        # Only individually unambiguous identifiers become links.
        matched = {}
        for ndc in sorted(set(ndcs)):
            result = resolve_drug(index, ndc=ndc)
            if result.drug:
                if rxcuis and result.drug['rxcui'] and result.drug['rxcui'] not in rxcuis:
                    continue
                method = 'rxcui' if result.drug['rxcui'] in rxcuis and len(index.find_by_rxcui(result.drug['rxcui'])) == 1 else 'ndc'
                value = result.drug['rxcui'] if method == 'rxcui' else ndc
                matched[str(result.drug['id'])] = (result.drug['id'], method, value)
        if not ndcs:
            for rxcui in sorted(set(rxcuis)):
                result = resolve_drug(index, rxcui=rxcui)
                if result.drug:
                    matched[str(result.drug['id'])] = (result.drug['id'], 'rxcui', rxcui)
        # Do not override explicit but unresolved identifiers with a bare product name.
        if not ndcs and not rxcuis:
            for name in sorted(set(names)):
                result = resolve_drug(index, name=name)
                if result.drug:
                    matched[str(result.drug['id'])] = (result.drug['id'], 'name', name)
        found.update(matched)
    return [found[key] for key in sorted(found)]
