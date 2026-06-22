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
            'fda_recalls_market_withdrawals_safety_alerts',
            'cpsc_recalls_api',
            'nhtsa_vpic_vin_decoder_api',
            'nhtsa_recalls_api_datasets'
        )
        """
    )
