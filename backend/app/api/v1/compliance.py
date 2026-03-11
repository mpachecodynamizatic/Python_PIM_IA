from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_scopes
from app.schemas.product_compliance import ComplianceRead, ComplianceUpdate
from app.services import compliance_service

router = APIRouter(prefix="/products/{sku}/compliance", tags=["compliance"])


@router.get("", response_model=ComplianceRead)
async def get_compliance(
    sku: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    return await compliance_service.get_or_create_compliance(db, sku)


@router.put("", response_model=ComplianceRead)
async def upsert_compliance(
    sku: str,
    body: ComplianceUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_scopes("products:write")),
):
    return await compliance_service.update_compliance(db, sku, body)
