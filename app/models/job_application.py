from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.interview_round import InterviewRound


class ApplicationStatus(str, enum.Enum):
    applied = "applied"
    phone_interview = "phone_interview"
    virtual_interview = "virtual_interview"
    onsite_interview = "onsite_interview"
    offer = "offer"
    rejected = "rejected"
    no_response = "no_response"
    withdrawn = "withdrawn"


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, native_enum=False, length=20),
        default=ApplicationStatus.applied,
        nullable=False,
    )
    applied_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner = relationship("User", back_populates="job_applications")
    interview_rounds: Mapped[List[InterviewRound]] = relationship(
        "InterviewRound", back_populates="job_application", cascade="all, delete-orphan"
    )
