import os
import subprocess

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
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


# ---------------------------------------------------------------------------
# PostgreSQL fixtures (pytest.mark.postgres)
# ---------------------------------------------------------------------------

PG_URL = os.environ.get("TEST_DATABASE_URL", "")
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _make_pg_session():
    """New engine+session with NullPool — connection closed immediately after use."""
    eng = create_async_engine(PG_URL, poolclass=NullPool)
    return AsyncSession(bind=eng, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=False)
def _pg_migrate():
    """Run alembic migrations once per session if TEST_DATABASE_URL is set."""
    if not PG_URL:
        return
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        cwd=_BACKEND_DIR,
        env={**os.environ, "DATABASE_URL": PG_URL},
    )
    if result.returncode != 0:
        pytest.fail(f"alembic upgrade failed:\n{result.stderr}")


@pytest_asyncio.fixture
async def pg_db(_pg_migrate):
    if not PG_URL:
        pytest.skip("TEST_DATABASE_URL not set")
    async with _make_pg_session() as session:
        yield session


@pytest_asyncio.fixture(autouse=False)
async def pg_clean(pg_db):
    """DELETE all rows from every table after the test (NullPool = no lock contention)."""
    yield
    for table in reversed(Base.metadata.sorted_tables):
        await pg_db.execute(sa_text(f"DELETE FROM {table.name}"))
    await pg_db.commit()


@pytest_asyncio.fixture
async def pg_client(_pg_migrate):
    if not PG_URL:
        pytest.skip("TEST_DATABASE_URL not set")

    async def _override_db():
        async with _make_pg_session() as session:
            yield session

    app.dependency_overrides[db_session] = _override_db
    app.dependency_overrides[redis_client] = override_redis
    with patch("app.main.get_redis", _fake_get_redis):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def pg_admin():
    if not PG_URL:
        pytest.skip("TEST_DATABASE_URL not set")
    async with _make_pg_session() as session:
        await session.execute(sa_text("DELETE FROM users WHERE email = 'pg_admin@test.com'"))
        await session.commit()
        user = User(email="pg_admin@test.com", password_hash=hash_password("secret"), role="admin")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user
        await session.execute(sa_text("DELETE FROM users WHERE email = 'pg_admin@test.com'"))
        await session.commit()


@pytest_asyncio.fixture
async def pg_auth_client(pg_client, pg_admin):
    resp = await pg_client.post("/api/auth/login", json={"email": "pg_admin@test.com", "password": "secret"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    pg_client.headers["Authorization"] = f"Bearer {token}"
    return pg_client
