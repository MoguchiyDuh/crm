import pytest


@pytest.mark.asyncio
async def test_register(client):
    r = await client.post("/api/auth/register", json={"email": "user@test.com", "password": "pass123"})
    assert r.status_code == 201
    assert r.json()["email"] == "user@test.com"
    assert r.json()["role"] == "user"


@pytest.mark.asyncio
async def test_register_duplicate(client):
    await client.post("/api/auth/register", json={"email": "dup@test.com", "password": "pass123"})
    r = await client.post("/api/auth/register", json={"email": "dup@test.com", "password": "pass123"})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_login(client, admin):
    r = await client.post("/api/auth/login", json={"email": "admin@test.com", "password": "secret"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin):
    r = await client.post("/api/auth/login", json={"email": "admin@test.com", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me(auth_client):
    r = await auth_client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_me_unauthenticated(client):
    r = await client.get("/api/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh(client, admin):
    r = await client.post("/api/auth/login", json={"email": "admin@test.com", "password": "secret"})
    refresh = r.json()["refresh_token"]
    r2 = await client.post("/api/auth/refresh", json={"refresh_token": refresh})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


@pytest.mark.asyncio
async def test_logout(auth_client, admin):
    r = await auth_client.post("/api/auth/logout")
    assert r.status_code == 204
