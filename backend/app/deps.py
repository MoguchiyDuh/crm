from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.exceptions import Unauthorized
from app.models.user import User
from app.redis import get_redis
from app.services.auth import decode_access_token, get_user_by_id

bearer = HTTPBearer(auto_error=False)


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def redis_client() -> Redis:
    return await get_redis()


async def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(db_session),
    redis: Redis = Depends(redis_client),
) -> User:
    if not creds:
        raise Unauthorized()
    token = creds.credentials
    user_id = await decode_access_token(token, redis)
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise Unauthorized()
    return user


async def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        from app.exceptions import Forbidden
        raise Forbidden()
    return user
