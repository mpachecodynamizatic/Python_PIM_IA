from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    permissions: dict[str, str] = {}  # {resource: level}, default to empty dict


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: dict[str, str] | None = None
    is_active: bool | None = None


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    permissions: dict[str, str]
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
