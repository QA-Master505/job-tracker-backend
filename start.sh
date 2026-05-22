#!/bin/sh
set -e

echo "=== Checking database state ==="
python3 - <<'EOF'
from app.database import engine
from sqlalchemy import inspect, text

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Tables found: {tables}")

required = ["users", "job_applications", "interview_rounds"]
has_version_table = "alembic_version" in tables
any_missing = any(t not in tables for t in required)

if has_version_table and any_missing:
    print("Detected stale state (alembic_version exists but tables incomplete). Resetting...")
    with engine.connect() as conn:
        for t in ["interview_rounds", "job_applications", "users"]:
            if t in tables:
                conn.execute(text(f"DROP TABLE {t} CASCADE"))
                print(f"Dropped partial table: {t}")
        conn.execute(text("DROP TABLE alembic_version"))
        conn.commit()
    print("Reset complete — migrations will run from scratch.")
else:
    missing = [t for t in required if t not in tables]
    print(f"State OK — missing tables (expected on fresh DB): {missing}")
EOF

echo "=== Migration files ==="
ls -la alembic/versions/

echo "=== SQL preview (dry-run) ==="
alembic upgrade head --sql

echo "=== Running migrations ==="
alembic upgrade head

echo "=== Verifying tables ==="
python3 - <<'EOF'
from app.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Tables in database: {tables}")

required = ["users", "job_applications", "interview_rounds"]
missing = [t for t in required if t not in tables]
if missing:
    print(f"ERROR: missing tables: {missing}")
    raise SystemExit(1)
print("All required tables verified.")
EOF

echo "=== Starting server ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
