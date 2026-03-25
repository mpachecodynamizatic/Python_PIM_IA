"""
Database management API endpoints.
Admin-only operations for purging and seeding data.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.services import database_service

router = APIRouter(prefix="/database", tags=["database"])


@router.post("/purge-all", status_code=200)
async def purge_all_data(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    """
    Delete all data except users and roles.

    **ADMIN ONLY - DESTRUCTIVE OPERATION**

    Returns:
        dict: Counts of deleted records per table
    """
    result = await database_service.purge_all_data(db)
    await db.commit()
    return result


@router.post("/purge-products", status_code=200)
async def purge_products_data(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    """
    Delete products and all related data.

    **ADMIN ONLY - DESTRUCTIVE OPERATION**

    Returns:
        dict: Counts of deleted records per table
    """
    result = await database_service.purge_products_data(db)
    await db.commit()
    return result


@router.post("/seed", status_code=200)
async def seed_sample_data(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    """
    Generate sample data for testing/demo.

    Creates:
    - 16 brands
    - 5 suppliers
    - 6 channels
    - 10 categories
    - 18 products (with media, translations, etc.)
    - 7 sync jobs
    - 3 quality rule sets
    - External taxonomies

    **ADMIN ONLY**

    Returns:
        dict: Counts of created records per table
    """
    # Note: seed functions do commits internally, no need to commit here
    result = await database_service.seed_sample_data(db)
    return result
