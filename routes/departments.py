from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from core.dependencies import get_current_user
from db.database import get_session
from db.models import Department, User
from schemas.department import DepartmentResponse

router = APIRouter(prefix="/api/departments", tags=["Departments"])


@router.get("", response_model=list[DepartmentResponse])
def list_departments_route(
    _: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[DepartmentResponse]:
    # Backfill for older DB records where department users existed
    # before rich department profile fields were introduced.
    department_users = session.exec(
        select(User).where(User.role == "department")
    ).all()
    existing_departments = session.exec(select(Department)).all()

    existing_by_user_id = {
        department.department_user_id for department in existing_departments if department.department_user_id
    }
    existing_department_names = {department.name for department in existing_departments}

    now = datetime.now(UTC)
    for department_user in department_users:
        if department_user.id in existing_by_user_id:
            continue
        if department_user.name in existing_department_names:
            continue

        session.add(
            Department(
                name=department_user.name,
                description=f"Department account for {department_user.name}",
                organization_name="Unknown Organization",
                contact_email=department_user.email,
                department_user_id=department_user.id,
                created_at=now,
                updated_at=now,
            )
        )

    session.commit()

    departments = session.exec(select(Department).order_by(Department.name.asc())).all()
    return [
        DepartmentResponse(
            id=department.id,
            name=department.name,
            description=department.description,
            organization_name=department.organization_name,
            organization_code=department.organization_code,
            department_code=department.department_code,
            contact_email=department.contact_email,
            contact_phone=department.contact_phone,
            created_at=department.created_at,
            updated_at=department.updated_at,
        )
        for department in departments
    ]
