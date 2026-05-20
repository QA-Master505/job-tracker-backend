from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import check_db_connection
from app.routers import auth, jobs

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(jobs.router)


@app.get("/")
def root():
    return {"message": "Job Tracker API is running"}


@app.get("/health")
def health_check():
    db_ok = check_db_connection()
    return {
        "status": "ok",
        "app": settings.app_name,
        "database": "connected" if db_ok else "unavailable",
    }
