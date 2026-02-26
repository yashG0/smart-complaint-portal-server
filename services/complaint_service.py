from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from db.models import Complaint, ComplaintHistory, Department, User
from schemas.complaint import ComplaintHistoryResponse, ComplaintResponse

ALLOWED_STATUS = {
    "pending",
    "assigned",
    "in_progress",
    "resolved",
    "rejected",
    "escalated",
}

STATUS_ALIASES = {
    "in progress": "in_progress",
}

VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"assigned", "rejected"},
    "assigned": {"in_progress", "resolved", "escalated"},
    "in_progress": {"resolved", "escalated"},
    "escalated": {"in_progress", "resolved", "rejected"},
    "resolved": set(),
    "rejected": set(),
}

DEPARTMENT_ALLOWED_TARGETS = {"in_progress", "resolved", "escalated"}


def _now() -> datetime:
    return datetime.now(UTC)


def _get_department_for_user(session: Session, user_id: str) -> Department | None:
    return session.exec(
        select(Department).where(Department.department_user_id == user_id)
    ).first()


def _normalize_status(status_value: str) -> str:
    normalized = status_value.strip().lower()
    return STATUS_ALIASES.get(normalized, normalized)


def _assert_valid_transition(*, current_status: str, next_status: str) -> None:
    if current_status == next_status:
        return

    allowed_next = VALID_TRANSITIONS.get(current_status, set())
    if next_status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Invalid status transition from '{current_status}' to '{next_status}'."
            ),
        )


def _build_history_responses(entries: list[ComplaintHistory]) -> list[ComplaintHistoryResponse]:
    return [
        ComplaintHistoryResponse(
            id=item.id,
            complaint_id=item.complaint_id,
            action=item.action,
            changed_by=item.changed_by,
            timestamp=item.timestamp,
        )
        for item in entries
    ]


def _build_complaint_response(
    *,
    session: Session,
    complaint: Complaint,
    include_history: bool = True,
) -> ComplaintResponse:
    history_entries: list[ComplaintHistoryResponse] = []
    if include_history:
        entries = session.exec(
            select(ComplaintHistory)
            .where(ComplaintHistory.complaint_id == complaint.id)
            .order_by(ComplaintHistory.timestamp.asc())
        ).all()
        history_entries = _build_history_responses(entries)

    department_name = None
    if complaint.department_id:
        department = session.get(Department, complaint.department_id)
        department_name = department.name if department else None

    return ComplaintResponse(
        id=complaint.id,
        user_id=complaint.user_id,
        department_id=complaint.department_id,
        department_name=department_name,
        title=complaint.title,
        description=complaint.description,
        status=complaint.status,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        history=history_entries,
    )


def _create_history_entry(
    *,
    complaint_id: str,
    action: str,
    changed_by: str,
) -> ComplaintHistory:
    return ComplaintHistory(
        complaint_id=complaint_id,
        action=action,
        changed_by=changed_by,
        timestamp=_now(),
    )


def _get_complaint_or_404(session: Session, complaint_id: str) -> Complaint:
    complaint = session.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )
    return complaint


def _assert_view_access(session: Session, user: User, complaint: Complaint) -> None:
    if user.role == "admin":
        return

    if user.role == "student" and complaint.user_id == user.id:
        return

    if user.role == "department":
        department = _get_department_for_user(session, user.id)
        if department and complaint.department_id == department.id:
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this complaint.",
    )


def create_complaint(
    *,
    session: Session,
    current_user: User,
    title: str,
    description: str,
    department_id: str | None = None,
) -> ComplaintResponse:
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can create complaints.",
        )

    department = None
    if department_id:
        department = session.get(Department, department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found.",
            )

    now = _now()
    complaint = Complaint(
        user_id=current_user.id,
        department_id=department.id if department else None,
        title=title.strip(),
        description=description.strip(),
        status="assigned" if department else "pending",
        created_at=now,
        updated_at=now,
    )
    session.add(complaint)
    session.commit()
    session.refresh(complaint)

    history = _create_history_entry(
        complaint_id=complaint.id,
        action=(
            f"created_with_department:{department.id}"
            if department
            else "created"
        ),
        changed_by=current_user.id,
    )
    session.add(history)
    session.commit()

    return _build_complaint_response(session=session, complaint=complaint)


def list_scope_complaints(*, session: Session, current_user: User) -> list[ComplaintResponse]:
    statement = select(Complaint).order_by(Complaint.created_at.desc())

    if current_user.role == "student":
        statement = statement.where(Complaint.user_id == current_user.id)
    elif current_user.role == "department":
        department = _get_department_for_user(session, current_user.id)
        if not department:
            return []
        statement = statement.where(Complaint.department_id == department.id)

    complaints = session.exec(statement).all()
    return [
        _build_complaint_response(session=session, complaint=item, include_history=False)
        for item in complaints
    ]


def get_complaint_by_id(*, session: Session, current_user: User, complaint_id: str) -> ComplaintResponse:
    complaint = _get_complaint_or_404(session, complaint_id)
    _assert_view_access(session, current_user, complaint)
    return _build_complaint_response(session=session, complaint=complaint)


def get_complaint_history(
    *, session: Session, current_user: User, complaint_id: str
) -> list[ComplaintHistoryResponse]:
    complaint = _get_complaint_or_404(session, complaint_id)
    _assert_view_access(session, current_user, complaint)

    entries = session.exec(
        select(ComplaintHistory)
        .where(ComplaintHistory.complaint_id == complaint.id)
        .order_by(ComplaintHistory.timestamp.asc())
    ).all()
    return _build_history_responses(entries)


def assign_department(
    *,
    session: Session,
    current_user: User,
    complaint_id: str,
    department_id: str,
) -> ComplaintResponse:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign departments.",
        )

    complaint = _get_complaint_or_404(session, complaint_id)
    if complaint.status in {"resolved", "rejected"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot assign a closed complaint.",
        )

    department = session.get(Department, department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found.",
        )

    complaint.department_id = department.id
    complaint.status = "assigned"
    complaint.updated_at = _now()
    session.add(complaint)

    history = _create_history_entry(
        complaint_id=complaint.id,
        action=f"assigned_department:{department.id}",
        changed_by=current_user.id,
    )
    session.add(history)

    session.commit()
    session.refresh(complaint)

    return _build_complaint_response(session=session, complaint=complaint)


def update_complaint_status(
    *,
    session: Session,
    current_user: User,
    complaint_id: str,
    status_value: str,
) -> ComplaintResponse:
    normalized_status = _normalize_status(status_value)
    if normalized_status not in ALLOWED_STATUS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{status_value}'.",
        )

    complaint = _get_complaint_or_404(session, complaint_id)

    current_status = _normalize_status(complaint.status)

    if current_user.role == "admin":
        _assert_valid_transition(current_status=current_status, next_status=normalized_status)
    elif current_user.role == "department":
        department = _get_department_for_user(session, current_user.id)
        if not department or complaint.department_id != department.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update complaint status.",
            )
        if normalized_status not in DEPARTMENT_ALLOWED_TARGETS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Department can only set status to in_progress, resolved, or escalated.",
            )
        _assert_valid_transition(current_status=current_status, next_status=normalized_status)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update complaint status.",
        )

    complaint.status = normalized_status
    complaint.updated_at = _now()
    session.add(complaint)

    history = _create_history_entry(
        complaint_id=complaint.id,
        action=f"status_updated:{normalized_status}",
        changed_by=current_user.id,
    )
    session.add(history)

    session.commit()
    session.refresh(complaint)

    return _build_complaint_response(session=session, complaint=complaint)
