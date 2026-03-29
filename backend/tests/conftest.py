import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import patch

from app.database import Base
from app.deps import db_session, redis_client
from app.main import app
from app.models.user import User
from app.services.auth import hash_password

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class FakeRedis:
    def __init__(self):
        self._store: dict = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    async def delete(self, *keys: str) -> None:
        for k in keys:
            self._store.pop(k, None)

    async def incr(self, key: str) -> int:
        val = int(self._store.get(key) or 0) + 1
        self._store[key] = str(val)
        return val

    async def expire(self, key: str, seconds: int) -> None:
        pass  # no-op in tests


fake_redis = FakeRedis()


async def override_db():
    async with TestSession() as session:
        yield session


async def override_redis():
    return fake_redis


async def _fake_get_redis():
    return fake_redis


@pytest.fixture(scope="session", autouse=True)
def event_loop_policy():
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    fake_redis._store.clear()


@pytest_asyncio.fixture
async def db():
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[db_session] = override_db
    app.dependency_overrides[redis_client] = override_redis
    with patch("app.main.get_redis", _fake_get_redis):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin(db):
    user = User(email="admin@test.com", password_hash=hash_password("secret"), role="admin")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def member(db):
    user = User(email="member@test.com", password_hash=hash_password("secret"), role="member")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_client(client, admin):
    resp = await client.post("/api/auth/login", json={"email": "admin@test.com", "password": "secret"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
async def member_client(client, member):
    resp = await client.post("/api/auth/login", json={"email": "member@test.com", "password": "secret"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    # Return a fresh client-like object sharing the same underlying client
    client.headers["Authorization"] = f"Bearer {token}"
    return client
