"""
DAM (Digital Asset Management) service.

Files are stored locally in backend/uploads/.
The upload directory is mounted as /uploads static route in main.py.
"""

import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import MediaAsset

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_CONTENT_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
    "video/mp4": ".mp4",
    "application/pdf": ".pdf",
}


async def upload_media(
    db: AsyncSession,
    file: UploadFile,
    sku: str | None,
    kind: str,
) -> MediaAsset:
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{content_type}' not allowed. Allowed: {list(ALLOWED_CONTENT_TYPES)}",
        )

    ext = ALLOWED_CONTENT_TYPES[content_type]
    stored_name = f"{uuid.uuid4()}{ext}"
    dest = UPLOAD_DIR / stored_name

    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)  # type: ignore[arg-type]

    asset = MediaAsset(
        sku=sku,
        kind=kind,
        url=f"/uploads/{stored_name}",
        filename=file.filename,
        metadata_extra={"content_type": content_type, "stored_as": stored_name},
    )
    db.add(asset)
    await db.flush()
    return asset


async def list_media(
    db: AsyncSession,
    sku: str | None = None,
    kind: str | None = None,
) -> list[MediaAsset]:
    query = select(MediaAsset).order_by(MediaAsset.created_at.desc())
    if sku:
        query = query.where(MediaAsset.sku == sku)
    if kind:
        query = query.where(MediaAsset.kind == kind)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_media_asset(db: AsyncSession, media_id: str) -> MediaAsset:
    result = await db.execute(select(MediaAsset).where(MediaAsset.id == media_id))
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=404, detail="Media asset not found")
    return asset


async def link_to_product(db: AsyncSession, media_id: str, sku: str) -> MediaAsset:
    asset = await get_media_asset(db, media_id)
    asset.sku = sku
    await db.flush()
    return asset


async def delete_media_asset(db: AsyncSession, media_id: str) -> None:
    asset = await get_media_asset(db, media_id)
    stored = (asset.metadata_extra or {}).get("stored_as")
    if stored:
        path = UPLOAD_DIR / stored
        if path.exists():
            path.unlink()
    await db.delete(asset)
    await db.flush()
