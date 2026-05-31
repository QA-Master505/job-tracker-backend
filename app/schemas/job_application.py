from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.types import DatetimeFormatted

from app.models.job_application import ApplicationStatus


class JobApplicationCreate(BaseModel):
    company_name: str
    job_title: str
    job_url: Optional[str] = None
    status: ApplicationStatus = ApplicationStatus.applied
    applied_date: date
    notes: Optional[str] = None

    @field_validator("company_name", "job_title")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("field cannot be blank")
        return v


class JobApplicationUpdate(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    job_url: Optional[str] = None
    status: Optional[ApplicationStatus] = None
    applied_date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator("company_name", "job_title")
    @classmethod
    def not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("field cannot be blank")
        return v


class JobApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    company_name: str
    job_title: str
    job_url: Optional[str]
    status: ApplicationStatus
    applied_date: date
    notes: Optional[str]
    created_at: DatetimeFormatted
    updated_at: DatetimeFormatted


class PaginatedJobsResponse(BaseModel):
    items: list[JobApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
