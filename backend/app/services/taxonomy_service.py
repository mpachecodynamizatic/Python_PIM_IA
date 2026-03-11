from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.external_taxonomy import ExternalTaxonomy, ProductExternalTaxonomy
from app.schemas.external_taxonomy import ExternalTaxonomyCreate, ProductTaxonomyUpsert


async def list_taxonomies(db: AsyncSession) -> list[ExternalTaxonomy]:
    result = await db.execute(select(ExternalTaxonomy).order_by(ExternalTaxonomy.provider, ExternalTaxonomy.name))
    return list(result.scalars().all())


async def get_taxonomy(db: AsyncSession, taxonomy_id: str) -> ExternalTaxonomy:
    result = await db.execute(select(ExternalTaxonomy).where(ExternalTaxonomy.id == taxonomy_id))
    t = result.scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taxonomy not found")
    return t


async def create_taxonomy(db: AsyncSession, data: ExternalTaxonomyCreate) -> ExternalTaxonomy:
    existing = await db.execute(select(ExternalTaxonomy).where(ExternalTaxonomy.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Taxonomy '{data.name}' already exists",
        )
    t = ExternalTaxonomy(**data.model_dump())
    db.add(t)
    await db.flush()
    await db.refresh(t)
    return t


async def delete_taxonomy(db: AsyncSession, taxonomy_id: str) -> None:
    t = await get_taxonomy(db, taxonomy_id)
    await db.delete(t)


async def list_product_taxonomies(db: AsyncSession, sku: str) -> list[ProductExternalTaxonomy]:
    result = await db.execute(
        select(ProductExternalTaxonomy)
        .where(ProductExternalTaxonomy.sku == sku)
        .options(selectinload(ProductExternalTaxonomy.taxonomy))
        .order_by(ProductExternalTaxonomy.taxonomy_id)
    )
    return list(result.scalars().all())


async def upsert_product_taxonomy(
    db: AsyncSession, sku: str, data: ProductTaxonomyUpsert
) -> ProductExternalTaxonomy:
    result = await db.execute(
        select(ProductExternalTaxonomy).where(
            ProductExternalTaxonomy.sku == sku,
            ProductExternalTaxonomy.taxonomy_id == data.taxonomy_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = ProductExternalTaxonomy(sku=sku, **data.model_dump())
        db.add(row)
    else:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
    await db.flush()
    result2 = await db.execute(
        select(ProductExternalTaxonomy)
        .where(ProductExternalTaxonomy.id == row.id)
        .options(selectinload(ProductExternalTaxonomy.taxonomy))
    )
    return result2.scalar_one()


async def remove_product_taxonomy(db: AsyncSession, sku: str, mapping_id: str) -> None:
    result = await db.execute(
        select(ProductExternalTaxonomy).where(
            ProductExternalTaxonomy.sku == sku,
            ProductExternalTaxonomy.id == mapping_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Taxonomy mapping not found")
    await db.delete(row)
