from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import current_user, db_session, redis_client
from app.exceptions import BadRequest, Unauthorized
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserOut
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    get_user_by_email,
    hash_password,
    revoke_refresh_token,
    store_refresh_token,
    validate_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(db_session),
) -> User:
    existing = await get_user_by_email(db, body.email)
    if existing:
        raise BadRequest("Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
) -> TokenResponse:
    user = await get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise Unauthorized("Invalid credentials")
    if not user.is_active:
        raise Unauthorized("Account disabled")

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    await store_refresh_token(redis, user.id, refresh)

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    redis: Redis = Depends(redis_client),
) -> TokenResponse:
    user_id = await validate_refresh_token(redis, body.refresh_token)
    access = create_access_token(user_id)
    refresh = create_refresh_token(user_id)
    await store_refresh_token(redis, user_id, refresh)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/logout", status_code=204)
async def logout(
    user: User = Depends(current_user),
    redis: Redis = Depends(redis_client),
) -> None:
    await revoke_refresh_token(redis, user.id)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user)) -> User:
    return user
