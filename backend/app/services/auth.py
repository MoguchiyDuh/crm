from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import Unauthorized
from app.models.user import User

REFRESH_PREFIX = "refresh:"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "access"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "refresh"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


async def store_refresh_token(redis: Redis, user_id: int, token: str) -> None:
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await redis.set(f"{REFRESH_PREFIX}{user_id}", token, ex=ttl)


async def revoke_refresh_token(redis: Redis, user_id: int) -> None:
    await redis.delete(f"{REFRESH_PREFIX}{user_id}")


async def decode_access_token(token: str, redis: Redis) -> int:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise Unauthorized("Invalid token")

    if payload.get("type") != "access":
        raise Unauthorized("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise Unauthorized("Invalid token")

    return int(user_id)


async def validate_refresh_token(redis: Redis, token: str) -> int:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise Unauthorized("Invalid refresh token")

    if payload.get("type") != "refresh":
        raise Unauthorized("Invalid token type")

    user_id = int(payload["sub"])
    stored = await redis.get(f"{REFRESH_PREFIX}{user_id}")
    if stored != token:
        raise Unauthorized("Refresh token revoked or invalid")

    return user_id


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
