from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, require_scopes
from app.schemas.supplier import (
    ProductSupplierCreate,
    ProductSupplierRead,
    ProductSupplierUpdate,
    SupplierCreate,
    SupplierRead,
    SupplierUpdate,
)
from app.services import supplier_service

router = APIRouter(tags=["suppliers"])


# --- Supplier catalog ---

@router.get("/suppliers", response_model=list[SupplierRead])
async def list_suppliers(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    return await supplier_service.list_suppliers(db, active_only=active_only)


@router.post("/suppliers", response_model=SupplierRead, status_code=201)
async def create_supplier(
    body: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await supplier_service.create_supplier(db, body)


@router.get("/suppliers/{supplier_id}", response_model=SupplierRead)
async def get_supplier(
    supplier_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    return await supplier_service.get_supplier(db, supplier_id)


@router.patch("/suppliers/{supplier_id}", response_model=SupplierRead)
async def update_supplier(
    supplier_id: str,
    body: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await supplier_service.update_supplier(db, supplier_id, body)


@router.delete("/suppliers/{supplier_id}", status_code=204)
async def delete_supplier(
    supplier_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    await supplier_service.delete_supplier(db, supplier_id)


# --- Product ↔ Supplier links ---

@router.get("/products/{sku}/suppliers", response_model=list[ProductSupplierRead])
async def list_product_suppliers(
    sku: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    return await supplier_service.list_product_suppliers(db, sku)


@router.post("/products/{sku}/suppliers", response_model=ProductSupplierRead, status_code=201)
async def add_product_supplier(
    sku: str,
    body: ProductSupplierCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_scopes("products:write")),
):
    return await supplier_service.add_product_supplier(db, sku, body)


@router.patch("/products/{sku}/suppliers/{link_id}", response_model=ProductSupplierRead)
async def update_product_supplier(
    sku: str,
    link_id: str,
    body: ProductSupplierUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_scopes("products:write")),
):
    return await supplier_service.update_product_supplier(db, sku, link_id, body)


@router.delete("/products/{sku}/suppliers/{link_id}", status_code=204)
async def remove_product_supplier(
    sku: str,
    link_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_scopes("products:write")),
):
    await supplier_service.remove_product_supplier(db, sku, link_id)
