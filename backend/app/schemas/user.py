from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "viewer"
    scopes: list[str] = []


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    scopes: list[str] | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    scopes: list[str]
    is_active: bool

    model_config = {"from_attributes": True}


class PasswordChange(BaseModel):
    current_password: str | None = None
    new_password: str
