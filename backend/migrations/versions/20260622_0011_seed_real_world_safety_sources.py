"""Seed RealWorldSafety source registry rows.

Revision ID: 20260622_0011
Revises: 20260616_0010
Create Date: 2026-06-22
"""

from alembic import op


revision = "20260622_0011"
down_revision = "20260616_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        insert into source_registry (
            source_id,
            source_name,
            endpoint,
            module,
            description,
            update_cadence
        )
        values
            (
                'rxnorm_rxnav_api',
                'RxNorm/RxNav API',
                'https://rxnav.nlm.nih.gov/REST',
                'RealWorldSafety',
                'U.S. National Library of Medicine RxNorm drug terminology source used for drug-name normalization and RXCUI reference lookup.',
                'NLM RxNorm releases and RxNav API updates'
            ),
            (
                'dailymed_spl_api',
                'DailyMed SPL API',
                'https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json',
                'RealWorldSafety',
                'U.S. National Library of Medicine DailyMed Structured Product Label source for official drug label references.',
                'DailyMed SPL label updates'
            ),
            (
                'openfda_drug_label',
                'openFDA Drug Label API',
                'https://api.fda.gov/drug/label.json',
                'RealWorldSafety',
                'Official openFDA drug label records for active ingredients, warnings, dosage, and usage sections.',
                'Source-dependent FDA drug label updates'
            ),
            (
                'openfda_ndc_directory',
                'openFDA NDC Directory API',
                'https://api.fda.gov/drug/ndc.json',
                'RealWorldSafety',
                'Official openFDA National Drug Code directory records for drug identity, labeler, active ingredients, dosage form, route, product NDC, and packaging reference. This is a reference source, not a recall source.',
                'Source-dependent FDA NDC directory updates'
            ),
            (
                'openfda_device_enforcement',
                'openFDA Device Enforcement API',
                'https://api.fda.gov/device/enforcement.json',
                'RealWorldSafety',
                'FDA medical device recall enforcement records from openFDA.',
                'Source-dependent FDA device enforcement updates'
            ),
            (
                'openfda_device_event',
                'openFDA Device Event API',
                'https://api.fda.gov/device/event.json',
                'RealWorldSafety',
                'FDA medical device adverse-event reports from openFDA. These are signal reports, not recalls or proof of causation.',
                'Source-dependent FDA device event updates'
            ),
            (
                'fda_recalls_market_withdrawals_safety_alerts',
                'FDA Recalls, Market Withdrawals & Safety Alerts',
                'https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts',
                'RealWorldSafety',
                'Public FDA recall, market withdrawal, and safety alert notices visible on FDA.gov, including notices that may not appear in openFDA enforcement APIs.',
                'FDA public notice page updates as recalls, market withdrawals, and safety alerts are posted'
            ),
            (
                'cpsc_recalls_api',
                'CPSC Recalls API',
                'https://www.saferproducts.gov/RestWebServices/Recall',
                'RealWorldSafety',
                'Consumer Product Safety Commission recall records for home goods, electronics, batteries, scooters, toys, baby products, furniture, appliances, and other consumer products.',
                'CPSC recall API updates as public recalls are published'
            ),
            (
                'nhtsa_vpic_vin_decoder_api',
                'NHTSA vPIC VIN Decoder API',
                'https://vpic.nhtsa.dot.gov/api/',
                'RealWorldSafety',
                'NHTSA vPIC vehicle decoder used to turn VIN input into make, model, and model year before recall lookup.',
                'NHTSA vPIC public API updates as vehicle product information is refreshed'
            ),
            (
                'nhtsa_recalls_api_datasets',
                'NHTSA Recalls API / datasets',
                'https://api.nhtsa.gov/recalls/recallsByVehicle',
                'RealWorldSafety',
                'NHTSA vehicle recall records by make, model, and model year for vehicle safety checks.',
                'NHTSA recall data updates as campaigns and safety notices are published'
            )
        on conflict (source_id) do update set
            source_name = excluded.source_name,
            endpoint = excluded.endpoint,
            module = excluded.module,
            description = excluded.description,
            update_cadence = excluded.update_cadence,
            updated_at = now()
        """
    )


def downgrade() -> None:
    op.execute(
        """
        delete from source_registry
        where source_id in (
            'rxnorm_rxnav_api',
            'dailymed_spl_api',
            'openfda_drug_label',
            'openfda_ndc_directory',
            'openfda_device_enforcement',
            'openfda_device_event',
            'fda_recalls_market_withdrawals_safety_alerts',
            'cpsc_recalls_api',
            'nhtsa_vpic_vin_decoder_api',
            'nhtsa_recalls_api_datasets'
        )
        """
    )
