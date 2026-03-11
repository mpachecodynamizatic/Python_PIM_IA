from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.schemas.attribute_family import (
    AttributeFamilyCreate,
    AttributeFamilyRead,
    AttributeDefinitionCreate,
    AttributeDefinitionRead,
)
from app.services import attribute_family_service

router = APIRouter(prefix="/attributes", tags=["attributes"])


@router.get("/families", response_model=list[AttributeFamilyRead])
async def list_families(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await attribute_family_service.list_families(db)


@router.post("/families", response_model=AttributeFamilyRead, status_code=201)
async def create_family(
    body: AttributeFamilyCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await attribute_family_service.create_family(db, body)


@router.get("/families/{family_id}/definitions", response_model=list[AttributeDefinitionRead])
async def list_family_definitions(
    family_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await attribute_family_service.list_definitions(db, family_id)


@router.post("/families/{family_id}/definitions", response_model=AttributeDefinitionRead, status_code=201)
async def add_family_definition(
    family_id: str,
    body: AttributeDefinitionCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await attribute_family_service.add_definition(db, family_id, body)

