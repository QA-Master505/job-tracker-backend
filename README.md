# Job Tracker Backend

A RESTful API for the Job Application Tracker — built with FastAPI and PostgreSQL. Allows users to register, authenticate, and manage their job applications with full CRUD support.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Makefile Commands](#makefile-commands)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Deployment](#deployment)

---

## Project Overview

Job Tracker Backend provides a secure JSON API that powers the Job Application Tracker web app. Key features:

- **JWT authentication** — register, login, and protect routes with Bearer tokens
- **Job application CRUD** — create, read, update, and delete job applications
- **Per-user data isolation** — users can only access their own records
- **Database migrations** — schema versioning via Alembic
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
│   ├── main.py                  # App entry point, middleware, router registration
│   ├── config.py                # Settings loaded from .env via pydantic-settings
│   ├── database.py              # SQLAlchemy engine, session factory, get_db dependency
│   │
│   ├── models/
│   │   ├── base.py              # SQLAlchemy DeclarativeBase
│   │   ├── user.py              # User model
│   │   └── job_application.py   # JobApplication model + ApplicationStatus enum
│   │
│   ├── schemas/
│   │   ├── types.py             # Shared Pydantic types (DatetimeFormatted)
│   │   ├── user.py              # UserRegister, UserLogin, UserResponse, TokenResponse
│   │   └── job_application.py   # JobApplicationCreate, Update, Response schemas
│   │
│   ├── routers/
│   │   ├── auth.py              # POST /auth/register, /auth/login, GET /auth/me
│   │   └── jobs.py              # GET/POST /jobs, GET/PUT/DELETE /jobs/{id}
│   │
│   ├── services/
│   │   ├── auth_service.py      # User lookup, creation, authentication
│   │   └── job_service.py       # Job application CRUD queries
│   │
│   ├── utils/
│   │   └── security.py          # Password hashing, JWT encode/decode
│   │
│   └── dependencies/
│       └── auth.py              # get_current_user FastAPI dependency
│
├── alembic/
│   └── versions/                # Auto-generated migration files
├── alembic.ini                  # Alembic configuration
├── requirements.txt
├── Makefile
├── .env                         # Local environment variables (not committed)
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

| Command | Description |
|---------|-------------|
| `make run` | Start the dev server (requires venv activated) |
| `make dev` | Start the dev server on `0.0.0.0:8000` for external access |
| `make start` | Start the dev server via `.venv` — no manual activation needed |
| `make install` | Install all packages from `requirements.txt` |
| `make freeze` | Overwrite `requirements.txt` with currently installed packages |
| `make migrate` | Apply all pending database migrations |
| `make migration MSG="description"` | Create a new autogenerated Alembic migration |
| `make rollback` | Roll back the most recent migration |
| `make test` | Run the test suite |
| `make help` | Print the full command reference |

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

## API Endpoints

All endpoints return JSON. Protected endpoints require a `Bearer` token in the `Authorization` header.

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
| `POST` | `/auth/login` | No | Login and receive a JWT token |
| `GET` | `/auth/me` | Yes | Get the currently authenticated user |

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
  "created_at": "2026-05-20T21:22:40"
}
```

**Login** — `POST /auth/login`

```json
// Request body
{
  "email": "user@example.com",
  "password": "securepassword"
}

// Response 200
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Get current user** — `GET /auth/me`

```
Authorization: Bearer <access_token>
```

```json
// Response 200
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "created_at": "2026-05-20T21:22:40"
}
```

---

### Job Applications

All job application endpoints require authentication.

```
Authorization: Bearer <access_token>
```

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/jobs` | List all job applications for the current user |
| `POST` | `/jobs` | Create a new job application |
| `GET` | `/jobs/{id}` | Get a single job application |
| `PUT` | `/jobs/{id}` | Update a job application |
| `DELETE` | `/jobs/{id}` | Delete a job application |

**Application status values:** `applied` · `interview` · `offer` · `rejected` · `no_response`

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

**Update** — `PUT /jobs/{id}`

Only include the fields you want to change:

```json
{
  "status": "interview",
  "notes": "Phone screen scheduled for Friday"
}
```

**Delete** — `DELETE /jobs/{id}`

Returns `204 No Content` on success.

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
| `403` | Forbidden — accessing another user's resource |
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

> Testing setup is in progress. This section will be updated when Playwright / pytest tests are added.

Placeholder commands:

```bash
# Run the full test suite
make test

# Run a specific test file
.venv/bin/pytest tests/test_auth.py -v
```

---

## Deployment

> Deployment configuration is in progress. This section will be updated with Railway / Render / Docker instructions.

Checklist before deploying:

- [ ] Set `DEBUG=False`
- [ ] Use a strong random `SECRET_KEY` (e.g. `openssl rand -hex 32`)
- [ ] Set `DATABASE_URL` to the production database connection string
- [ ] Run `make migrate` against the production database
- [ ] Restrict `allow_origins` in `main.py` to your production frontend URL
