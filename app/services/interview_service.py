from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.interview_round import InterviewRound
from app.schemas.interview_round import InterviewRoundCreate, InterviewRoundUpdate


def get_all_rounds(db: Session, job_id: int) -> list[InterviewRound]:
    return (
        db.query(InterviewRound)
        .filter(InterviewRound.job_application_id == job_id)
        .order_by(InterviewRound.round_number)
        .all()
    )


def get_round_by_id(db: Session, round_id: int) -> InterviewRound | None:
    return db.query(InterviewRound).filter(InterviewRound.id == round_id).first()


def create_round(db: Session, job_id: int, data: InterviewRoundCreate) -> InterviewRound:
    last = (
        db.query(func.max(InterviewRound.round_number))
        .filter(InterviewRound.job_application_id == job_id)
        .scalar()
    )
    round_obj = InterviewRound(
        job_application_id=job_id,
        round_number=(last or 0) + 1,
        **data.model_dump(),
    )
    db.add(round_obj)
    db.commit()
    db.refresh(round_obj)
    return round_obj


def update_round(db: Session, round_obj: InterviewRound, data: InterviewRoundUpdate) -> InterviewRound:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(round_obj, field, value)
    round_obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(round_obj)
    return round_obj


def delete_round(db: Session, round_obj: InterviewRound) -> None:
    db.delete(round_obj)
    db.commit()
