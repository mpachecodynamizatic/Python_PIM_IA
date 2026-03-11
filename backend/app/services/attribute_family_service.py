from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribute_family import AttributeFamily, AttributeDefinition
from app.schemas.attribute_family import (
    AttributeFamilyCreate,
    AttributeFamilyRead,
    AttributeDefinitionCreate,
    AttributeDefinitionRead,
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

