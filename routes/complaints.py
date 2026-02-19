from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from core.dependencies import get_current_user
from db.database import get_session
from db.models import User
from schemas.complaint import (
    ComplaintAssignRequest,
    ComplaintCreateRequest,
    ComplaintResponse,
    ComplaintStatusUpdateRequest,
)
from services.complaint_service import (
    assign_department,
    create_complaint,
    get_complaint_by_id,
    list_scope_complaints,
    update_complaint_status,
)

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintResponse)
def create_complaint_route(
    payload: ComplaintCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ComplaintResponse:
    return create_complaint(
        session=session,
        current_user=current_user,
        title=payload.title,
        description=payload.description,
    )


@router.get("/my", response_model=list[ComplaintResponse])
def list_my_complaints_route(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ComplaintResponse]:
    return list_scope_complaints(session=session, current_user=current_user)


@router.get("", response_model=list[ComplaintResponse])
def list_complaints_route(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ComplaintResponse]:
    return list_scope_complaints(session=session, current_user=current_user)


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint_by_id_route(
    complaint_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ComplaintResponse:
    return get_complaint_by_id(
        session=session,
        current_user=current_user,
        complaint_id=complaint_id,
    )


@router.patch("/{complaint_id}/assign", response_model=ComplaintResponse)
def assign_department_route(
    complaint_id: str,
    payload: ComplaintAssignRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ComplaintResponse:
    return assign_department(
        session=session,
        current_user=current_user,
        complaint_id=complaint_id,
        department_id=payload.department_id,
    )


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def update_status_route(
    complaint_id: str,
    payload: ComplaintStatusUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ComplaintResponse:
    return update_complaint_status(
        session=session,
        current_user=current_user,
        complaint_id=complaint_id,
        status_value=payload.status,
    )
