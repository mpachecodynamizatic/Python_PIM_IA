from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.supplier import ProductSupplier, Supplier
from app.schemas.supplier import (
    ProductSupplierCreate,
    ProductSupplierUpdate,
    SupplierCreate,
    SupplierUpdate,
)


# --- Supplier CRUD ---

async def list_suppliers(db: AsyncSession, active_only: bool = False) -> list[Supplier]:
    q = select(Supplier).order_by(Supplier.name)
    if active_only:
        q = q.where(Supplier.active.is_(True))
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_supplier(db: AsyncSession, supplier_id: str) -> Supplier:
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    s = result.scalar_one_or_none()
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return s


async def create_supplier(db: AsyncSession, data: SupplierCreate) -> Supplier:
    if data.code:
        existing = await db.execute(select(Supplier).where(Supplier.code == data.code))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Supplier with code '{data.code}' already exists",
            )
    s = Supplier(**data.model_dump())
    db.add(s)
    await db.flush()
    await db.refresh(s)
    return s


async def update_supplier(db: AsyncSession, supplier_id: str, data: SupplierUpdate) -> Supplier:
    s = await get_supplier(db, supplier_id)
    update_data = data.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"]:
        existing = await db.execute(
            select(Supplier).where(Supplier.code == update_data["code"], Supplier.id != supplier_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Supplier with code '{update_data['code']}' already exists",
            )
    for field, value in update_data.items():
        setattr(s, field, value)
    await db.flush()
    await db.refresh(s)
    return s


async def delete_supplier(db: AsyncSession, supplier_id: str) -> None:
    s = await get_supplier(db, supplier_id)
    await db.delete(s)


# --- ProductSupplier ---

async def list_product_suppliers(db: AsyncSession, sku: str) -> list[ProductSupplier]:
    result = await db.execute(
        select(ProductSupplier)
        .where(ProductSupplier.sku == sku)
        .options(selectinload(ProductSupplier.supplier))
        .order_by(ProductSupplier.is_primary.desc())
    )
    return list(result.scalars().all())


async def add_product_supplier(db: AsyncSession, sku: str, data: ProductSupplierCreate) -> ProductSupplier:
    existing = await db.execute(
        select(ProductSupplier).where(
            ProductSupplier.sku == sku, ProductSupplier.supplier_id == data.supplier_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This supplier is already linked to the product",
        )
    row = ProductSupplier(sku=sku, **data.model_dump())
    db.add(row)
    await db.flush()
    result = await db.execute(
        select(ProductSupplier)
        .where(ProductSupplier.id == row.id)
        .options(selectinload(ProductSupplier.supplier))
    )
    return result.scalar_one()


async def update_product_supplier(
    db: AsyncSession, sku: str, link_id: str, data: ProductSupplierUpdate
) -> ProductSupplier:
    result = await db.execute(
        select(ProductSupplier).where(
            ProductSupplier.sku == sku, ProductSupplier.id == link_id
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier link not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.flush()
    result2 = await db.execute(
        select(ProductSupplier)
        .where(ProductSupplier.id == row.id)
        .options(selectinload(ProductSupplier.supplier))
    )
    return result2.scalar_one()


async def remove_product_supplier(db: AsyncSession, sku: str, link_id: str) -> None:
    result = await db.execute(
        select(ProductSupplier).where(
            ProductSupplier.sku == sku, ProductSupplier.id == link_id
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier link not found")
    await db.delete(row)
