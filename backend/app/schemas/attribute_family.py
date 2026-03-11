from pydantic import BaseModel


class AttributeDefinitionBase(BaseModel):
    code: str
    label: str
    type: str = "string"  # string, number, boolean, enum
    required: bool = False
    options_json: str | None = None


class AttributeDefinitionCreate(AttributeDefinitionBase):
    pass


class AttributeDefinitionRead(AttributeDefinitionBase):
    id: str

    class Config:
        from_attributes = True


class AttributeFamilyBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    category_id: str | None = None


class AttributeFamilyCreate(AttributeFamilyBase):
    pass


class AttributeFamilyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category_id: str | None = None


class AttributeDefinitionUpdate(BaseModel):
    label: str | None = None
    type: str | None = None
    required: bool | None = None
    options_json: str | None = None


class AttributeFamilyRead(AttributeFamilyBase):
    id: str

    class Config:
        from_attributes = True

