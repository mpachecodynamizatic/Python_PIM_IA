from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quality_rule import QualityRuleSet, QualityRule
from app.schemas.quality_rule import (
    QualityRuleSetCreate,
    QualityRuleSetRead,
    QualityRuleSetUpdate,
    QualityRuleCreate,
    QualityRuleRead,
    QualityRuleUpdate,
)


async def list_rule_sets(db: AsyncSession) -> list[QualityRuleSetRead]:
    result = await db.execute(
        select(QualityRuleSet)
        .options(selectinload(QualityRuleSet.rules))
        .order_by(QualityRuleSet.name)
    )
    sets = result.scalars().all()
    return [QualityRuleSetRead.model_validate(rs) for rs in sets]


async def get_rule_set(db: AsyncSession, rule_set_id: str) -> QualityRuleSetRead:
    result = await db.execute(
        select(QualityRuleSet)
        .options(selectinload(QualityRuleSet.rules))
        .where(QualityRuleSet.id == rule_set_id)
    )
    rs = result.scalar_one_or_none()
    if rs is None:
        raise HTTPException(status_code=404, detail="Rule set not found")
    return QualityRuleSetRead.model_validate(rs)


async def create_rule_set(db: AsyncSession, data: QualityRuleSetCreate) -> QualityRuleSetRead:
    rule_set = QualityRuleSet(
        name=data.name,
        description=data.description,
        active=data.active,
    )
    for rule_data in data.rules:
        rule_set.rules.append(QualityRule(**rule_data.model_dump()))
    db.add(rule_set)
    await db.flush()
    # Re-query with eager load to avoid MissingGreenlet on rules relationship
    result = await db.execute(
        select(QualityRuleSet)
        .options(selectinload(QualityRuleSet.rules))
        .where(QualityRuleSet.id == rule_set.id)
    )
    rule_set = result.scalar_one()
    return QualityRuleSetRead.model_validate(rule_set)


async def update_rule_set(db: AsyncSession, rule_set_id: str, data: QualityRuleSetUpdate) -> QualityRuleSetRead:
    result = await db.execute(
        select(QualityRuleSet)
        .options(selectinload(QualityRuleSet.rules))
        .where(QualityRuleSet.id == rule_set_id)
    )
    rs = result.scalar_one_or_none()
    if rs is None:
        raise HTTPException(status_code=404, detail="Rule set not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rs, field, value)
    await db.flush()
    await db.refresh(rs)
    result2 = await db.execute(
        select(QualityRuleSet)
        .options(selectinload(QualityRuleSet.rules))
        .where(QualityRuleSet.id == rule_set_id)
    )
    return QualityRuleSetRead.model_validate(result2.scalar_one())


async def delete_rule_set(db: AsyncSession, rule_set_id: str) -> None:
    result = await db.execute(select(QualityRuleSet).where(QualityRuleSet.id == rule_set_id))
    rs = result.scalar_one_or_none()
    if rs is None:
        raise HTTPException(status_code=404, detail="Rule set not found")
    await db.delete(rs)
    await db.flush()


async def set_active_rule_set(db: AsyncSession, rule_set_id: str) -> None:
    result = await db.execute(select(QualityRuleSet))
    for rs in result.scalars().all():
        rs.active = rs.id == rule_set_id
    await db.flush()


async def deactivate_all(db: AsyncSession) -> None:
    result = await db.execute(select(QualityRuleSet))
    for rs in result.scalars().all():
        rs.active = False
    await db.flush()


async def list_rules(db: AsyncSession, rule_set_id: str) -> list[QualityRuleRead]:
    result = await db.execute(
        select(QualityRule).where(QualityRule.rule_set_id == rule_set_id).order_by(QualityRule.dimension)
    )
    rules = result.scalars().all()
    return [QualityRuleRead.model_validate(r) for r in rules]


async def add_rule(
    db: AsyncSession,
    rule_set_id: str,
    data: QualityRuleCreate,
) -> QualityRuleRead:
    rule = QualityRule(rule_set_id=rule_set_id, **data.model_dump())
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return QualityRuleRead.model_validate(rule)


async def delete_rule(db: AsyncSession, rule_id: str) -> None:
    result = await db.execute(select(QualityRule).where(QualityRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.flush()


async def update_rule(db: AsyncSession, rule_id: str, data: QualityRuleUpdate) -> QualityRuleRead:
    result = await db.execute(select(QualityRule).where(QualityRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await db.flush()
    await db.refresh(rule)
    return QualityRuleRead.model_validate(rule)

