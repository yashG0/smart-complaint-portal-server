from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlmodel import Session

from core.dependencies import require_roles
from db.database import get_session
from db.models import User
from schemas.complaint import (
    ComplaintAssignRequest,
    ComplaintCreateRequest,
    ComplaintHistoryResponse,
    ComplaintResponse,
    ComplaintStatusUpdateRequest,
)
from services.complaint_service import (
    assign_department,
    create_complaint,
    get_complaint_history,
    get_complaint_by_id,
    list_scope_complaints,
    update_complaint_status,
)

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintResponse)
def create_complaint_route(
    payload: ComplaintCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("student")),
) -> ComplaintResponse:
    return create_complaint(
        session=session,
        current_user=current_user,
        title=payload.title,
        description=payload.description,
        department_id=payload.department_id,
    )


@router.get("/my", response_model=list[ComplaintResponse])
def list_my_complaints_route(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("student", "department", "admin")),
) -> list[ComplaintResponse]:
    return list_scope_complaints(session=session, current_user=current_user)


@router.get("", response_model=list[ComplaintResponse])
def list_complaints_route(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("student", "department", "admin")),
) -> list[ComplaintResponse]:
    return list_scope_complaints(session=session, current_user=current_user)


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint_by_id_route(
    complaint_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("student", "department", "admin")),
) -> ComplaintResponse:
    return get_complaint_by_id(
        session=session,
        current_user=current_user,
        complaint_id=complaint_id,
    )


@router.get("/{complaint_id}/history", response_model=list[ComplaintHistoryResponse])
def get_complaint_history_route(
    complaint_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("student", "department", "admin")),
) -> list[ComplaintHistoryResponse]:
    return get_complaint_history(
        session=session,
        current_user=current_user,
        complaint_id=complaint_id,
    )


@router.patch("/{complaint_id}/assign", response_model=ComplaintResponse)
def assign_department_route(
    complaint_id: str,
    payload: ComplaintAssignRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
) -> ComplaintResponse:
    return assign_department(
        session=session,
        current_user=current_user,
        complaint_id=complaint_id,
        department_id=payload.department_id,
        background_tasks=background_tasks,
    )


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def update_status_route(
    complaint_id: str,
    payload: ComplaintStatusUpdateRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("department", "admin")),
) -> ComplaintResponse:
    return update_complaint_status(
        session=session,
        current_user=current_user,
        complaint_id=complaint_id,
        status_value=payload.status,
        background_tasks=background_tasks,
    )
