from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, field_validator

from app.schemas.types import DatetimeFormatted

_VALID_ROLES = ("user", "admin", "superadmin")


class UserAdminResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    role: str
    created_at: DatetimeFormatted
    job_count: int


class PaginatedUsersResponse(BaseModel):
    items: list[UserAdminResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RoleUpdateRequest(BaseModel):
    new_role: str

    @field_validator("new_role")
    @classmethod
    def valid_role(cls, v: str) -> str:
        if v not in _VALID_ROLES:
            raise ValueError(f"role must be one of: {', '.join(_VALID_ROLES)}")
        return v


class StatsOverviewResponse(BaseModel):
    total_users: int
    active_users: int
    total_jobs: int
    jobs_by_status: dict[str, int]


class AuditLogResponse(BaseModel):
    id: int
    actor_id: Optional[int]
    actor_email: Optional[str]
    action: str
    target_type: str
    target_id: Optional[int]
    detail: Optional[str]
    created_at: DatetimeFormatted


class PaginatedAuditLogResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
