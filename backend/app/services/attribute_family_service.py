from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribute_family import AttributeFamily, AttributeDefinition
from app.schemas.attribute_family import (
    AttributeFamilyCreate,
    AttributeFamilyRead,
    AttributeFamilyUpdate,
    AttributeDefinitionCreate,
    AttributeDefinitionRead,
    AttributeDefinitionUpdate,
)


async def list_families(db: AsyncSession) -> list[AttributeFamilyRead]:
    result = await db.execute(select(AttributeFamily).order_by(AttributeFamily.code))
    families = result.scalars().all()
    return [AttributeFamilyRead.model_validate(f) for f in families]


async def create_family(db: AsyncSession, data: AttributeFamilyCreate) -> AttributeFamilyRead:
    family = AttributeFamily(**data.model_dump())
    db.add(family)
    await db.flush()
    await db.refresh(family)
    return AttributeFamilyRead.model_validate(family)


async def list_definitions(db: AsyncSession, family_id: str) -> list[AttributeDefinitionRead]:
    result = await db.execute(
        select(AttributeDefinition)
        .where(AttributeDefinition.family_id == family_id)
        .order_by(AttributeDefinition.code)
    )
    defs = result.scalars().all()
    return [AttributeDefinitionRead.model_validate(d) for d in defs]


async def add_definition(
    db: AsyncSession,
    family_id: str,
    data: AttributeDefinitionCreate,
) -> AttributeDefinitionRead:
    definition = AttributeDefinition(family_id=family_id, **data.model_dump())
    db.add(definition)
    await db.flush()
    await db.refresh(definition)
    return AttributeDefinitionRead.model_validate(definition)


async def update_family(db: AsyncSession, family_id: str, data: AttributeFamilyUpdate) -> AttributeFamilyRead:
    result = await db.execute(select(AttributeFamily).where(AttributeFamily.id == family_id))
    family = result.scalar_one_or_none()
    if family is None:
        raise HTTPException(status_code=404, detail="Family not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(family, field, value)
    await db.flush()
    await db.refresh(family)
    return AttributeFamilyRead.model_validate(family)


async def delete_family(db: AsyncSession, family_id: str) -> None:
    result = await db.execute(select(AttributeFamily).where(AttributeFamily.id == family_id))
    family = result.scalar_one_or_none()
    if family is None:
        raise HTTPException(status_code=404, detail="Family not found")
    await db.delete(family)
    await db.flush()


async def update_definition(
    db: AsyncSession, family_id: str, def_id: str, data: AttributeDefinitionUpdate,
) -> AttributeDefinitionRead:
    result = await db.execute(
        select(AttributeDefinition).where(
            AttributeDefinition.id == def_id,
            AttributeDefinition.family_id == family_id,
        )
    )
    defn = result.scalar_one_or_none()
    if defn is None:
        raise HTTPException(status_code=404, detail="Definition not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(defn, field, value)
    await db.flush()
    await db.refresh(defn)
    return AttributeDefinitionRead.model_validate(defn)


async def delete_definition(db: AsyncSession, family_id: str, def_id: str) -> None:
    result = await db.execute(
        select(AttributeDefinition).where(
            AttributeDefinition.id == def_id,
            AttributeDefinition.family_id == family_id,
        )
    )
    defn = result.scalar_one_or_none()
    if defn is None:
        raise HTTPException(status_code=404, detail="Definition not found")
    await db.delete(defn)
    await db.flush()

