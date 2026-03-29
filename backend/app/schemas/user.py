from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "member"


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    role: str
    is_active: bool


class UpdateMe(BaseModel):
    email: str | None = None
    current_password: str | None = None
    new_password: str | None = None
