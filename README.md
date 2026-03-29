# CRM

Internal project management CRM for small agencies/studios. Track projects, team, and meetings.

## Stack

| Layer    | Tech                                                                  |
| -------- | --------------------------------------------------------------------- |
| Backend  | FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2                 |
| Auth     | JWT access tokens (30m) + refresh tokens (7d, stored in Redis)        |
| Cache    | Redis — reference data (10m TTL), employee list (5m TTL)              |
| Database | PostgreSQL 16                                                         |
| Frontend | React 19, TypeScript, Vite, TanStack Query v5, shadcn/ui, Tailwind v4 |
| Runtime  | Docker + docker-compose                                               |

## Quick start

```bash
git clone <repo>
cd crm
docker-compose up --build -d
```

| Service     | URL                        |
| ----------- | -------------------------- |
| Frontend    | http://localhost:80        |
| Backend API | http://localhost:8000      |
| API docs    | http://localhost:8000/docs |

Default admin account: `admin@example.com` / `admin1234`

## Project structure

```
crm/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, lifespan, CORS
│   │   ├── config.py          # pydantic-settings
│   │   ├── database.py        # async SQLAlchemy engine + session
│   │   ├── redis.py           # Redis client singleton
│   │   ├── deps.py            # FastAPI dependencies (db, redis, current_user)
│   │   ├── exceptions.py      # HTTP exception types
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic v2 request/response schemas
│   │   ├── routers/           # FastAPI routers (auth, projects, employees, meetings, reference)
│   │   └── services/          # auth (JWT/bcrypt), cache (Redis helpers)
│   ├── alembic/               # migrations
│   ├── scripts/seed.py        # idempotent seed (9 employees, 5 projects, 3 meetings)
│   └── tests/                 # pytest-asyncio, SQLite in-memory, fake Redis
├── frontend/
│   ├── src/
│   │   ├── pages/             # Dashboard, ProjectDetail, Employees, Login
│   │   ├── components/        # shadcn/ui primitives + layout + common
│   │   ├── hooks/             # TanStack Query hooks per domain
│   │   ├── lib/               # axios client (auto token refresh), utils
│   │   └── types/             # shared TypeScript types
│   └── nginx.conf
└── docker-compose.yml
```

## API

All routes under `/api/`. Protected with Bearer JWT unless noted.

```
POST   /api/auth/register
POST   /api/auth/login          # returns access_token + refresh_token
POST   /api/auth/refresh
POST   /api/auth/logout
GET    /api/auth/me

GET    /api/projects            # ?status_id= &priority_id= &manager_id= &search=
POST   /api/projects
GET    /api/projects/:id
PATCH  /api/projects/:id
DELETE /api/projects/:id

GET    /api/employees
POST   /api/employees
GET    /api/employees/:id
PATCH  /api/employees/:id
DELETE /api/employees/:id       # soft delete (is_active=false)

GET    /api/meetings
POST   /api/meetings
GET    /api/meetings/:id
PATCH  /api/meetings/:id
DELETE /api/meetings/:id
POST   /api/meetings/:id/participants/:employee_id
DELETE /api/meetings/:id/participants/:employee_id

GET    /api/reference/statuses
POST   /api/reference/statuses  # admin only
GET    /api/reference/priorities
POST   /api/reference/priorities # admin only
```

## Development

**Backend** (requires uv):

```bash
cd backend
cp .env.example .env           # fill DATABASE_URL, REDIS_URL, JWT_SECRET
uv sync
uv run alembic upgrade head
uv run python scripts/seed.py
uv run uvicorn app.main:app --reload
```

**Tests** (no DB/Redis needed — SQLite + fake Redis):

```bash
cd backend
uv run pytest tests/ -v
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev                    # proxies /api -> localhost:8000
```

## Environment variables

| Variable                      | Default                     | Description                              |
| ----------------------------- | --------------------------- | ---------------------------------------- |
| `DATABASE_URL`                | —                           | `postgresql+asyncpg://user:pass@host/db` |
| `REDIS_URL`                   | `redis://localhost:6379/0`  | Redis connection                         |
| `JWT_SECRET`                  | —                           | Secret key for signing JWTs              |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                        | Access token TTL                         |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `7`                         | Refresh token TTL                        |
| `CORS_ORIGINS`                | `["http://localhost:5173"]` | JSON array of allowed origins            |
