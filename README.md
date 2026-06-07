# Job Tracker Backend

A RESTful API for the Job Application Tracker — built with FastAPI and PostgreSQL. Supports user authentication, job application tracking, interview round management, and a full admin panel with role-based access control and audit logging.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Makefile Commands](#makefile-commands)
- [Docker Setup](#docker-setup)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Deployment](#deployment)

---

## Project Overview

Job Tracker Backend provides a secure JSON API that powers the Job Application Tracker web app. Key features:

- **Cookie-based JWT authentication** — httpOnly cookie issued on login; Bearer token header also supported as a fallback
- **Job application CRUD** — create, read, update, and delete job applications with paginated listing
- **Interview round tracking** — attach multiple interview rounds to any job application; round numbers are assigned automatically
- **Per-user data isolation** — users can only access their own records
- **Role-based access control** — three tiers: `user` → `admin` → `superadmin`
- **Admin panel** — user management, status toggling, role promotion, and platform statistics
- **Audit log** — every admin mutation (role change, status toggle, deletion) is recorded to a dedicated audit table
- **Database migrations** — full schema versioning via Alembic
- **Input validation** — request and response validation via Pydantic v2

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) 0.128 |
| Language | Python 3.9+ |
| Database | PostgreSQL 16 |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) 1.16 |
| Validation | [Pydantic](https://docs.pydantic.dev/) v2 |
| Authentication | JWT via [python-jose](https://github.com/mpdavis/python-jose) |
| Password hashing | [bcrypt](https://github.com/pyca/bcrypt/) 5.0 |
| Server | [Uvicorn](https://www.uvicorn.org/) |

---

## Project Structure

```
job-tracker-backend/
├── app/
│   ├── main.py                    # App entry point, CORS middleware, router registration
│   ├── config.py                  # Settings loaded from .env via pydantic-settings
│   ├── database.py                # SQLAlchemy engine, session factory, get_db dependency
│   │
│   ├── models/
│   │   ├── base.py                # SQLAlchemy DeclarativeBase
│   │   ├── user.py                # User model (id, email, username, role, is_active)
│   │   ├── job_application.py     # JobApplication model + ApplicationStatus enum
│   │   ├── interview_round.py     # InterviewRound model + InterviewType enum
│   │   └── audit_log.py           # AuditLog model (actor, action, target_type/id, detail)
│   │
│   ├── schemas/
│   │   ├── types.py               # Shared Pydantic types (DatetimeFormatted)
│   │   ├── user.py                # UserRegister, UserLogin, UserResponse, TokenResponse, UserProfileUpdate
│   │   ├── job_application.py     # JobApplicationCreate, Update, Response, PaginatedJobsResponse
│   │   ├── interview_round.py     # InterviewRoundCreate, Update, Response
│   │   └── admin.py               # UserAdminResponse, RoleUpdateRequest, StatsOverviewResponse, AuditLogResponse
│   │
│   ├── routers/
│   │   ├── auth.py                # POST /auth/register, /auth/login, /auth/logout · GET /auth/me
│   │   ├── jobs.py                # GET/POST /jobs, GET/PUT/DELETE /jobs/{id}
│   │   ├── interview_rounds.py    # Full CRUD under /jobs/{job_id}/interviews
│   │   ├── users.py               # GET/PUT/DELETE /users/me
│   │   └── admin.py               # /admin/users, /admin/stats/overview, /admin/audit-log
│   │
│   ├── services/
│   │   ├── auth_service.py        # User lookup, creation, authentication
│   │   ├── job_service.py         # Job application CRUD + paginated queries
│   │   ├── interview_service.py   # Interview round CRUD; auto-assigns round_number
│   │   └── admin_service.py       # Admin ops: user management, stats, audit log writes
│   │
│   ├── utils/
│   │   └── security.py            # Password hashing (bcrypt), JWT encode/decode
│   │
│   └── dependencies/
│       └── auth.py                # get_current_user, require_admin, require_superadmin
│
├── alembic/
│   ├── env.py                     # Alembic runtime config — wired to SQLAlchemy models
│   ├── script.py.mako             # Migration file template
│   └── versions/
│       ├── 0408b69a93c1_add_user_table.py
│       ├── 007ea04b7f23_add_job_applications_table.py
│       ├── 1c466a497ce3_add_interview_rounds_table.py
│       ├── f7e97e8dcb2e_add_role_to_users.py
│       └── 03547cddd285_add_audit_log_table.py   ← current head
│
├── scripts/
│   └── seed_ci_superadmin.py      # Seeds a superadmin into CI/prod PostgreSQL (idempotent)
│
├── tests/
│   ├── conftest.py                # SQLite in-memory fixtures, TestClient, user/admin/superadmin helpers
│   ├── test_auth.py               # 14 tests — register, login, logout, /me
│   ├── test_jobs.py               # 14 tests — job application CRUD + pagination
│   ├── test_interviews.py         # 9 tests  — interview round CRUD
│   └── test_admin.py              # 40 tests — user management, stats, audit log, RBAC
│
├── .github/workflows/ci.yml       # GitHub Actions — runs pytest on every push/PR to main
├── alembic.ini                    # Alembic configuration
├── docker-compose.yml             # Local dev: PostgreSQL + backend with hot reload
├── Dockerfile                     # Production container image
├── Makefile                       # Developer shortcut commands
├── pytest.ini                     # Pytest configuration
├── railway.json                   # Railway.app deployment config
├── requirements.txt               # Pinned Python dependencies
├── start.sh                       # Container entrypoint (runs migrations, then uvicorn)
├── .env                           # Local environment variables (not committed)
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 16 (local install or a hosted instance)
- `make` (comes pre-installed on macOS and Linux)

### 1. Clone the repo

```bash
git clone https://github.com/QA-Master505/job-tracker-backend.git
cd job-tracker-backend
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
# or
make install
```

### 4. Set up the `.env` file

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then edit the values — see [Environment Variables](#environment-variables) for details.

### 5. Create the database

```bash
# macOS with Homebrew
brew services start postgresql@16
createdb -U postgres job_tracker_db
```

### 6. Run migrations

```bash
alembic upgrade head
# or
make migrate
```

### 7. Start the development server

```bash
uvicorn app.main:app --reload
# or
make run
```

The API is now available at:

- **Base URL:** `http://localhost:8000`
- **Interactive docs (Swagger):** `http://localhost:8000/docs`
- **Alternative docs (ReDoc):** `http://localhost:8000/redoc`

---

## Makefile Commands

| Command | Description | Original Command |
|---------|-------------|-----------------|
| `make run` | Start dev server (requires venv activated) | `uvicorn app.main:app --reload` |
| `make dev` | Start dev server on `0.0.0.0:8000` | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| `make start` | Start dev server via `.venv` directly | `.venv/bin/uvicorn app.main:app --reload` |
| `make install` | Install all packages from `requirements.txt` | `.venv/bin/pip install -r requirements.txt` |
| `make freeze` | Overwrite `requirements.txt` with current packages | `.venv/bin/pip freeze > requirements.txt` |
| `make migrate` | Apply all pending database migrations | `alembic upgrade head` |
| `make migration MSG="description"` | Create a new autogenerated migration | `alembic revision --autogenerate -m "description"` |
| `make rollback` | Roll back the most recent migration | `alembic downgrade -1` |
| `make test` | Run the test suite | `.venv/bin/pytest` |
| `make help` | Print the full command reference | `@echo ...` |

**Examples:**

```bash
# Apply all pending migrations
make migrate

# Create a new migration after changing a model
make migration MSG="add salary field to job applications"

# Roll back if something went wrong
make rollback
```

---

## Docker Setup

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Docker Compose (included with Docker Desktop)

### Quick Start

Start the database and backend with a single command:

```bash
make docker-up
```

This builds the image, starts PostgreSQL, waits for it to be healthy, runs all pending migrations, then starts the API server with hot reload.

### Services

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

### Docker Commands

| Command | Description | Original Command |
|---------|-------------|-----------------|
| `make docker-up` | Start all services (with build) | `docker-compose up --build` |
| `make docker-start` | Start in background | `docker-compose up -d --build` |
| `make docker-stop` | Stop all containers | `docker-compose down` |
| `make docker-clean` | Stop and remove volumes (clean slate) | `docker-compose down -v` |
| `make docker-logs` | Stream logs from all services | `docker-compose logs -f` |
| `make docker-logs-backend` | Stream backend logs only | `docker-compose logs -f backend` |
| `make docker-logs-db` | Stream database logs only | `docker-compose logs -f db` |
| `make docker-migrate` | Run migrations inside the container | `docker-compose exec backend alembic upgrade head` |
| `make docker-db-shell` | Open a psql shell | `docker-compose exec db psql -U postgres -d job_tracker_db` |
| `make docker-shell` | Open bash in the backend container | `docker-compose exec backend bash` |
| `make docker-rebuild` | Tear down and rebuild everything | `docker-compose down && docker-compose up --build` |

### How it works

```
docker-compose up --build
        │
        ├─ builds backend image (python:3.11-slim + requirements.txt)
        │
        ├─ starts postgres:16 container
        │        └─ waits for healthcheck (pg_isready)
        │
        └─ starts backend container
                 ├─ alembic upgrade head   ← runs migrations automatically
                 └─ uvicorn app.main:app --reload
```

### Notes

- PostgreSQL data is persisted in a Docker named volume (`postgres_data`). Run `make docker-clean` to wipe it.
- The backend mounts `.:/app` so code changes are reflected immediately without rebuilding the image.
- Environment variables in `docker-compose.yml` are for **development only**. Never use these values in production.
- A local `.env` file will **not** be read inside the container — set variables directly in `docker-compose.yml` or pass them with `docker-compose --env-file`.

---

## API Endpoints

All endpoints return JSON. Protected endpoints require authentication via the `access_token` httpOnly cookie (set automatically on login) or an `Authorization: Bearer <token>` header.

### Health Check

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | No | Returns API and database status |

```json
// GET /health
{
  "status": "ok",
  "app": "Job Tracker API",
  "database": "connected"
}
```

---

### Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | No | Register a new user |
| `POST` | `/auth/login` | No | Login — sets httpOnly cookie and returns token |
| `GET` | `/auth/me` | Yes | Get the currently authenticated user |
| `POST` | `/auth/logout` | Yes | Clear the auth cookie |

**Register** — `POST /auth/register`

```json
// Request body
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword"
}

// Response 201
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "role": "user",
  "created_at": "2026-05-20T21:22:40"
}
```

**Login** — `POST /auth/login`

Sets an `access_token` httpOnly cookie and also returns the token in the response body for clients that prefer Bearer header auth.

```json
// Request body
{
  "email": "user@example.com",
  "password": "securepassword"
}

// Response 200
// Sets: Set-Cookie: access_token=<jwt>; HttpOnly; SameSite=Lax
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Get current user** — `GET /auth/me`

```json
// Response 200
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "role": "user",
  "created_at": "2026-05-20T21:22:40"
}
```

**Logout** — `POST /auth/logout`

Clears the `access_token` cookie. Returns `200` with a confirmation message.

---

### Users

All `/users` endpoints require authentication.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/users/me` | Yes | Get the authenticated user's profile |
| `PUT` | `/users/me` | Yes | Update username, email, or password |
| `DELETE` | `/users/me` | Yes | Permanently delete the authenticated user's account |

**Update profile** — `PUT /users/me`

Only include the fields you want to change. To change the password, both `current_password` and `new_password` are required.

```json
// Request body
{
  "username": "newusername",
  "email": "newemail@example.com",
  "current_password": "oldpass123",
  "new_password": "newpass456"
}
```

**Delete account** — `DELETE /users/me`

Returns `204 No Content`. Cascades to all owned job applications and interview rounds.

---

### Job Applications

All job application endpoints require authentication.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/jobs` | List job applications for the current user (paginated) |
| `POST` | `/jobs` | Create a new job application |
| `GET` | `/jobs/{id}` | Get a single job application |
| `PUT` | `/jobs/{id}` | Update a job application |
| `DELETE` | `/jobs/{id}` | Delete a job application |

**Query parameters for `GET /jobs`:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `page` | `1` | Page number |
| `page_size` | `20` | Results per page (max 100) |

**Application status values:** `applied` · `phone_interview` · `virtual_interview` · `onsite_interview` · `offer` · `rejected` · `no_response` · `withdrawn`

**Create** — `POST /jobs`

```json
// Request body
{
  "company_name": "Acme Corp",
  "job_title": "Backend Engineer",
  "job_url": "https://acme.com/jobs/123",
  "status": "applied",
  "applied_date": "2026-05-20",
  "notes": "Referred by a friend"
}

// Response 201
{
  "id": 1,
  "user_id": 1,
  "company_name": "Acme Corp",
  "job_title": "Backend Engineer",
  "job_url": "https://acme.com/jobs/123",
  "status": "applied",
  "applied_date": "2026-05-20",
  "notes": "Referred by a friend",
  "created_at": "2026-05-20T21:22:40",
  "updated_at": "2026-05-20T21:22:40"
}
```

**Paginated list response** — `GET /jobs`

```json
{
  "items": [ ... ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

**Update** — `PUT /jobs/{id}`

Only include the fields you want to change:

```json
{
  "status": "phone_interview",
  "notes": "Phone screen scheduled for Friday"
}
```

**Delete** — `DELETE /jobs/{id}`

Returns `204 No Content` on success.

---

### Interview Rounds

Interview rounds are nested under a job application. All endpoints require authentication and ownership of the parent job application.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/jobs/{job_id}/interviews` | List all interview rounds for a job application |
| `POST` | `/jobs/{job_id}/interviews` | Add a new interview round |
| `PUT` | `/jobs/{job_id}/interviews/{round_id}` | Update an interview round |
| `DELETE` | `/jobs/{job_id}/interviews/{round_id}` | Delete an interview round |

`round_number` is assigned automatically (MAX + 1) and is not part of the request body.

**Interview type values:** `phone` · `virtual` · `onsite` · `other`

**Add interview round** — `POST /jobs/{job_id}/interviews`

```json
// Request body
{
  "interview_type": "virtual",
  "interview_date": "2026-06-01",
  "notes": "Two-hour technical screen"
}

// Response 201
{
  "id": 1,
  "job_application_id": 1,
  "round_number": 1,
  "interview_type": "virtual",
  "interview_date": "2026-06-01",
  "notes": "Two-hour technical screen",
  "created_at": "2026-05-20T21:22:40",
  "updated_at": "2026-05-20T21:22:40"
}
```

**Update** — `PUT /jobs/{job_id}/interviews/{round_id}`

```json
{
  "interview_date": "2026-06-03",
  "notes": "Rescheduled to Monday"
}
```

**Delete** — `DELETE /jobs/{job_id}/interviews/{round_id}`

Returns `204 No Content` on success.

---

### Admin

Admin endpoints require the `admin` or `superadmin` role. Some actions are restricted to `superadmin` only — see the permission matrix below.

**Permission matrix:**

| Endpoint | `admin` | `superadmin` |
|----------|---------|--------------|
| `GET /admin/users` | Yes | Yes |
| `GET /admin/users/{id}` | Yes | Yes |
| `PATCH /admin/users/{id}/role` | No | Yes |
| `PATCH /admin/users/{id}/status` | Yes | Yes |
| `DELETE /admin/users/{id}` | No | Yes |
| `GET /admin/stats/overview` | Yes | Yes |
| `GET /admin/audit-log` | Yes | Yes |

**List users** — `GET /admin/users`

Supports optional query filters: `?role=admin`, `?is_active=true`, and pagination via `page` / `page_size`.

```json
// Response 200
{
  "items": [
    {
      "id": 1,
      "email": "user@example.com",
      "username": "johndoe",
      "is_active": true,
      "role": "user",
      "created_at": "2026-05-20T21:22:40",
      "job_count": 5
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

**Update role** — `PATCH /admin/users/{id}/role` *(superadmin only)*

```json
// Request body
{ "new_role": "admin" }
```

Valid values: `user` · `admin` · `superadmin`

**Toggle status** — `PATCH /admin/users/{id}/status`

Flips `is_active` between `true` and `false`. No request body required.

**Delete user** — `DELETE /admin/users/{id}` *(superadmin only)*

Returns `204 No Content`. Cascades to all owned job applications and interview rounds.

**Stats overview** — `GET /admin/stats/overview`

```json
{
  "total_users": 120,
  "active_users": 115,
  "total_jobs": 843,
  "jobs_by_status": {
    "applied": 310,
    "phone_interview": 140,
    "virtual_interview": 95,
    "onsite_interview": 42,
    "offer": 18,
    "rejected": 180,
    "no_response": 50,
    "withdrawn": 8
  }
}
```

**Audit log** — `GET /admin/audit-log`

Returns paginated admin actions ordered by most recent first.

```json
{
  "items": [
    {
      "id": 1,
      "actor_id": 2,
      "actor_email": "admin@example.com",
      "action": "user.role_change",
      "target_type": "user",
      "target_id": 5,
      "detail": "{\"old_role\": \"user\", \"new_role\": \"admin\"}",
      "created_at": "2026-05-20T21:22:40"
    }
  ],
  "total": 24,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

---

### Error Responses

All errors follow this format:

```json
{
  "detail": "error message here"
}
```

| Status | Meaning |
|--------|---------|
| `400` | Bad request — malformed input |
| `401` | Unauthorized — missing or invalid token |
| `403` | Forbidden — insufficient role or accessing another user's resource |
| `404` | Not found — resource does not exist |
| `409` | Conflict — email or username already registered |
| `422` | Unprocessable entity — validation error |

---

## Environment Variables

Create a `.env` file in the project root with these variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | Secret used to sign JWT tokens — use a long random string in production |
| `APP_NAME` | No | Display name for the API (default: `Job Tracker API`) |
| `DEBUG` | No | Enable SQLAlchemy query logging (default: `False`) |
| `SUPERADMIN_EMAIL` | Production | Email for the production superadmin account |
| `SUPERADMIN_PASSWORD` | Production | Password for the production superadmin account |
| `CI_SUPERADMIN_EMAIL` | CI only | Email for the throwaway CI superadmin (GitHub Actions secret) |
| `CI_SUPERADMIN_PASSWORD` | CI only | Password for the throwaway CI superadmin (GitHub Actions secret) |

**Example `.env`:**

```env
APP_NAME=Job Tracker API
DEBUG=True
DATABASE_URL=postgresql://postgres:password@localhost:5432/job_tracker_db
SECRET_KEY=your-secret-key-change-in-production
```

> **Never commit `.env` to version control.** It is already listed in `.gitignore`.

---

## Testing

The test suite uses `pytest` with a fully isolated in-memory SQLite database — no running Postgres instance is required.

### Test breakdown

| File | Tests | Coverage |
|------|-------|----------|
| `tests/test_auth.py` | 14 | Register, login, logout, `/auth/me`, validation errors, duplicate detection |
| `tests/test_jobs.py` | 14 | Job application CRUD, pagination, ownership enforcement |
| `tests/test_interviews.py` | 9 | Interview round CRUD, auto `round_number`, ownership enforcement |
| `tests/test_admin.py` | 40 | User management, RBAC enforcement, stats overview, audit log |
| **Total** | **77** | |

### How tests work

- `conftest.py` creates a fresh in-memory SQLite database for each test function (function-scoped `StaticPool`)
- `app.dependency_overrides` replaces the real `get_db` with the test session
- `FastAPI TestClient` drives all HTTP calls — no network required
- Pre-built fixtures (`registered_user`, `auth_headers`, `admin_user`, `superadmin_user`, `sample_job`) keep tests concise

### Running tests

```bash
# Run the full test suite
make test

# Run a specific file
.venv/bin/pytest tests/test_admin.py -v

# Run with short traceback output
.venv/bin/pytest --tb=short -q
```

---

## CI/CD

### GitHub Actions

The CI pipeline runs automatically on every push and pull request to `main`.

**Workflow file:** `.github/workflows/ci.yml`

**What it does:**

1. Checks out the repository
2. Sets up Python 3.11
3. Installs dependencies from `requirements.txt` (pip cache enabled)
4. Runs the full pytest suite against SQLite in-memory (`DATABASE_URL=sqlite:///./test.db`)

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

No database container is needed in CI — the test suite uses SQLite in-memory and does not depend on PostgreSQL.

---

## Deployment

The backend is deployed to [Railway.app](https://railway.app) and configured via `railway.json`. The `start.sh` entrypoint runs `alembic upgrade head` before starting uvicorn.

### Pre-deploy checklist

- [ ] Set `DEBUG=False`
- [ ] Generate a strong `SECRET_KEY`: `openssl rand -hex 32`
- [ ] Set `DATABASE_URL` to the production connection string
- [ ] Run migrations against the production database: `alembic upgrade head`
- [ ] Restrict `allow_origins` in `app/main.py` to your production frontend URL
- [ ] Set `SUPERADMIN_EMAIL` and `SUPERADMIN_PASSWORD` in Railway environment variables
- [ ] Run `scripts/seed_ci_superadmin.py` (or equivalent) to seed the initial superadmin account
- [ ] Remove `--reload` from the uvicorn command
- [ ] Do not expose `docker-compose.yml` secrets — use environment variables or a secrets manager
