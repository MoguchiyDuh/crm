from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import current_user, db_session
from app.models.user import User
from app.schemas.search import EmployeeSearchResult, ProjectSearchResult, SearchOut

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchOut)
async def search(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(db_session),
    _: User = Depends(current_user),
) -> SearchOut:
    q = q.strip()
    if not q:
        return SearchOut(projects=[], employees=[])

    projects_rows = (
        await db.execute(
            text("""
                SELECT id, name, client_name,
                       ts_rank(search_vector, query) AS rank
                FROM projects,
                     websearch_to_tsquery('english', :q) query
                WHERE search_vector @@ query
                ORDER BY rank DESC
                LIMIT :limit
            """),
            {"q": q, "limit": limit},
        )
    ).fetchall()

    employees_rows = (
        await db.execute(
            text("""
                SELECT id, full_name, role,
                       ts_rank(search_vector, query) AS rank
                FROM employees,
                     websearch_to_tsquery('english', :q) query
                WHERE search_vector @@ query
                  AND is_active = true
                ORDER BY rank DESC
                LIMIT :limit
            """),
            {"q": q, "limit": limit},
        )
    ).fetchall()

    return SearchOut(
        projects=[
            ProjectSearchResult(id=r.id, name=r.name, client_name=r.client_name, rank=r.rank)
            for r in projects_rows
        ],
        employees=[
            EmployeeSearchResult(id=r.id, full_name=r.full_name, role=r.role, rank=r.rank)
            for r in employees_rows
        ],
    )
