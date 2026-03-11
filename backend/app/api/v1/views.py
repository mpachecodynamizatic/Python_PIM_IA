from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.saved_view import SavedViewCreate, SavedViewExport, SavedViewRead, SavedViewUpdate
from app.services import saved_view_service

router = APIRouter(prefix="/views", tags=["views"])

# ---------------------------------------------------------------------------
# Generic resource endpoints  (replaces/extends the products-only ones)
# ---------------------------------------------------------------------------

@router.get("/{resource}", response_model=list[SavedViewRead])
async def list_views(
    resource: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List the user's own views plus all public views for a resource."""
    return await saved_view_service.list_views(db, user_id=str(user.id), resource=resource)


@router.post("/{resource}", response_model=SavedViewRead, status_code=status.HTTP_201_CREATED)
async def create_view(
    resource: str,
    body: SavedViewCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    view = await saved_view_service.create_view(db, user_id=str(user.id), resource=resource, data=body)
    await db.commit()
    return view


@router.get("/{resource}/{view_id}/export", response_model=SavedViewExport)
async def export_view(
    resource: str,
    view_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export a view definition as a portable JSON (no user/id fields)."""
    return await saved_view_service.export_view(db, user_id=str(user.id), resource=resource, view_id=view_id)


@router.post("/{resource}/import", response_model=SavedViewRead, status_code=status.HTTP_201_CREATED)
async def import_view(
    resource: str,
    body: SavedViewExport,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Import a previously exported view definition."""
    view = await saved_view_service.import_view(db, user_id=str(user.id), resource=resource, data=body)
    await db.commit()
    return view


@router.get("/{resource}/{view_id}", response_model=SavedViewRead)
async def get_view(
    resource: str,
    view_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await saved_view_service.get_view(db, user_id=str(user.id), resource=resource, view_id=view_id)


@router.patch("/{resource}/{view_id}", response_model=SavedViewRead)
async def update_view(
    resource: str,
    view_id: str,
    body: SavedViewUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    view = await saved_view_service.update_view(
        db, user_id=str(user.id), resource=resource, view_id=view_id, data=body,
    )
    await db.commit()
    return view


@router.delete("/{resource}/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_view(
    resource: str,
    view_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await saved_view_service.delete_view(db, user_id=str(user.id), resource=resource, view_id=view_id)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


