# Job Tracker Backend

[![CI](https://github.com/QA-Master505/job-tracker-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/QA-Master505/job-tracker-backend/actions/workflows/ci.yml)
[![Deployed on Railway](https://img.shields.io/badge/Deployed%20on-Railway-0B0D0E?logo=railway&logoColor=white)](https://job-tracker-backend-production-7acf.up.railway.app)
[![GitHub last commit](https://img.shields.io/github/last-commit/QA-Master505/job-tracker-backend)](https://github.com/QA-Master505/job-tracker-backend/commits/main)
[![GitHub repo size](https://img.shields.io/github/repo-size/QA-Master505/job-tracker-backend)](https://github.com/QA-Master505/job-tracker-backend)

A production-deployed RESTful API for a Job Application Tracker. Built with FastAPI and PostgreSQL. Features JWT authentication via httpOnly cookies, per-user data isolation, role-based admin system, audit logging, and full CRUD for job applications and interview rounds.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Live Demo](#live-demo)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Makefile Commands](#makefile-commands)
- [Docker Setup](#docker-setup)
- [API Endpoints](#api-endpoints)
- [Admin System](#admin-system)
- [Audit Log System](#audit-log-system)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Deployment](#deployment)

---

## Project Overview

Job Tracker Backend provides a secure JSON API that powers the Job Application Tracker web app. Key features:

- **Cookie-based JWT authentication** — httpOnly cookie issued on login; Bearer token header supported as a fallback
- **Job application CRUD** — create, read, update, and delete job applications with paginated listing
- **Interview round tracking** — attach multiple interview rounds to any job application; `round_number` is auto-assigned as `MAX + 1`
- **Per-user data isolation** — users can only access their own records; ownership is enforced on every read and write
- **Role-based access control** — three tiers: `user` → `admin` → `superadmin`
- **Admin panel** — user management, status toggling, role promotion, and platform statistics
- **Audit log** — every admin mutation (role change, status toggle, deletion) is written to `audit_logs` as an atomic part of the same transaction
- **Database migrations** — full schema versioning via Alembic (5 migrations, current head: `03547cddd285`)
- **Input validation** — all requests and responses validated by Pydantic v2 schemas

---

## Live Demo

| Resource | URL |
|----------|-----|
| Backend API | `https://job-tracker-backend-production-7acf.up.railway.app` |
| Swagger UI | `https://job-tracker-backend-production-7acf.up.railway.app/docs` |
| ReDoc | `https://job-tracker-backend-production-7acf.up.railway.app/redoc` |
| Health check | `https://job-tracker-backend-production-7acf.up.railway.app/health` |

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
| Authentication | JWT (HS256) via [python-jose](https://github.com/mpdavis/python-jose) |
| Password hashing | [bcrypt](https://github.com/pyca/bcrypt/) 5.0 |
| Server | [Uvicorn](https://www.uvicorn.org/) |
| Containerisation | Docker + Docker Compose |
| CI | GitHub Actions |
| Deployment | Railway.app |

---

## Project Structure

```
job-tracker-backend/
├── app/
│   ├── main.py                    # FastAPI app, CORS middleware, router registration
│   ├── config.py                  # pydantic-settings Settings; reads .env; normalises postgres:// → postgresql://
│   ├── database.py                # SQLAlchemy engine, SessionLocal, get_db dependency, check_db_connection
│   │
│   ├── models/
│   │   ├── base.py                # SQLAlchemy DeclarativeBase
│   │   ├── user.py                # users — id, email (unique), username (unique), hashed_password, role, is_active, created_at
│   │   ├── job_application.py     # job_applications + ApplicationStatus enum (8 values)
│   │   ├── interview_round.py     # interview_rounds + InterviewType enum (phone/virtual/onsite/other)
│   │   └── audit_log.py           # audit_logs — actor_id (SET NULL FK), action, target_type, target_id, detail
│   │
│   ├── schemas/
│   │   ├── types.py               # DatetimeFormatted — serialises datetime as "YYYY-MM-DDTHH:MM:SS"
│   │   ├── user.py                # UserRegister, UserLogin, UserResponse, TokenResponse, UserProfileUpdate
│   │   ├── job_application.py     # JobApplicationCreate/Update/Response, PaginatedJobsResponse
│   │   ├── interview_round.py     # InterviewRoundCreate/Update/Response
│   │   └── admin.py               # UserAdminResponse, RoleUpdateRequest, StatsOverviewResponse, AuditLogResponse
│   │
│   ├── routers/
│   │   ├── auth.py                # POST /auth/register  POST /auth/login  GET /auth/me  POST /auth/logout
│   │   ├── jobs.py                # GET/POST /jobs  GET/PUT/DELETE /jobs/{id}
│   │   ├── interview_rounds.py    # GET/POST/PUT/DELETE under /jobs/{job_id}/interviews[/{round_id}]
│   │   ├── users.py               # GET/PUT/DELETE /users/me
│   │   └── admin.py               # GET/PATCH/DELETE under /admin/users, /admin/stats/overview, /admin/audit-log
│   │
│   ├── services/
│   │   ├── auth_service.py        # get_user_by_email/username/id, create_user, authenticate_user
│   │   ├── job_service.py         # CRUD + get_jobs_paginated (offset/limit/ceil, max page_size 10)
│   │   ├── interview_service.py   # CRUD + MAX(round_number)+1 auto-assignment on insert
│   │   └── admin_service.py       # User management, log_admin_action, stats via subquery/COALESCE, aliased audit join
│   │
│   ├── utils/
│   │   └── security.py            # bcrypt hash/verify, create_access_token (JWT encode), decode_access_token
│   │
│   └── dependencies/
│       └── auth.py                # get_current_user (cookie → Bearer fallback), require_admin, require_superadmin
│
├── alembic/
│   ├── env.py                     # Overrides sqlalchemy.url from settings; imports all models for autogenerate
│   ├── script.py.mako             # Migration file template
│   └── versions/
│       ├── 0408b69a93c1_add_user_table.py
│       ├── 007ea04b7f23_add_job_applications_table.py
│       ├── 1c466a497ce3_add_interview_rounds_table.py
│       ├── f7e97e8dcb2e_add_role_to_users.py
│       └── 03547cddd285_add_audit_log_table.py       ← current head
│
├── scripts/
│   └── seed_ci_superadmin.py      # Raw-SQL + bcrypt seeder; idempotent via ON CONFLICT DO NOTHING; no app imports
│
├── tests/
│   ├── conftest.py                # SQLite in-memory (StaticPool), TestClient, dependency_overrides, 8 fixtures
│   ├── test_auth.py               # 13 tests — register, login, me, logout, account deletion
│   ├── test_jobs.py               # 13 tests — full CRUD, ownership enforcement, pagination
│   ├── test_interviews.py         # 9 tests  — CRUD, round_number auto-increment
│   └── test_admin.py              # 40 tests — 401/403 matrix, user management, stats, audit log verification
│
├── .github/workflows/ci.yml       # Runs pytest on every push/PR to main (SQLite in-memory, no Postgres needed)
├── alembic.ini                    # Alembic config (URL overridden at runtime by alembic/env.py)
├── docker-compose.yml             # postgres:16 + backend (depends_on: service_healthy; mounts .:/app)
├── Dockerfile                     # python:3.11-slim; installs gcc + postgresql-client; CMD ./start.sh
├── Makefile                       # 21 shortcut targets for dev, migration, test, and Docker workflows
├── pytest.ini                     # testpaths = tests, pythonpath = .
├── railway.json                   # Dockerfile builder; restart ON_FAILURE, max 3 retries
├── requirements.txt               # Pinned Python dependencies
├── start.sh                       # Container entrypoint — DB inspection, stale-state reset, migrate, verify, start
├── .env                           # Local environment variables (not committed)
└── README.md
```

---

## Architecture

All request handling flows through four distinct layers with no bypasses.

```
HTTP Request
    │
    ▼
routers/           ← validates input (Pydantic schemas), enforces auth (dependencies/auth.py)
    │
    ▼
services/          ← all DB queries and mutations; owns business rules and audit log writes
    │
    ▼
models/            ← SQLAlchemy ORM table definitions; alembic/versions/ tracks all schema changes
    │
    ▼
database.py        ← engine + SessionLocal bound to DATABASE_URL; get_db() yields one session per request
```

**Auth flow:**

```
Incoming request
    │
    ├─ Bearer token in Authorization header?  ─┐
    │                                          │
    └─ access_token cookie?  ─────────────────┤
                                              ▼
                                        decode JWT (HS256)
                                              │
                                   look up user by id (sub claim)
                                              │
                                       check is_active
                                              │
                                    inject User into route handler
```

**Delete cascade chain:**

```
DELETE users
    └─ CASCADE → job_applications
                     └─ CASCADE → interview_rounds

audit_logs.actor_id → SET NULL   (row preserved; actor field cleared)
audit_logs.target_id → plain int (no FK; survives target deletion permanently)
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
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## Makefile Commands

| Command | Description | Underlying command |
|---------|-------------|-------------------|
| `make run` | Start dev server (requires venv activated) | `uvicorn app.main:app --reload` |
| `make dev` | Start dev server on `0.0.0.0:8000` | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| `make start` | Start dev server via `.venv` directly | `.venv/bin/uvicorn app.main:app --reload` |
| `make install` | Install all packages from `requirements.txt` | `.venv/bin/pip install -r requirements.txt` |
| `make freeze` | Overwrite `requirements.txt` with current packages | `.venv/bin/pip freeze > requirements.txt` |
| `make migrate` | Apply all pending migrations | `alembic upgrade head` |
| `make migration MSG="description"` | Create a new autogenerated migration | `alembic revision --autogenerate -m "description"` |
| `make rollback` | Roll back the most recent migration | `alembic downgrade -1` |
| `make test` | Run the test suite | `.venv/bin/pytest` |
| `make help` | Print the full command reference | `@echo ...` |
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

**Examples:**

```bash
make migrate
make migration MSG="add salary field to job applications"
make rollback
```

---

## Docker Setup

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Docker Compose (included with Docker Desktop)

### Quick Start

```bash
make docker-up
```

This builds the image, starts PostgreSQL, waits for the healthcheck (`pg_isready`), runs all pending migrations, then starts the API server with hot reload.

### Services

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |

### How it works

```
docker-compose up --build
        │
        ├─ builds image: python:3.11-slim + gcc + postgresql-client + requirements.txt
        │
        ├─ starts postgres:16
        │     └─ healthcheck: pg_isready every 10s (5s timeout, 5 retries)
        │
        └─ starts backend (depends_on: service_healthy)
               ├─ alembic upgrade head
               └─ uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Notes

- PostgreSQL data is persisted in a named volume (`postgres_data`). Run `make docker-clean` to wipe it.
- The backend mounts `.:/app` — code changes are reflected immediately without rebuilding.
- Variables in `docker-compose.yml` are for **development only**. Never use them in production.
- A local `.env` file is **not** read inside the container — set variables directly in `docker-compose.yml` or pass them with `docker-compose --env-file`.

---

## API Endpoints

All endpoints return JSON. Protected endpoints require authentication via the `access_token` httpOnly cookie (set automatically on login) or an `Authorization: Bearer <token>` header.

---

### Health Check

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | No | Root — confirms the API is running |
| `GET` | `/health` | No | Returns app name and database connectivity |

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
| `GET` | `/auth/me` | Yes | Get the authenticated user's profile |
| `POST` | `/auth/logout` | Yes | Clear the auth cookie |

**Register** — `POST /auth/register`

```json
// Request body
{
  "email": "user@example.com",
  "username": "johndoe",      // 3–50 characters
  "password": "securepass"    // minimum 8 characters
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

Sets an `access_token` httpOnly cookie and also returns the raw token in the body for clients that prefer the Bearer header.

```json
// Request body
{
  "email": "user@example.com",
  "password": "securepass"
}

// Response 200
// Sets: Set-Cookie: access_token=<jwt>; HttpOnly; SameSite=Lax
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Logout** — `POST /auth/logout`

Clears the cookie by setting `max_age=0`. Returns `200` with a confirmation message.

---

### Users

All `/users` endpoints require authentication.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/users/me` | Yes | Get the authenticated user's profile |
| `PUT` | `/users/me` | Yes | Update username, email, or password |
| `DELETE` | `/users/me` | Yes | Permanently delete the authenticated user's account |

**Update profile** — `PUT /users/me`

All fields are optional. To change the password, both `current_password` and `new_password` must be supplied together.

```json
// Request body (include only fields to change)
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

All job application endpoints require authentication. Users can only access their own records.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/jobs` | List the current user's job applications (paginated) |
| `POST` | `/jobs` | Create a new job application |
| `GET` | `/jobs/{id}` | Get a single job application |
| `PUT` | `/jobs/{id}` | Partially update a job application |
| `DELETE` | `/jobs/{id}` | Delete a job application |

**Query parameters for `GET /jobs`:**

| Parameter | Default | Max | Description |
|-----------|---------|-----|-------------|
| `page` | `1` | — | Page number |
| `page_size` | `6` | `10` | Results per page |

**Application status values:**

`applied` · `phone_interview` · `virtual_interview` · `onsite_interview` · `offer` · `rejected` · `no_response` · `withdrawn`

**Create** — `POST /jobs`

```json
// Request body
{
  "company_name": "Acme Corp",
  "job_title": "Backend Engineer",
  "job_url": "https://acme.com/jobs/123",   // optional
  "status": "applied",
  "applied_date": "2026-05-20",
  "notes": "Referred by a friend"           // optional
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

**Paginated list** — `GET /jobs`

```json
{
  "items": [ ... ],
  "total": 42,
  "page": 1,
  "page_size": 6,
  "total_pages": 7
}
```

**Update** — `PUT /jobs/{id}`

Uses `exclude_unset=True` — only the fields included in the request body are changed.

```json
{
  "status": "phone_interview",
  "notes": "Phone screen scheduled for Friday"
}
```

**Delete** — `DELETE /jobs/{id}` → `204 No Content`

---

### Interview Rounds

Interview rounds are nested under a job application. All endpoints require authentication and ownership of the parent job.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/jobs/{job_id}/interviews` | List all interview rounds for a job application |
| `POST` | `/jobs/{job_id}/interviews` | Add a new interview round |
| `PUT` | `/jobs/{job_id}/interviews/{round_id}` | Update an interview round |
| `DELETE` | `/jobs/{job_id}/interviews/{round_id}` | Delete an interview round |

`round_number` is assigned automatically as `MAX(round_number) + 1` per job and is not part of the request body.

**Interview type values:** `phone` · `virtual` · `onsite` · `other`

**Add round** — `POST /jobs/{job_id}/interviews`

```json
// Request body
{
  "interview_type": "phone",
  "interview_date": "2026-06-01",
  "notes": "Initial recruiter screen"   // optional
}

// Response 201
{
  "id": 1,
  "job_application_id": 1,
  "round_number": 1,
  "interview_type": "phone",
  "interview_date": "2026-06-01",
  "notes": "Initial recruiter screen",
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

**Delete** — `DELETE /jobs/{job_id}/interviews/{round_id}` → `204 No Content`

---

### Error Responses

All errors follow this format:

```json
{ "detail": "error message here" }
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

## Admin System

Access is gated by two dependency functions in `app/dependencies/auth.py`:

- **`require_admin`** — role must be `admin` or `superadmin`
- **`require_superadmin`** — role must be `superadmin` only

### Role tiers

| Role | Description |
|------|-------------|
| `user` | Default on registration. Access to own data only. No admin routes. |
| `admin` | Can view all users, toggle account status, read stats and audit log. Cannot change roles or delete users. |
| `superadmin` | Full access. Can also promote/demote roles and permanently delete users. |

### Permission matrix

| Endpoint | `user` | `admin` | `superadmin` |
|----------|--------|---------|--------------|
| `GET /admin/users` | 403 | ✅ | ✅ |
| `GET /admin/users/{id}` | 403 | ✅ | ✅ |
| `PATCH /admin/users/{id}/status` | 403 | ✅ | ✅ |
| `GET /admin/stats/overview` | 403 | ✅ | ✅ |
| `GET /admin/audit-log` | 403 | ✅ | ✅ |
| `PATCH /admin/users/{id}/role` | 403 | 403 | ✅ |
| `DELETE /admin/users/{id}` | 403 | 403 | ✅ |

### Admin endpoints

**List users** — `GET /admin/users`

Supports query filters `?role=admin` and `?is_active=false`. Paginated via `page` / `page_size` (max 10).

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
  "page_size": 6,
  "total_pages": 17
}
```

**Update role** — `PATCH /admin/users/{id}/role` *(superadmin only)*

```json
// Request body
{ "new_role": "admin" }
```

Valid values: `user` · `admin` · `superadmin`

**Toggle status** — `PATCH /admin/users/{id}/status`

Flips `is_active` between `true` and `false`. No request body. Writes an audit entry (`user.activate` or `user.deactivate`) on every call.

**Delete user** — `DELETE /admin/users/{id}` *(superadmin only)*

Returns `204 No Content`. Cascades to all owned job applications and interview rounds. Writes a `user.delete` audit entry before deletion.

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

Paginated (max 200 per page), ordered by most recent first. See [Audit Log System](#audit-log-system).

---

## Audit Log System

Every mutating admin action writes a row to `audit_logs` as an atomic part of the same database transaction as the mutation itself. If the mutation is rolled back, the audit entry is rolled back too.

### What is recorded

| Action string | Trigger |
|---------------|---------|
| `user.role_change` | `PATCH /admin/users/{id}/role` |
| `user.activate` | `PATCH /admin/users/{id}/status` (when toggling on) |
| `user.deactivate` | `PATCH /admin/users/{id}/status` (when toggling off) |
| `user.delete` | `DELETE /admin/users/{id}` |

### Schema

| Column | Type | Notes |
|--------|------|-------|
| `actor_id` | `int` (FK → users, SET NULL) | The admin who took the action. Set to NULL if the actor is later deleted. |
| `action` | `varchar(100)` | Dot-namespaced string, e.g. `user.role_change` |
| `target_type` | `varchar(50)` | Resource type, e.g. `user` |
| `target_id` | `int` (no FK) | ID of the affected resource. Plain integer — survives target deletion permanently. |
| `detail` | `text` | JSON-encoded before/after state, e.g. `{"old_role": "user", "new_role": "admin"}` |

### Sample response item

```json
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
```

`actor_email` is resolved via a LEFT JOIN on the `users` table at query time and is `null` if the actor has been deleted.

---

## Environment Variables

Create a `.env` file in the project root with these variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string. `postgres://` is auto-normalised to `postgresql://` at startup. |
| `SECRET_KEY` | Yes | JWT signing key — use a long random string in production (`openssl rand -hex 32`) |
| `APP_NAME` | No | Display name for the API (default: `Job Tracker API`) |
| `DEBUG` | No | Enable SQLAlchemy query logging (default: `False`) |
| `SUPERADMIN_EMAIL` | Production | Email for the production superadmin account |
| `SUPERADMIN_PASSWORD` | Production | Password for the production superadmin account |
| `CI_SUPERADMIN_EMAIL` | CI only | Email for the throwaway CI superadmin (stored as a GitHub Actions secret) |
| `CI_SUPERADMIN_PASSWORD` | CI only | Password for the throwaway CI superadmin (stored as a GitHub Actions secret) |

**Example `.env`:**

```env
APP_NAME=Job Tracker API
DEBUG=True
DATABASE_URL=postgresql://postgres:password@localhost:5432/job_tracker_db
SECRET_KEY=your-secret-key-change-in-production
```

> **Never commit `.env` to version control.** It is listed in `.gitignore`.

---

## Testing

The backend has two separate test layers. Full documentation for both lives in
the [job-tracker-tests](https://github.com/QA-Master505/job-tracker-tests)
repository.

### API Layer Tests — SQLite (Fast)

Uses FastAPI `TestClient` with SQLite in-memory. No database or server setup
required. Covers endpoints, status codes, response shapes, ownership
enforcement, and role-based access control.

| File | Tests | What It Covers |
|------|-------|---------------|
| `tests/test_auth.py` | 13 | Register, login, logout, `/auth/me`, account deletion |
| `tests/test_jobs.py` | 13 | Full CRUD, ownership enforcement, pagination |
| `tests/test_interviews.py` | 9 | CRUD, `round_number` auto-increment |
| `tests/test_admin.py` | 40 | 401/403 matrix, role/status mutations, stats, audit log |
| **Total** | **75** | |

```bash
# Run all API layer tests
make test

# Run a specific file
.venv/bin/pytest tests/test_admin.py -v
```
→ Full API & Admin Test Documentation

### Database Layer Tests — PostgreSQL (Real)
Uses pytest + SQLAlchemy against a real Docker PostgreSQL instance (port 5433).
Verifies constraints, cascade behaviour, migration integrity, and query
correctness — things SQLite cannot replicate accurately. Uses a
rollback-after-every-test fixture for full isolation.

| File | What It Verifies |
|------|-----------------|
| `tests/db/test_user_model.py` | Unique constraints, NOT NULL, bcrypt format, default role |
| `tests/db/test_job_model.py` | FK enforcement, CASCADE delete chain, enum gap finding |
| `tests/db/test_migrations.py` | Alembic head, all tables present, column verification |
| `tests/db/test_queries.py` | Pagination, aggregation, filter isolation |
| `tests/db/test_admin_service.py` | Audit log atomicity, SET NULL on delete, stats accuracy |

```bash
# Start Docker PostgreSQL (port 5433)
docker start job-tracker-db-test

# Run migrations against test DB
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/job_tracker_test \
  alembic upgrade head

# Run all DB layer tests
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/job_tracker_test \
  pytest tests/db/ -v
```
→ Full Database Automation Test Documentation

---

## CI/CD

The GitHub Actions workflow (.github/workflows/ci.yml) runs the 75 API layer
tests automatically on every push and pull request to main. No PostgreSQL
container is needed — SQLite runs entirely in-memory.

Database layer tests are run locally against Docker and are planned for
addition to CI with a PostgreSQL service block in a future update.

---

## Deployment

The backend is deployed to Railway.app. `railway.json` configures a Dockerfile build with an `ON_FAILURE` restart policy and a maximum of 3 retries.

### Container entrypoint (`start.sh`)

`start.sh` runs before uvicorn and performs several safety checks before starting the server:

1. **DB inspection** — lists all existing tables using SQLAlchemy's `inspect(engine)`
2. **Stale-state detection** — if `alembic_version` exists but the required tables (`users`, `job_applications`, `interview_rounds`) are missing, it drops all partial tables and the version row so migrations can run cleanly from scratch
3. **Migration file listing** — `ls -la alembic/versions/` confirms revision files are present
4. **SQL dry-run** — `alembic upgrade head --sql` prints the full SQL without executing it
5. **Migration** — `alembic upgrade head` applies all pending revisions
6. **Table verification** — confirms all three required tables exist; exits non-zero if any are missing
7. **Start server** — `exec uvicorn app.main:app --host 0.0.0.0 --port 8000` (no `--reload` in production)

### Pre-deploy checklist

- [ ] Set `DEBUG=False`
- [ ] Generate a strong `SECRET_KEY`: `openssl rand -hex 32`
- [ ] Set `DATABASE_URL` to the production PostgreSQL connection string
- [ ] Run migrations (or let `start.sh` handle it on first boot): `alembic upgrade head`
- [ ] Restrict `allow_origins` in `app/main.py` to your production frontend URL
- [ ] Set `SUPERADMIN_EMAIL` and `SUPERADMIN_PASSWORD` in Railway environment variables
- [ ] Seed the initial superadmin account using `scripts/seed_ci_superadmin.py`:

```bash
DATABASE_URL=<prod_url> \
CI_SUPERADMIN_EMAIL=admin@yourdomain.com \
CI_SUPERADMIN_PASSWORD=<strong_password> \
python scripts/seed_ci_superadmin.py
```

- [ ] Do not expose `docker-compose.yml` credentials — use Railway environment variables or a secrets manager
