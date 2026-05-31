from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.job_application import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationUpdate,
    PaginatedJobsResponse,
)
from app.services.job_service import (
    create_job,
    delete_job,
    get_job_by_id,
    get_jobs_paginated,
    update_job,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _get_owned_job(job_id: int, current_user: User, db: Session):
    job = get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job application not found")
    if job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return job


@router.get("", response_model=PaginatedJobsResponse)
def list_jobs(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_jobs_paginated(db, current_user.id, page=page, page_size=page_size)


@router.post("", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_job_application(
    data: JobApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_job(db, current_user.id, data)


@router.get("/{job_id}", response_model=JobApplicationResponse)
def get_job_application(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_owned_job(job_id, current_user, db)


@router.put("/{job_id}", response_model=JobApplicationResponse)
def update_job_application(
    job_id: int,
    data: JobApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = _get_owned_job(job_id, current_user, db)
    return update_job(db, job, data)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_application(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = _get_owned_job(job_id, current_user, db)
    delete_job(db, job)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
