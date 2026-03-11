from pydantic import BaseModel, ConfigDict


class SavedViewBase(BaseModel):
    name: str
    description: str | None = None
    filters: dict
    is_default: bool = False
    is_public: bool = False


class SavedViewCreate(SavedViewBase):
    pass


class SavedViewUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    filters: dict | None = None
    is_default: bool | None = None
    is_public: bool | None = None


class SavedViewRead(SavedViewBase):
    id: str
    user_id: str
    resource: str
    model_config = ConfigDict(from_attributes=True)


class SavedViewExport(BaseModel):
    """Portable view definition for export/import (no user/id fields)."""
    resource: str
    name: str
    description: str | None = None
    filters: dict
    is_default: bool = False
    is_public: bool = False

