from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.interview_round import InterviewType
from app.schemas.types import DatetimeFormatted


class InterviewRoundCreate(BaseModel):
    interview_type: InterviewType
    interview_date: date
    notes: Optional[str] = None


class InterviewRoundUpdate(BaseModel):
    interview_type: Optional[InterviewType] = None
    interview_date: Optional[date] = None
    notes: Optional[str] = None


class InterviewRoundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_application_id: int
    round_number: int
    interview_type: InterviewType
    interview_date: date
    notes: Optional[str]
    created_at: DatetimeFormatted
    updated_at: DatetimeFormatted
