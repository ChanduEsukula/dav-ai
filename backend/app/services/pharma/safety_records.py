"""Source-specific field extraction; absent upstream values stay absent."""
from datetime import datetime
from urllib.parse import urlencode
import json

SOURCES = {
    'labels': ('openfda_drug_label', 'https://api.fda.gov/drug/label.json'),
    'recalls': ('openfda_drug_enforcement', 'https://api.fda.gov/drug/enforcement.json'),
    'adverse_events': ('openfda_drug_event', 'https://api.fda.gov/drug/event.json'),
    'communications': ('fda_drug_safety_communications', 'https://www.fda.gov/drugs/drug-safety-and-availability/drug-safety-communications'),
}
TABLES = {
    'labels': ('drug_labels', 'drug_label_links', 'drug_label_id', 'effective_date'),
    'recalls': ('recalls', 'drug_recall_links', 'recall_id', 'recall_initiation_date'),
    'adverse_events': ('adverse_events', 'drug_adverse_event_links', 'adverse_event_id', 'received_date'),
    'communications': ('safety_communications', 'drug_safety_communication_links', 'safety_communication_id', 'published_date'),
}


def text(value):
    if isinstance(value, list):
        return '\n\n'.join(v.strip() for v in value if isinstance(v, str) and v.strip()) or None
    return value.strip() or None if isinstance(value, str) else None


def date(value):
    if not value:
        return None
    for fmt in ('%Y%m%d', '%Y-%m-%d'):
        try:
            return datetime.strptime(str(value)[:10], fmt).date()
        except ValueError:
            pass
    return None


def normalize_record(kind, raw, run_id):
    source, endpoint = SOURCES[kind]
    if kind == 'labels':
        identifier, key = text(raw.get('id')), 'id'
        of = raw.get('openfda') or {}
        title = text(of.get('brand_name')) or text(of.get('generic_name')) or text(raw.get('spl_product_data_elements'))
        result = dict(title=title, label_set_id=text(raw.get('set_id')),
                      label_version=str(raw['version']) if raw.get('version') is not None else None,
                      effective_date=date(raw.get('effective_time')))
        for field in ('boxed_warning', 'warnings_and_precautions', 'contraindications',
                      'drug_interactions', 'indications_and_usage', 'dosage_and_administration'):
            result[field] = text(raw.get(field))
        if not result['warnings_and_precautions']:
            result['warnings_and_precautions'] = text(raw.get('warnings'))
    elif kind == 'recalls':
        identifier, key = text(raw.get('recall_number')), 'recall_number'
        result = {field: text(raw.get(field)) for field in (
            'recall_number', 'event_id', 'product_description', 'reason_for_recall',
            'classification', 'recalling_firm', 'distribution_pattern')}
        if not result['product_description'] or not result['reason_for_recall']:
            raise ValueError('Recall missing required description')
        result.update(reported_status=text(raw.get('status')),
                      recall_initiation_date=date(raw.get('recall_initiation_date')),
                      report_date=date(raw.get('report_date')), lot_information=text(raw.get('code_info')))
    elif kind == 'adverse_events':
        identifier, key = text(raw.get('safetyreportid')), 'safetyreportid'
        patient = raw.get('patient') or {}
        # Preserve drug mentions and roles, not patient entities or causal pairs.
        result = dict(report_version=str(raw['safetyreportversion']) if raw.get('safetyreportversion') is not None else None,
                      received_date=date(raw.get('receivedate')), last_received_date=date(raw.get('receiptdate')),
                      serious={'1': True, '2': False}.get(str(raw.get('serious'))),
                      seriousness_details={k: v for k, v in raw.items() if k.startswith('seriousness')},
                      reported_drugs=patient.get('drug') or [],
                      reactions=list(dict.fromkeys(r['reactionmeddrapt'] for r in patient.get('reaction', [])
                                                   if isinstance(r.get('reactionmeddrapt'), str))),
                      country=text(raw.get('occurcountry')) or text(raw.get('primarysourcecountry')))
    else:
        raise ValueError('Unknown openFDA source')
    if not identifier:
        raise ValueError('Missing original source record ID')
    result.update(source=source, source_record_id=identifier,
                  source_url=endpoint + '?' + urlencode({'search': key + ':' + json.dumps(identifier), 'limit': 1}),
                  source_updated_at=None, ingestion_run_id=run_id, raw_json=raw)
    return result
