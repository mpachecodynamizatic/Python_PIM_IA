from pydantic import BaseModel, ConfigDict


class SavedViewBase(BaseModel):
    name: str
    description: str | None = None
    filters: dict
    is_default: bool = False


class SavedViewCreate(SavedViewBase):
    pass


class SavedViewUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    filters: dict | None = None
    is_default: bool | None = None


class SavedViewRead(SavedViewBase):
    id: str
    resource: str
    model_config = ConfigDict(from_attributes=True)

