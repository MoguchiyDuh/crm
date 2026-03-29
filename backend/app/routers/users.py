from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import admin_user, current_user, db_session
from app.exceptions import BadRequest, Conflict, NotFound
from app.models.user import User
from app.schemas.user import UpdateMe, UserCreate, UserOut
from app.services.activity import log_activity
from app.services.ws import manager
from app.services.auth import get_user_by_email, hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(db_session),
    _: User = Depends(admin_user),
) -> list[User]:
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()


@router.post("", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(db_session),
    me: User = Depends(admin_user),
) -> User:
    if await get_user_by_email(db, body.email):
        raise Conflict("Email already registered")
    if body.role not in ("admin", "member"):
        raise BadRequest("Role must be 'admin' or 'member'")
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.flush()
    await log_activity(db, me.id, "created", "user", user.id, user.email)
    await db.commit()
    await db.refresh(user)
    await manager.broadcast("user.created", id=user.id)
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(db_session),
    me: User = Depends(admin_user),
) -> None:
    if user_id == me.id:
        raise BadRequest("Cannot delete yourself")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFound("User")
    await log_activity(db, me.id, "deleted", "user", user.id, user.email)
    await db.delete(user)
    await db.commit()
    await manager.broadcast("user.deleted", id=user_id)


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UpdateMe,
    db: AsyncSession = Depends(db_session),
    me: User = Depends(current_user),
) -> User:
    if body.email and body.email != me.email:
        if await get_user_by_email(db, body.email):
            raise Conflict("Email already taken")
        me.email = body.email

    if body.new_password:
        if not body.current_password:
            raise BadRequest("current_password required to set a new password")
        if not verify_password(body.current_password, me.password_hash):
            raise BadRequest("Wrong current password")
        me.password_hash = hash_password(body.new_password)

    await db.commit()
    await db.refresh(me)
    return me
