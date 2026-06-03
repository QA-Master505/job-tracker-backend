from __future__ import annotations

import json
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.models.audit_log import AuditLog
from app.models.job_application import ApplicationStatus, JobApplication
from app.models.user import User


def log_admin_action(
    db: Session,
    actor_id: Optional[int],
    action: str,
    target_type: str,
    target_id: Optional[int] = None,
    detail: Optional[str] = None,
) -> None:
    db.add(AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
    ))
    # caller commits — entry is part of the same transaction as the mutation


def _job_count(db: Session, user_id: int) -> int:
    return db.query(func.count(JobApplication.id)).filter(
        JobApplication.user_id == user_id
    ).scalar() or 0


def get_all_users(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    role_filter: Optional[str] = None,
    is_active_filter: Optional[bool] = None,
) -> tuple[list, int]:
    filters = []
    if role_filter is not None:
        filters.append(User.role == role_filter)
    if is_active_filter is not None:
        filters.append(User.is_active == is_active_filter)

    job_count_subq = (
        db.query(
            JobApplication.user_id.label("user_id"),
            func.count(JobApplication.id).label("job_count"),
        )
        .group_by(JobApplication.user_id)
        .subquery()
    )
    total = db.query(func.count(User.id)).filter(*filters).scalar() or 0
    rows = (
        db.query(User, func.coalesce(job_count_subq.c.job_count, 0).label("job_count"))
        .outerjoin(job_count_subq, User.id == job_count_subq.c.user_id)
        .filter(*filters)
        .order_by(User.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rows, total


def get_user_by_id(db: Session, user_id: int) -> tuple[User, int]:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user, _job_count(db, user_id)


def update_user_role(db: Session, user_id: int, new_role: str, actor_id: int) -> tuple[User, int]:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    old_role = user.role
    user.role = new_role
    log_admin_action(
        db, actor_id=actor_id, action="user.role_change", target_type="user",
        target_id=user_id, detail=json.dumps({"old_role": old_role, "new_role": new_role}),
    )
    db.commit()
    db.refresh(user)
    return user, _job_count(db, user_id)


def toggle_user_status(db: Session, user_id: int, actor_id: int) -> tuple[User, int]:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = not user.is_active
    action = "user.activate" if user.is_active else "user.deactivate"
    log_admin_action(
        db, actor_id=actor_id, action=action, target_type="user",
        target_id=user_id, detail=json.dumps({"is_active": user.is_active}),
    )
    db.commit()
    db.refresh(user)
    return user, _job_count(db, user_id)


def delete_user_by_id(db: Session, user_id: int, actor_id: int) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    log_admin_action(
        db, actor_id=actor_id, action="user.delete", target_type="user",
        target_id=user_id, detail=json.dumps({"email": user.email, "username": user.username}),
    )
    db.delete(user)
    db.commit()


def get_stats_overview(db: Session) -> dict:
    status_rows = (
        db.query(JobApplication.status, func.count(JobApplication.id).label("cnt"))
        .group_by(JobApplication.status)
        .all()
    )
    raw_counts = {row.status: row.cnt for row in status_rows}
    return {
        "total_users": db.query(func.count(User.id)).scalar() or 0,
        "active_users": db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0,
        "total_jobs": db.query(func.count(JobApplication.id)).scalar() or 0,
        "jobs_by_status": {s.value: raw_counts.get(s.value, 0) for s in ApplicationStatus},
    }


def get_audit_log(db: Session, skip: int = 0, limit: int = 50) -> tuple[list, int]:
    ActorAlias = aliased(User)
    total = db.query(func.count(AuditLog.id)).scalar() or 0
    rows = (
        db.query(AuditLog, ActorAlias.email.label("actor_email"))
        .outerjoin(ActorAlias, AuditLog.actor_id == ActorAlias.id)
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rows, total
