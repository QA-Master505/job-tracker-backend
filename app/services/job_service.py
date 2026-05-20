from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.job_application import JobApplication
from app.schemas.job_application import JobApplicationCreate, JobApplicationUpdate


def get_jobs_for_user(db: Session, user_id: int) -> list[JobApplication]:
    return (
        db.query(JobApplication)
        .filter(JobApplication.user_id == user_id)
        .order_by(JobApplication.applied_date.desc())
        .all()
    )


def get_job_by_id(db: Session, job_id: int) -> JobApplication | None:
    return db.query(JobApplication).filter(JobApplication.id == job_id).first()


def create_job(db: Session, user_id: int, data: JobApplicationCreate) -> JobApplication:
    job = JobApplication(user_id=user_id, **data.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_job(db: Session, job: JobApplication, data: JobApplicationUpdate) -> JobApplication:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    job.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job


def delete_job(db: Session, job: JobApplication) -> None:
    db.delete(job)
    db.commit()
