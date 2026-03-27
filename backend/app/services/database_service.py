"""
Database management service for admin operations.
Handles purging data and seeding sample data.
"""

import os
import logging
import requests
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Import all models (except User and Role which must be preserved)
from app.models.audit import AuditLog
from app.models.attribute_family import AttributeFamily, AttributeDefinition
from app.models.brand import Brand
from app.models.category import Category
from app.models.channel import Channel
from app.models.export_preference import ExportPreference
from app.models.external_taxonomy import ExternalTaxonomy, ProductExternalTaxonomy
from app.models.import_job import ImportJob
from app.models.mapping_template import MappingTemplate
from app.models.media import MediaAsset
from app.models.product import Product, ProductI18n
from app.models.product_channel import ProductChannel
from app.models.product_comment import ProductComment
from app.models.product_compliance import ProductCompliance
from app.models.product_logistics import ProductLogistics
from app.models.product_sync_history import ProductSyncHistory
from app.models.quality_rule import QualityRule, QualityRuleSet
from app.models.saved_view import SavedView
from app.models.supplier import Supplier, ProductSupplier
from app.models.sync_job import SyncJob


async def purge_all_data(db: AsyncSession) -> dict[str, int]:
    """
    Delete ALL data except users and roles.

    Deletes tables in FK-safe order to avoid constraint violations.
    Returns a dict with counts of deleted records per table.
    """
    counts = {}

    # Order matters! Delete children before parents to avoid FK violations
    tables_to_purge = [
        # Product-related (most dependent first)
        ("product_external_taxonomies", ProductExternalTaxonomy),
        ("product_suppliers", ProductSupplier),
        ("product_channels", ProductChannel),
        ("product_logistics", ProductLogistics),
        ("product_compliance", ProductCompliance),
        ("product_comments", ProductComment),
        ("product_sync_history", ProductSyncHistory),
        ("media_assets", MediaAsset),
        ("product_i18n", ProductI18n),
        ("products", Product),

        # Catalog data
        ("categories", Category),
        ("brands", Brand),
        ("channels", Channel),
        ("suppliers", Supplier),
        ("external_taxonomies", ExternalTaxonomy),

        # Sync and jobs
        ("sync_jobs", SyncJob),
        ("import_jobs", ImportJob),

        # Quality
        ("quality_rules", QualityRule),
        ("quality_rule_sets", QualityRuleSet),

        # Attributes
        ("attribute_definitions", AttributeDefinition),
        ("attribute_families", AttributeFamily),

        # Other
        ("audits", AuditLog),
        ("saved_views", SavedView),
        ("mapping_templates", MappingTemplate),
        ("export_preference", ExportPreference),
    ]

    for table_name, model in tables_to_purge:
        result = await db.execute(delete(model))
        counts[table_name] = result.rowcount

    return counts


async def purge_products_data(db: AsyncSession) -> dict[str, int]:
    """
    Delete products and all related data only.

    Returns a dict with counts of deleted records per table.
    """
    counts = {}

    # Product-related tables only (in FK-safe order)
    tables_to_purge = [
        ("product_external_taxonomies", ProductExternalTaxonomy),
        ("product_suppliers", ProductSupplier),
        ("product_channels", ProductChannel),
        ("product_logistics", ProductLogistics),
        ("product_compliance", ProductCompliance),
        ("product_comments", ProductComment),
        ("product_sync_history", ProductSyncHistory),
        ("media_assets", MediaAsset),
        ("product_i18n", ProductI18n),
        ("products", Product),
    ]

    for table_name, model in tables_to_purge:
        result = await db.execute(delete(model))
        counts[table_name] = result.rowcount

    return counts


async def seed_sample_data(db: AsyncSession) -> dict[str, int]:
    """
    Generate sample data for testing/demo.

    Reuses seed functions from seed.py.
    Does NOT touch users or roles.

    Returns a dict with counts of created records per table.
    """
    # Import seed functions dynamically to avoid circular imports
    import sys
    from pathlib import Path

    # Add backend directory to path if not already there
    backend_path = str(Path(__file__).parent.parent.parent)
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    # Import seed functions
    from seed import (
        wipe_product_data,
        seed_brands,
        seed_suppliers,
        seed_channels,
        seed_categories,
        seed_products,
        seed_sync_jobs,
        seed_quality_rules,
        seed_logistics_compliance_channels_taxonomies,
        seed_external_taxonomies,
    )

    counts = {}

    from sqlalchemy import select, func

    # First, wipe existing product data (keeps users and roles)
    await wipe_product_data(db)

    # Create brands (seed function does commit internally)
    await seed_brands(db)
    result = await db.execute(select(func.count()).select_from(Brand))
    counts['brands'] = result.scalar() or 0

    # Create suppliers (returns mapping, commits internally)
    supplier_mapping = await seed_suppliers(db)
    counts['suppliers'] = len(supplier_mapping)

    # Create channels (returns mapping, commits internally)
    channel_mapping = await seed_channels(db)
    counts['channels'] = len(channel_mapping)

    # Create external taxonomies (returns mapping, commits internally)
    taxonomy_mapping = await seed_external_taxonomies(db)
    counts['external_taxonomies'] = len(taxonomy_mapping)

    # Create categories (returns mapping, commits internally)
    category_mapping = await seed_categories(db)
    counts['categories'] = len(category_mapping)

    # Create products (commits internally)
    await seed_products(db, category_mapping)
    result = await db.execute(select(func.count()).select_from(Product))
    counts['products'] = result.scalar() or 0

    # Create logistics, compliance, channels, taxonomies (commits internally)
    await seed_logistics_compliance_channels_taxonomies(db, taxonomy_mapping, supplier_mapping, channel_mapping)
    result = await db.execute(select(func.count()).select_from(ProductLogistics))
    counts['product_logistics'] = result.scalar() or 0

    # Create sync jobs (commits internally)
    await seed_sync_jobs(db, channel_mapping)
    result = await db.execute(select(func.count()).select_from(SyncJob))
    counts['sync_jobs'] = result.scalar() or 0

    # Create quality rules (commits internally)
    await seed_quality_rules(db)
    result = await db.execute(select(func.count()).select_from(QualityRuleSet))
    counts['quality_rule_sets'] = result.scalar() or 0

    return counts

