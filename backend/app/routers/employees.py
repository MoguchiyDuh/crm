from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import current_user, db_session, redis_client
from app.exceptions import NotFound
from app.models.employee import Employee
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeOut, EmployeeUpdate
from app.services.cache import EMPLOYEES_KEY, EMPLOYEES_TTL, cached, invalidate

router = APIRouter(prefix="/employees", tags=["employees"])


async def _load_employees(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Employee).where(Employee.is_active == True))  # noqa: E712
    rows = result.scalars().all()
    return [EmployeeOut.model_validate(r).model_dump() for r in rows]


@router.get("", response_model=list[EmployeeOut])
async def list_employees(
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
    _: User = Depends(current_user),
) -> list[EmployeeOut]:
    data = await cached(redis, EMPLOYEES_KEY, EMPLOYEES_TTL, lambda: _load_employees(db))
    return [EmployeeOut(**item) for item in data]


@router.post("", response_model=EmployeeOut, status_code=201)
async def create_employee(
    body: EmployeeCreate,
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
    _: User = Depends(current_user),
) -> Employee:
    employee = Employee(**body.model_dump())
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    await invalidate(redis, EMPLOYEES_KEY)
    return employee


@router.get("/{employee_id}", response_model=EmployeeOut)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> Employee:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFound("Employee")
    return employee


@router.patch("/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: int,
    body: EmployeeUpdate,
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
    _: User = Depends(current_user),
) -> Employee:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFound("Employee")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)

    await db.commit()
    await db.refresh(employee)
    await invalidate(redis, EMPLOYEES_KEY)
    return employee


@router.delete("/{employee_id}", status_code=204)
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
    _: User = Depends(current_user),
) -> None:
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise NotFound("Employee")

    employee.is_active = False
    await db.commit()
    await invalidate(redis, EMPLOYEES_KEY)
