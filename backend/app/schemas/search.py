from pydantic import BaseModel


class ProjectSearchResult(BaseModel):
    id: int
    name: str
    client_name: str | None
    rank: float


class EmployeeSearchResult(BaseModel):
    id: int
    full_name: str
    role: str
    rank: float


class SearchOut(BaseModel):
    projects: list[ProjectSearchResult]
    employees: list[EmployeeSearchResult]
