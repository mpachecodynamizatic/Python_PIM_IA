from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, require_scopes
from app.schemas.external_taxonomy import (
    ExternalTaxonomyCreate,
    ExternalTaxonomyRead,
    ProductTaxonomyRead,
    ProductTaxonomyUpsert,
)
from app.services import taxonomy_service

router = APIRouter(tags=["external-taxonomies"])


# --- Taxonomy catalog ---

@router.get("/external-taxonomies", response_model=list[ExternalTaxonomyRead])
async def list_taxonomies(
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    return await taxonomy_service.list_taxonomies(db)


@router.post("/external-taxonomies", response_model=ExternalTaxonomyRead, status_code=201)
async def create_taxonomy(
    body: ExternalTaxonomyCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await taxonomy_service.create_taxonomy(db, body)


@router.delete("/external-taxonomies/{taxonomy_id}", status_code=204)
async def delete_taxonomy(
    taxonomy_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    await taxonomy_service.delete_taxonomy(db, taxonomy_id)


# --- Product taxonomy mappings ---

@router.get("/products/{sku}/external-taxonomies", response_model=list[ProductTaxonomyRead])
async def list_product_taxonomies(
    sku: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    return await taxonomy_service.list_product_taxonomies(db, sku)


@router.put("/products/{sku}/external-taxonomies", response_model=ProductTaxonomyRead)
async def upsert_product_taxonomy(
    sku: str,
    body: ProductTaxonomyUpsert,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_scopes("products:write")),
):
    return await taxonomy_service.upsert_product_taxonomy(db, sku, body)


@router.delete("/products/{sku}/external-taxonomies/{mapping_id}", status_code=204)
async def remove_product_taxonomy(
    sku: str,
    mapping_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_scopes("products:write")),
):
    await taxonomy_service.remove_product_taxonomy(db, sku, mapping_id)
