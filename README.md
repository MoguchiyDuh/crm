# CRM

Internal project management CRM for small agencies/studios. Track projects, team, meetings, and activity.

## Stack

| Layer         | Tech                                                                  |
| ------------- | --------------------------------------------------------------------- |
| Backend       | FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2                 |
| Auth          | JWT access tokens (30m) + refresh tokens (7d, stored in Redis)        |
| Cache         | Redis — reference data (10m TTL), employee list (5m TTL)              |
| Rate limiting | Redis-backed — 10 req/min on login, 300 req/min general               |
| Database      | PostgreSQL 16                                                         |
| Search        | PostgreSQL FTS — tsvector + GIN index + websearch_to_tsquery          |
| Frontend      | React 19, TypeScript, Vite, TanStack Query v5, shadcn/ui, Tailwind v4 |
| Runtime       | Docker + docker-compose                                               |
| CI/CD         | GitHub Actions — test → deploy (SSH)                                  |

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

**Roles:** `admin` — full access including user management and reference data. `member` — projects, team, meetings. No public registration — accounts are created by admin.

## Features

- **Projects** — status, priority, manager, dates, budget, progress, tags, client info
- **Team** — employee directory with soft delete; link employees to user accounts
- **Meetings** — scheduling, participants, status tracking
- **Activity log** — audit trail for all mutations; admins see all, members see own
- **File attachments** — upload/download per project (50 MB cap, stored on Docker volume)
- **Dashboard stats** — totals, breakdowns by status/priority, overdue count
- **Full-text search** — Cmd+K command palette; searches projects and employees via PG FTS
- **WebSocket live push** — all mutations broadcast in real time; UI invalidates queries automatically
- **Rate limiting** — Redis-backed per-IP limits

## Project structure

```
crm/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, lifespan, CORS, rate limit middleware
│   │   ├── config.py          # pydantic-settings
│   │   ├── database.py        # async SQLAlchemy engine + session
│   │   ├── redis.py           # Redis client singleton
│   │   ├── deps.py            # FastAPI dependencies (db, redis, current_user)
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic v2 request/response schemas
│   │   ├── routers/           # auth, projects, employees, meetings, users,
│   │   │                      # activity, stats, attachments, search, ws
│   │   └── services/          # auth (JWT/bcrypt), activity log, WebSocket manager
│   ├── alembic/               # migrations (initial + features + FTS)
│   ├── scripts/seed.py        # idempotent seed (9 employees, 5 projects, 3 meetings)
│   └── tests/                 # pytest-asyncio; SQLite + fake Redis for unit tests,
│                              # real PostgreSQL for FTS tests (pytest.mark.postgres)
├── frontend/
│   ├── src/
│   │   ├── pages/             # Dashboard, ProjectDetail, Employees, Activity, Login
│   │   ├── components/        # shadcn/ui primitives + layout + SearchModal + AttachmentList
│   │   ├── hooks/             # TanStack Query hooks + useWebSocket + useSearch
│   │   ├── lib/               # axios client (auto token refresh), utils
│   │   └── types/             # shared TypeScript types
│   └── nginx.conf             # reverse proxy + WebSocket upgrade
├── .github/workflows/
│   └── deploy.yml             # test job (postgres service) → deploy job (SSH)
└── docker-compose.yml
```

## API

All routes under `/api/`. Protected with Bearer JWT unless noted.

```
POST   /api/auth/login          # returns access_token + refresh_token
POST   /api/auth/refresh
POST   /api/auth/logout
GET    /api/auth/me
PATCH  /api/users/me

GET    /api/users               # admin
POST   /api/users               # admin
DELETE /api/users/:id           # admin

GET    /api/projects            # ?status_id= &priority_id= &manager_id= &search=
POST   /api/projects
GET    /api/projects/:id
PATCH  /api/projects/:id
DELETE /api/projects/:id
GET    /api/projects/:id/attachments
POST   /api/projects/:id/attachments
GET    /api/attachments/:id/download
DELETE /api/attachments/:id

GET    /api/employees
POST   /api/employees
GET    /api/employees/:id
PATCH  /api/employees/:id
DELETE /api/employees/:id       # soft delete
POST   /api/employees/:id/link  # admin — link to user account
DELETE /api/employees/:id/link  # admin

GET    /api/meetings
POST   /api/meetings
GET    /api/meetings/:id
PATCH  /api/meetings/:id
DELETE /api/meetings/:id
POST   /api/meetings/:id/participants/:employee_id
DELETE /api/meetings/:id/participants/:employee_id

GET    /api/activity            # ?limit= &offset= &entity_type=
GET    /api/stats
GET    /api/search              # ?q= &limit=  (FTS — min 2 chars)

GET    /api/reference/statuses
POST   /api/reference/statuses  # admin
GET    /api/reference/priorities
POST   /api/reference/priorities # admin

WS     /ws?token=               # live push events
```

## WebSocket events

The `/ws` endpoint streams JSON events after every mutation:

```json
{"type": "project.created", "id": 1}
{"type": "employee.updated", "id": 3}
{"type": "meeting.deleted", "id": 2}
```

The frontend maps event types to TanStack Query cache keys and invalidates automatically.

## Tests

```bash
cd backend

# Unit tests — SQLite in-memory + fake Redis (no external deps)
uv run pytest tests/ -v

# FTS tests — require a live PostgreSQL instance
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/testdb \
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/testdb \
JWT_SECRET=secret \
uv run pytest tests/ -v -m postgres
```

## Development

**Backend** (requires uv):

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run python scripts/seed.py
uv run uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev                    # proxies /api and /ws -> localhost:8000
```

## CI/CD

Push to `main` triggers:
1. **test** — spins up `postgres:16`, runs `pytest tests/ -v` including FTS tests
2. **deploy** — SSH into the VPS, `git pull`, `docker compose build --no-cache`, restart

Secrets required: `DEPLOY_HOST`, `DEPLOY_PORT`, `DEPLOY_USER`, `DEPLOY_KEY`.

## Environment variables

| Variable                      | Default                     | Description                              |
| ----------------------------- | --------------------------- | ---------------------------------------- |
| `DATABASE_URL`                | —                           | `postgresql+asyncpg://user:pass@host/db` |
| `REDIS_URL`                   | `redis://localhost:6379/0`  | Redis connection                         |
| `JWT_SECRET`                  | —                           | Secret key for signing JWTs              |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                        | Access token TTL                         |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `7`                         | Refresh token TTL                        |
| `CORS_ORIGINS`                | `["http://localhost:5173"]` | JSON array of allowed origins            |
