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


async def import_from_external_pim(db: AsyncSession) -> dict[str, int]:
    """
    Import data from external PIM using credentials from environment variables.

    Connects to external PIM API, retrieves products, and imports them into the current database.
    Maps external PIM model to internal model using configurable field mappings if available,
    otherwise falls back to hardcoded mapping logic.

    Returns a dict with counts of imported records per entity type.
    """
    from sqlalchemy import func
    from app.core.config import settings
    from app.models.pim_field_mapping import PimResourceMapping
    from app.services import pim_mapping_service

    # Configuration from settings
    BASE_URL = settings.PIM_BASE_URL
    LOGIN_ENDPOINT = "/auth/login"
    GET_PRODUCTS_ENDPOINT = "/B2bProductos"
    SSL_VERIFY = settings.PIM_SSL_VERIFY.lower() != 'false'

    # Credentials
    AUTH_PAYLOAD = {
        "mail": settings.PIM_MAIL,
        "password": settings.PIM_PASSWORD
    }

    if not AUTH_PAYLOAD["mail"] or not AUTH_PAYLOAD["password"]:
        raise ValueError("PIM_MAIL and PIM_PASSWORD must be set in environment variables")

    counts = {
        'products': 0,
        'brands': 0,
        'categories': 0,
        'skipped': 0,
        'errors': 0,
    }

    # Check if there's an active mapping configuration for products
    result = await db.execute(
        select(PimResourceMapping).where(
            PimResourceMapping.resource == "products",
            PimResourceMapping.is_active == True
        )
    )
    use_mapping_config = result.scalar_one_or_none() is not None

    if use_mapping_config:
        logger.info("Using configured field mapping for product import")
    else:
        logger.info("Using hardcoded field mapping for product import (no active config found)")

    try:
        # Authenticate
        login_url = f"{BASE_URL}{LOGIN_ENDPOINT}"
        logger.info(f"Connecting to external PIM at {BASE_URL}")

        login_response = requests.post(
            login_url,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json=AUTH_PAYLOAD,
            verify=SSL_VERIFY,
            timeout=30
        )
        login_response.raise_for_status()
        login_data = login_response.json()

        # Get token
        if isinstance(login_data, dict) and 'token' in login_data:
            access_token = login_data['token']
        elif isinstance(login_data, str):
            access_token = login_data
        else:
            raise ValueError("Could not find access token in login response")

        logger.info("Successfully authenticated with external PIM")

        # Get products
        get_products_url = f"{BASE_URL}{GET_PRODUCTS_ENDPOINT}"
        get_headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        get_response = requests.get(
            get_products_url,
            headers=get_headers,
            verify=SSL_VERIFY,
            timeout=60
        )
        get_response.raise_for_status()

        external_products = get_response.json()
        logger.info(f"Retrieved {len(external_products)} products from external PIM")

        # Get existing brands and categories to avoid duplicates
        existing_brands = await db.execute(select(Brand))
        brand_map = {b.name: b for b in existing_brands.scalars().all()}

        existing_categories = await db.execute(select(Category))
        category_map = {c.name: c for c in existing_categories.scalars().all()}

        # Process each product
        for item in external_products:
            try:
                # Use configured mapping if available
                if use_mapping_config:
                    try:
                        # Apply configured field mapping
                        product_data = await pim_mapping_service.apply_field_mapping(
                            db, "products", item
                        )

                        # Check if product already exists
                        sku = product_data.get('sku')
                        if not sku:
                            logger.warning(f"Skipping product without SKU after mapping: {item.get('id', 'unknown')}")
                            counts['skipped'] += 1
                            continue

                        existing = await db.execute(select(Product).where(Product.sku == sku))
                        product = existing.scalar_one_or_none()

                        if product:
                            # Update existing product with mapped data
                            for key, value in product_data.items():
                                if key != 'sku':  # Don't change SKU
                                    setattr(product, key, value)
                        else:
                            # Create new product with mapped data
                            product = Product(**product_data)
                            db.add(product)

                        counts['products'] += 1

                    except ValueError as e:
                        # Mapping error (missing required field, FK not found, etc.)
                        logger.warning(f"Skipping product due to mapping error: {e}")
                        counts['skipped'] += 1
                        continue
                    except Exception as e:
                        logger.error(f"Error applying mapping to product {item.get('sku', 'unknown')}: {e}")
                        counts['errors'] += 1
                        continue

                else:
                    # Fallback to hardcoded mapping logic
                    # Skip products without essential data
                    sku = item.get('sku')
                    titulo = item.get('titulo')
                    estado = item.get('estado_referencia')

                    if not sku or not titulo:
                        counts['skipped'] += 1
                        continue

                    # Filter by active states
                    if estado not in ['ACTIVA', 'PROXIMAMENTE', 'FIN EXISTENCIAS']:
                        counts['skipped'] += 1
                        continue

                    # Filter by category (skip REPUESTOS)
                    categoria = item.get('categorias')
                    if categoria == 'REPUESTOS':
                        counts['skipped'] += 1
                        continue

                    # Map brand code
                    marca_pim = item.get('marca', '')
                    marca_codigo = {
                        'Aspes': 'AS',
                        'Svan': 'SV',
                        'Nilson': 'NL',
                        'Hyundai': 'HY'
                    }.get(marca_pim, marca_pim)

                    # Filter by allowed brands
                    if marca_codigo not in ['AS', 'SV', 'NL', 'HY']:
                        counts['skipped'] += 1
                        continue

                    # Create or get brand
                    if marca_pim and marca_pim not in brand_map:
                        brand = Brand(
                            name=marca_pim,
                            slug=marca_pim.lower().replace(' ', '-'),
                            description=f"Imported from external PIM: {marca_pim}"
                        )
                        db.add(brand)
                        await db.flush()
                        brand_map[marca_pim] = brand
                        counts['brands'] += 1

                    # Create or get category
                    if categoria and categoria not in category_map:
                        category = Category(
                            name=categoria,
                            slug=categoria.lower().replace(' ', '-'),
                            description=f"Imported from external PIM: {categoria}"
                        )
                        db.add(category)
                        await db.flush()
                        category_map[categoria] = category
                        counts['categories'] += 1

                    # Check if product already exists
                    existing = await db.execute(select(Product).where(Product.sku == sku))
                    product = existing.scalar_one_or_none()

                    # Map status
                    status_map = {
                        'ACTIVA': 'approved',
                        'PROXIMAMENTE': 'draft',
                        'FIN EXISTENCIAS': 'retired'
                    }
                    status = status_map.get(estado, 'draft')

                    # Get category ID
                    category_id = category_map.get(categoria).id if categoria in category_map else None

                    if product:
                        # Update existing product
                        product.name = titulo
                        product.long_description = item.get('descripcion_larga', '')
                        product.status = status
                        product.brand = marca_codigo
                        product.category_id = category_id
                        product.ean_gtin = item.get('ean')
                        product.attributes = {
                            'external_id': item.get('id'),
                            'palabras_clave': item.get('palabras_clave'),
                            'imagen': item.get('imagen'),
                            'codigo': item.get('codigo'),
                            'volumen': item.get('volumen'),
                            'estado_referencia': estado,
                        }
                    else:
                        # Create new product
                        product = Product(
                            sku=sku,
                            name=titulo,
                            long_description=item.get('descripcion_larga', ''),
                            status=status,
                            brand=marca_codigo,
                            category_id=category_id,
                            ean_gtin=item.get('ean'),
                            attributes={
                                'external_id': item.get('id'),
                                'palabras_clave': item.get('palabras_clave'),
                                'imagen': item.get('imagen'),
                                'codigo': item.get('codigo'),
                                'volumen': item.get('volumen'),
                                'estado_referencia': estado,
                            },
                            seo={
                                'meta_title': titulo,
                                'meta_description': item.get('descripcion_larga', '')[:160] if item.get('descripcion_larga') else '',
                            }
                        )
                        db.add(product)

                    counts['products'] += 1

            except Exception as e:
                logger.error(f"Error processing product {item.get('sku', 'unknown')}: {e}")
                counts['errors'] += 1
                continue

        # Commit all changes
        await db.commit()

        logger.info(f"Import completed: {counts}")
        return counts

    except requests.HTTPError as e:
        logger.error(f"HTTP error connecting to external PIM: {e}")
        raise ValueError(f"Failed to connect to external PIM: {e}")
    except Exception as e:
        logger.exception("Unexpected error importing from external PIM")
        raise
