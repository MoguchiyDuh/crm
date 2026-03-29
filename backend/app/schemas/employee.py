from pydantic import BaseModel, EmailStr


class EmployeeBase(BaseModel):
    full_name: str
    role: str
    telegram: str | None = None
    email: EmailStr | None = None
    notes: str | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    telegram: str | None = None
    email: EmailStr | None = None
    notes: str | None = None
    is_active: bool | None = None


class EmployeeOut(EmployeeBase):
    model_config = {"from_attributes": True}

    id: int
    is_active: bool
    user_id: int | None = None
