"""FTS search tests — require a live PostgreSQL instance."""
import pytest
from sqlalchemy import text

pytestmark = pytest.mark.postgres


async def _ensure_refs(pg_db) -> tuple[int, int]:
    """Return (status_id, priority_id), inserting defaults if absent."""
    row = (await pg_db.execute(text("SELECT id FROM project_statuses LIMIT 1"))).fetchone()
    if row:
        status_id = row[0]
    else:
        status_id = (
            await pg_db.execute(
                text("INSERT INTO project_statuses (name, is_default) VALUES ('Active', true) RETURNING id")
            )
        ).scalar_one()

    row = (await pg_db.execute(text("SELECT id FROM project_priorities LIMIT 1"))).fetchone()
    if row:
        priority_id = row[0]
    else:
        priority_id = (
            await pg_db.execute(
                text("INSERT INTO project_priorities (name) VALUES ('Normal') RETURNING id")
            )
        ).scalar_one()

    await pg_db.commit()
    return status_id, priority_id


async def _seed(pg_db):
    """Insert a project and an employee with known names."""
    status_id, priority_id = await _ensure_refs(pg_db)
    await pg_db.execute(
        text(
            "INSERT INTO projects (name, description, status_id, priority_id, progress, created_at, updated_at) "
            "VALUES (:name, :desc, :sid, :pid, 0, NOW(), NOW())"
        ),
        {"name": "AlphaTest Project", "desc": "something about alphatest", "sid": status_id, "pid": priority_id},
    )
    await pg_db.execute(
        text("INSERT INTO employees (full_name, role, is_active) VALUES (:name, :role, true)"),
        {"name": "ZetaWorker Jones", "role": "developer"},
    )
    await pg_db.commit()


async def test_search_requires_auth(pg_client):
    resp = await pg_client.get("/api/search", params={"q": "alpha"})
    assert resp.status_code == 401


async def test_search_missing_query(pg_auth_client):
    resp = await pg_auth_client.get("/api/search")
    assert resp.status_code == 422


@pytest.mark.usefixtures("pg_clean")
async def test_search_single_char_returns_empty(pg_auth_client):
    resp = await pg_auth_client.get("/api/search", params={"q": "a"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["projects"] == []
    assert data["employees"] == []


@pytest.mark.usefixtures("pg_clean")
async def test_search_finds_project(pg_auth_client, pg_db, pg_admin):
    await _seed(pg_db)
    resp = await pg_auth_client.get("/api/search", params={"q": "alphatest"})
    assert resp.status_code == 200
    data = resp.json()
    assert any(p["name"] == "AlphaTest Project" for p in data["projects"])


@pytest.mark.usefixtures("pg_clean")
async def test_search_finds_employee(pg_auth_client, pg_db, pg_admin):
    await _seed(pg_db)
    resp = await pg_auth_client.get("/api/search", params={"q": "zetaworker"})
    assert resp.status_code == 200
    data = resp.json()
    assert any(e["full_name"] == "ZetaWorker Jones" for e in data["employees"])


@pytest.mark.usefixtures("pg_clean")
async def test_search_no_results(pg_auth_client, pg_admin):
    resp = await pg_auth_client.get("/api/search", params={"q": "xyznonexistent"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["projects"] == []
    assert data["employees"] == []


@pytest.mark.usefixtures("pg_clean")
async def test_search_response_structure(pg_auth_client, pg_db, pg_admin):
    await _seed(pg_db)
    resp = await pg_auth_client.get("/api/search", params={"q": "alphatest"})
    assert resp.status_code == 200
    data = resp.json()
    assert "projects" in data and "employees" in data
    if data["projects"]:
        p = data["projects"][0]
        assert {"id", "name", "rank"} <= p.keys()


@pytest.mark.usefixtures("pg_clean")
async def test_search_rank_ordering(pg_auth_client, pg_db, pg_admin):
    """More specific match should rank higher."""
    status_id, priority_id = await _ensure_refs(pg_db)
    for name, desc in [
        ("AlphaTest Focused", "alphatest alphatest alphatest"),
        ("AlphaTest Sparse", "unrelated stuff"),
    ]:
        await pg_db.execute(
            text(
                "INSERT INTO projects (name, description, status_id, priority_id, progress, created_at, updated_at) "
                "VALUES (:name, :desc, :sid, :pid, 0, NOW(), NOW())"
            ),
            {"name": name, "desc": desc, "sid": status_id, "pid": priority_id},
        )
    await pg_db.commit()

    resp = await pg_auth_client.get("/api/search", params={"q": "alphatest"})
    assert resp.status_code == 200
    projects = resp.json()["projects"]
    assert len(projects) >= 2
    ranks = [p["rank"] for p in projects]
    assert ranks == sorted(ranks, reverse=True)
