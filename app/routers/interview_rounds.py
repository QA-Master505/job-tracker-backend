from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.interview_round import (
    InterviewRoundCreate,
    InterviewRoundResponse,
    InterviewRoundUpdate,
)
from app.services.interview_service import (
    create_round,
    delete_round,
    get_all_rounds,
    get_round_by_id,
    update_round,
)
from app.services.job_service import get_job_by_id

router = APIRouter(tags=["interviews"])


def _get_owned_job(job_id: int, current_user: User, db: Session):
    job = get_job_by_id(db, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job application not found")
    if job.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return job


def _get_round_or_404(round_id: int, job_id: int, db: Session):
    round_obj = get_round_by_id(db, round_id)
    if round_obj is None or round_obj.job_application_id != job_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview round not found")
    return round_obj


@router.get("/{job_id}/interviews", response_model=list[InterviewRoundResponse])
def list_rounds(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_job(job_id, current_user, db)
    return get_all_rounds(db, job_id)


@router.post("/{job_id}/interviews", response_model=InterviewRoundResponse, status_code=status.HTTP_201_CREATED)
def add_round(
    job_id: int,
    data: InterviewRoundCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_job(job_id, current_user, db)
    return create_round(db, job_id, data)


@router.put("/{job_id}/interviews/{round_id}", response_model=InterviewRoundResponse)
def edit_round(
    job_id: int,
    round_id: int,
    data: InterviewRoundUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_job(job_id, current_user, db)
    round_obj = _get_round_or_404(round_id, job_id, db)
    return update_round(db, round_obj, data)


@router.delete("/{job_id}/interviews/{round_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_round(
    job_id: int,
    round_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_owned_job(job_id, current_user, db)
    round_obj = _get_round_or_404(round_id, job_id, db)
    delete_round(db, round_obj)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
