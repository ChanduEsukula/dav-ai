"""Seed Everyday Safety source registry rows.

Revision ID: 20260608_0009
Revises: 20260605_0008
Create Date: 2026-06-08
"""

from alembic import op


revision = "20260608_0009"
down_revision = "20260605_0008"
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
                'openfda_cosmetic_event',
                'openFDA Cosmetic Event API',
                'https://api.fda.gov/cosmetic/event.json',
                'CosmeticSignal',
                'Cosmetic adverse-event reports from openFDA for skincare, makeup, hair, fragrance, and related products.',
                'Source-dependent FDA cosmetic event updates'
            ),
            (
                'cdc_foodborne_outbreaks',
                'CDC/FDA Foodborne Outbreak Investigation Context',
                'https://www.cdc.gov/foodborne-outbreaks/ + https://www.fda.gov/food/outbreaks-foodborne-illness',
                'RealWorldSafety',
                'CDC/FDA foodborne outbreak and investigation context records. These are public-health context records, not automatically recalls or proof of causation.',
                'CDC/FDA outbreak investigation updates',
            ),
            (
                'openfda_food_enforcement',
                'openFDA Food Enforcement API',
                'https://api.fda.gov/food/enforcement.json',
                'FoodRadar',
                'Food, supplement, grocery, and packaged-food recall enforcement records from openFDA.',
                'Source-dependent FDA updates'
            ),
            (
                'usda_fsis_recall',
                'USDA FSIS Recall API',
                'https://www.fsis.usda.gov/fsis/api/recall/v/1',
                'FoodRadar',
                'Meat, poultry, egg-product recall and public-health-alert records from USDA FSIS.',
                'Real-time FSIS recall and public health alert updates'
            ),
            (
                'foodradar_multi_source',
                'FoodRadar Multi-Source Recall Search',
                'https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts + https://api.fda.gov/food/enforcement.json + https://www.fsis.usda.gov/fsis/api/recall/v/1',
                'FoodRadar',
                'Aggregate FoodRadar workflow combining FDA public recall notices, openFDA Food Enforcement records, and USDA FSIS recall/public-health-alert records.',
                'Source-dependent FDA updates plus FSIS recall/public-health-alert updates'
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
            'openfda_cosmetic_event',
            'openfda_food_enforcement',
            'usda_fsis_recall',
            'foodradar_multi_source'
        )
        """
    )