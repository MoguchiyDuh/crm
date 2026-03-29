from pydantic import BaseModel


class ProjectStatusOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    is_default: bool


class ProjectStatusCreate(BaseModel):
    name: str
    is_default: bool = False


class ProjectPriorityOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    order: int | None
    color: str | None


class ProjectPriorityCreate(BaseModel):
    name: str
    order: int | None = None
    color: str | None = None
