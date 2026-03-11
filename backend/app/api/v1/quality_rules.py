from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.schemas.quality_rule import (
    QualityRuleSetCreate,
    QualityRuleSetRead,
    QualityRuleSetUpdate,
    QualityRuleCreate,
    QualityRuleRead,
    QualityRuleUpdate,
)
from app.services import quality_rule_service

router = APIRouter(prefix="/quality-rules", tags=["quality-rules"])


@router.get("/sets", response_model=list[QualityRuleSetRead])
async def list_rule_sets(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await quality_rule_service.list_rule_sets(db)


@router.post("/sets", response_model=QualityRuleSetRead, status_code=201)
async def create_rule_set(
    body: QualityRuleSetCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await quality_rule_service.create_rule_set(db, body)


@router.get("/sets/{rule_set_id}", response_model=QualityRuleSetRead)
async def get_rule_set(
    rule_set_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await quality_rule_service.get_rule_set(db, rule_set_id)


@router.delete("/sets/{rule_set_id}", status_code=204)
async def delete_rule_set(
    rule_set_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    await quality_rule_service.delete_rule_set(db, rule_set_id)
    await db.commit()


@router.patch("/sets/{rule_set_id}", response_model=QualityRuleSetRead)
async def update_rule_set(
    rule_set_id: str,
    body: QualityRuleSetUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    result = await quality_rule_service.update_rule_set(db, rule_set_id, body)
    await db.commit()
    return result


@router.post("/sets/{rule_set_id}/activate", status_code=204)
async def activate_rule_set(
    rule_set_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    await quality_rule_service.set_active_rule_set(db, rule_set_id)
    await db.commit()


@router.post("/sets/deactivate-all", status_code=204)
async def deactivate_all(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    await quality_rule_service.deactivate_all(db)
    await db.commit()


@router.get("/sets/{rule_set_id}/rules", response_model=list[QualityRuleRead])
async def list_rules(
    rule_set_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await quality_rule_service.list_rules(db, rule_set_id)


@router.post("/sets/{rule_set_id}/rules", response_model=QualityRuleRead, status_code=201)
async def add_rule(
    rule_set_id: str,
    body: QualityRuleCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await quality_rule_service.add_rule(db, rule_set_id, body)


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    await quality_rule_service.delete_rule(db, rule_id)
    await db.commit()


@router.patch("/rules/{rule_id}", response_model=QualityRuleRead)
async def update_rule(
    rule_id: str,
    body: QualityRuleUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    result = await quality_rule_service.update_rule(db, rule_id, body)
    await db.commit()
    return result

