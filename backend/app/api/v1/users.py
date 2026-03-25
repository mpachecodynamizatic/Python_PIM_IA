import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.permissions import RESOURCES, RESOURCE_LABELS, PERMISSION_LEVELS, ROLE_PERMISSIONS
from app.models.user import User
from app.schemas.user import PasswordChange, UserCreate, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    user = await user_service.create_user(db, body)
    user_id = user.id  # Store ID before commit
    await db.commit()
    # Re-query to avoid MissingGreenlet error after commit
    return await user_service.get_user(db, uuid.UUID(user_id))


@router.get("", response_model=list[UserRead])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    return await user_service.list_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    return await user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    await user_service.update_user(db, user_id, body)
    await db.commit()
    # Re-query to avoid MissingGreenlet error after commit
    return await user_service.get_user(db, user_id)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
):
    await user_service.delete_user(db, user_id, current_user.id)
    await db.commit()
    return None


@router.patch("/{user_id}/password", status_code=204)
async def change_password(
    user_id: uuid.UUID,
    body: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change user password. Users can change their own (requires current password), admins can change any."""
    await user_service.change_password(db, user_id, body, current_user)
    await db.commit()
    return None


@router.get("/permissions/resources")
async def get_permission_resources(
    _admin: User = Depends(require_roles("admin")),
):
    """Get available resources and permission levels for the permission system."""
    return {
        "resources": [
            {"id": res, "label": RESOURCE_LABELS.get(res, res)}
            for res in RESOURCES
        ],
        "levels": PERMISSION_LEVELS,
        "roles": {
            "admin": ROLE_PERMISSIONS["admin"],
            "editor": ROLE_PERMISSIONS["editor"],
            "viewer": ROLE_PERMISSIONS["viewer"],
        },
    }
