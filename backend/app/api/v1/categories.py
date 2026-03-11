from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_scopes
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead, CategoryTree, CategoryUpdate
from app.schemas.common import MessageResponse
from app.services import category_service

router = APIRouter(prefix="/taxonomy/categories", tags=["taxonomy"])


@router.post("", response_model=CategoryRead, status_code=201)
async def create_category(
    body: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_scopes("taxonomy:write")),
):
    return await category_service.create_category(db, body)


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await category_service.list_categories(db, page=page, size=size)
    return result.items


@router.get("/tree", response_model=list[CategoryTree])
async def get_tree(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await category_service.get_category_tree(db)


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await category_service.get_category(db, category_id)


@router.get("/{category_id}/schema")
async def get_category_schema(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    cat = await category_service.get_category(db, category_id)
    return {"category_id": str(cat.id), "name": cat.name, "attribute_schema": cat.attribute_schema}


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: str,
    body: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_scopes("taxonomy:write")),
):
    return await category_service.update_category(db, category_id, body)


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_scopes("taxonomy:write")),
):
    await category_service.delete_category(db, category_id)
    return MessageResponse(message="Category deleted")
