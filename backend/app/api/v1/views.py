from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.saved_view import SavedViewCreate, SavedViewRead, SavedViewUpdate
from app.services import saved_view_service

router = APIRouter(prefix="/views", tags=["views"])


@router.get("/products", response_model=list[SavedViewRead])
async def list_product_views(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await saved_view_service.list_product_views(db, user_id=str(user.id))


@router.post("/products", response_model=SavedViewRead, status_code=status.HTTP_201_CREATED)
async def create_product_view(
    body: SavedViewCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    view = await saved_view_service.create_product_view(db, user_id=str(user.id), data=body)
    await db.commit()
    return view


@router.get("/products/{view_id}", response_model=SavedViewRead)
async def get_product_view(
    view_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await saved_view_service.get_product_view(db, user_id=str(user.id), view_id=view_id)


@router.patch("/products/{view_id}", response_model=SavedViewRead)
async def update_product_view(
    view_id: str,
    body: SavedViewUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    view = await saved_view_service.update_product_view(
        db, user_id=str(user.id), view_id=view_id, data=body,
    )
    await db.commit()
    return view


@router.delete("/products/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_view(
    view_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await saved_view_service.delete_product_view(db, user_id=str(user.id), view_id=view_id)
    await db.commit()

