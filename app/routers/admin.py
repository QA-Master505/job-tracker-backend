from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin, require_superadmin
from app.models.user import User
from app.schemas.admin import (
    AuditLogResponse,
    PaginatedAuditLogResponse,
    PaginatedUsersResponse,
    RoleUpdateRequest,
    StatsOverviewResponse,
    UserAdminResponse,
)
from app.services.admin_service import (
    delete_user_by_id,
    get_all_users,
    get_audit_log,
    get_stats_overview,
    get_user_by_id,
    toggle_user_status,
    update_user_role,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _build_user_response(user: User, job_count: int) -> UserAdminResponse:
    return UserAdminResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        role=user.role,
        created_at=user.created_at,
        job_count=job_count,
    )


@router.get("/users", response_model=PaginatedUsersResponse)
def list_users(
    page: int = 1,
    page_size: int = 20,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    rows, total = get_all_users(
        db, skip=(page - 1) * page_size, limit=page_size,
        role_filter=role, is_active_filter=is_active,
    )
    return PaginatedUsersResponse(
        items=[_build_user_response(u, jc) for u, jc in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/users/{user_id}", response_model=UserAdminResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user, job_count = get_user_by_id(db, user_id)
    return _build_user_response(user, job_count)


@router.patch("/users/{user_id}/role", response_model=UserAdminResponse)
def change_user_role(
    user_id: int,
    data: RoleUpdateRequest,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    user, job_count = update_user_role(
        db, user_id=user_id, new_role=data.new_role, actor_id=current_user.id,
    )
    return _build_user_response(user, job_count)


@router.patch("/users/{user_id}/status", response_model=UserAdminResponse)
def change_user_status(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user, job_count = toggle_user_status(db, user_id=user_id, actor_id=current_user.id)
    return _build_user_response(user, job_count)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
):
    delete_user_by_id(db, user_id=user_id, actor_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/stats/overview", response_model=StatsOverviewResponse)
def stats_overview(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return get_stats_overview(db)


@router.get("/audit-log", response_model=PaginatedAuditLogResponse)
def list_audit_log(
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    page = max(1, page)
    page_size = max(1, min(200, page_size))
    rows, total = get_audit_log(db, skip=(page - 1) * page_size, limit=page_size)
    items = [
        AuditLogResponse(
            id=log.id,
            actor_id=log.actor_id,
            actor_email=actor_email,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            detail=log.detail,
            created_at=log.created_at,
        )
        for log, actor_email in rows
    ]
    return PaginatedAuditLogResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )
