import math
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryTree, CategoryUpdate
from app.schemas.common import PaginatedResponse


async def create_category(db: AsyncSession, data: CategoryCreate) -> Category:
    existing = await db.execute(select(Category).where(Category.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category with slug '{data.slug}' already exists",
        )
    if data.parent_id:
        parent = await db.execute(select(Category).where(Category.id == data.parent_id))
        if parent.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found",
            )
    category = Category(**data.model_dump())
    db.add(category)
    await db.flush()
    return category


async def get_category(db: AsyncSession, category_id: str) -> Category:
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


async def update_category(
    db: AsyncSession, category_id: uuid.UUID, data: CategoryUpdate
) -> Category:
    category = await get_category(db, category_id)
    update_data = data.model_dump(exclude_unset=True)
    if "slug" in update_data:
        existing = await db.execute(
            select(Category).where(Category.slug == update_data["slug"], Category.id != category_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category with slug '{update_data['slug']}' already exists",
            )
    for field, value in update_data.items():
        setattr(category, field, value)
    await db.flush()
    await db.refresh(category)
    return category


async def delete_category(db: AsyncSession, category_id: str) -> None:
    category = await get_category(db, category_id)
    await db.delete(category)
    await db.flush()


async def get_category_tree(db: AsyncSession) -> list[CategoryTree]:
    result = await db.execute(
        select(Category).options(selectinload(Category.children)).order_by(Category.sort_order)
    )
    all_cats = result.scalars().unique().all()

    cat_map: dict[str, CategoryTree] = {}
    for cat in all_cats:
        cat_map[cat.id] = CategoryTree.model_validate(cat)

    roots: list[CategoryTree] = []
    for cat_tree in cat_map.values():
        if cat_tree.parent_id is None:
            roots.append(cat_tree)
        elif cat_tree.parent_id in cat_map:
            cat_map[cat_tree.parent_id].children.append(cat_tree)

    return roots


async def list_categories(
    db: AsyncSession, page: int = 1, size: int = 50
) -> PaginatedResponse:
    count_result = await db.execute(select(func.count(Category.id)))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Category).order_by(Category.sort_order).offset((page - 1) * size).limit(size)
    )
    items = result.scalars().all()

    from app.schemas.category import CategoryRead

    return PaginatedResponse(
        items=[CategoryRead.model_validate(c) for c in items],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if size > 0 else 0,
    )
