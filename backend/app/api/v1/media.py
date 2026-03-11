from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_scopes
from app.models.user import User
from app.schemas.media import MediaRead
from app.services import media_service

router = APIRouter(prefix="/media", tags=["media"])


@router.post("", response_model=MediaRead, status_code=201)
async def upload_media(
    file: UploadFile = File(...),
    sku: str | None = Form(None),
    kind: str = Form("image"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_scopes("media:write")),
):
    """Upload a file and optionally link it to a product SKU."""
    asset = await media_service.upload_media(db, file, sku=sku, kind=kind)
    await db.commit()
    await db.refresh(asset)
    return asset


@router.get("", response_model=list[MediaRead])
async def list_media(
    sku: str | None = Query(None, description="Filter by product SKU"),
    kind: str | None = Query(None, description="Filter by kind (image, video, pdf…)"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await media_service.list_media(db, sku=sku, kind=kind)


@router.get("/{media_id}", response_model=MediaRead)
async def get_media(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await media_service.get_media_asset(db, media_id)


@router.patch("/{media_id}/link", response_model=MediaRead)
async def link_media(
    media_id: str,
    sku: str = Query(..., description="SKU of the product to link this asset to"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_scopes("media:write")),
):
    """Associate an existing media asset with a product."""
    asset = await media_service.link_to_product(db, media_id, sku)
    await db.commit()
    return asset


@router.delete("/{media_id}", status_code=204)
async def delete_media(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_scopes("media:write")),
):
    await media_service.delete_media_asset(db, media_id)
    await db.commit()
