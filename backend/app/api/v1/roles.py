import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services import role_service

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post("", response_model=RoleRead, status_code=201)
async def create_role(
    body: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    """Create a new role. Admin only."""
    role = await role_service.create_role(db, body)
    await db.commit()
    return role


@router.get("", response_model=list[RoleRead])
async def list_roles(
    include_inactive: bool = Query(False, description="Include inactive roles"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """List all roles. Available to all authenticated users."""
    return await role_service.list_roles(db, include_inactive=include_inactive)


@router.get("/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Get a role by ID. Available to all authenticated users."""
    return await role_service.get_role(db, role_id)


@router.patch("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: uuid.UUID,
    body: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    """Update a role. Admin only. System roles can have permissions edited."""
    await role_service.update_role(db, role_id, body)
    await db.commit()
    # Re-query to avoid MissingGreenlet error after commit
    return await role_service.get_role(db, role_id)


@router.delete("/{role_id}", status_code=204)
async def delete_role(
    role_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    """Delete a role. Admin only. Cannot delete system roles or roles with users."""
    await role_service.delete_role(db, role_id)
    await db.commit()
    return None
