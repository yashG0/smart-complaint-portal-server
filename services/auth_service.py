from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from core.config import ACCESS_TOKEN_EXPIRE_DELTA
from core.security import create_access_token, hash_password, verify_password
from db.models import Department, User
from schemas.auth import AuthResponse, UserResponse

ROLE_ALIASES = {
    "user": "student",
    "student": "student",
    "department": "department",
    "admin": "admin",
}


def normalize_role(role: str) -> str:
    normalized = role.strip().lower()
    return ROLE_ALIASES.get(normalized, normalized)


def _build_auth_response(user: User) -> AuthResponse:
    token = create_access_token(
        subject=user.id,
        role=user.role,
        expires_delta=ACCESS_TOKEN_EXPIRE_DELTA,
    )

    return AuthResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ),
    )


def register_user(
    *,
    session: Session,
    name: str,
    email: str,
    password: str,
    role: str,
    organization_name: str | None = None,
    department_description: str | None = None,
    organization_code: str | None = None,
    department_code: str | None = None,
    contact_email: str | None = None,
    contact_phone: str | None = None,
) -> AuthResponse:
    normalized_role = normalize_role(role)

    existing_user = session.exec(select(User).where(User.email == email.lower())).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    now = datetime.now(UTC)
    user = User(
        name=name.strip(),
        email=email.lower(),
        password_hash=hash_password(password),
        role=normalized_role,
        created_at=now,
        updated_at=now,
    )
    session.add(user)

    if normalized_role == "department":
        organization_name_value = (organization_name or "").strip()
        if not organization_name_value:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="organization_name is required for department registration.",
            )

        existing_department = session.exec(
            select(Department).where(Department.name == user.name)
        ).first()
        if existing_department:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Department name is already registered.",
            )

        if organization_code:
            org_code_exists = session.exec(
                select(Department).where(Department.organization_code == organization_code.strip())
            ).first()
            if org_code_exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Organization code is already in use.",
                )

        if department_code:
            dept_code_exists = session.exec(
                select(Department).where(Department.department_code == department_code.strip())
            ).first()
            if dept_code_exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Department code is already in use.",
                )

        department = Department(
            name=user.name,
            description=(department_description or "").strip(),
            organization_name=organization_name_value,
            organization_code=(organization_code or "").strip() or None,
            department_code=(department_code or "").strip() or None,
            contact_email=(contact_email or user.email).strip() or None,
            contact_phone=(contact_phone or "").strip() or None,
            department_user_id=user.id,
            created_at=now,
            updated_at=now,
        )
        session.add(department)

    session.commit()
    session.refresh(user)

    return _build_auth_response(user)


def login_user(*, session: Session, email: str, password: str, role: str | None = None) -> AuthResponse:
    user = session.exec(select(User).where(User.email == email.lower())).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if role and user.role != normalize_role(role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role mismatch for this login endpoint.",
        )

    return _build_auth_response(user)
