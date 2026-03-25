import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.models.user import User
from app.schemas.role import RoleCreate, RoleUpdate


async def create_role(db: AsyncSession, data: RoleCreate) -> Role:
    """Create a new role."""
    # Check if role name already exists
    existing = await db.execute(select(Role).where(Role.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role with name '{data.name}' already exists",
        )

    role = Role(
        name=data.name,
        description=data.description,
        permissions=data.permissions,
        is_system=False,  # New roles are never system roles
        is_active=True,
    )
    db.add(role)
    await db.flush()
    return role


async def get_role(db: AsyncSession, role_id: uuid.UUID) -> Role:
    """Get a role by ID."""
    result = await db.execute(select(Role).where(Role.id == str(role_id)))
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )
    return role


async def get_role_by_name(db: AsyncSession, name: str) -> Role | None:
    """Get a role by name."""
    result = await db.execute(select(Role).where(Role.name == name))
    return result.scalar_one_or_none()


async def list_roles(db: AsyncSession, include_inactive: bool = False) -> list[Role]:
    """List all roles, optionally including inactive ones."""
    query = select(Role).order_by(Role.name)
    if not include_inactive:
        query = query.where(Role.is_active == True)  # noqa: E712
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_role(db: AsyncSession, role_id: uuid.UUID, data: RoleUpdate) -> Role:
    """Update a role. System roles can have permissions edited but not name."""
    role = await get_role(db, role_id)

    update_data = data.model_dump(exclude_unset=True)

    # If trying to change name of a system role, prevent it
    if role.is_system and "name" in update_data and update_data["name"] != role.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change the name of a system role",
        )

    # Apply updates
    for field, value in update_data.items():
        setattr(role, field, value)

    await db.flush()
    return role


async def delete_role(db: AsyncSession, role_id: uuid.UUID) -> None:
    """Delete a role. Cannot delete system roles or roles with users."""
    role = await get_role(db, role_id)

    # Prevent deletion of system roles
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system roles",
        )

    # Check if any users have this role
    result = await db.execute(select(User).where(User.role == role.name))
    users_with_role = result.scalars().all()
    if users_with_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role '{role.name}' because {len(users_with_role)} user(s) have this role",
        )

    await db.delete(role)
    await db.flush()
