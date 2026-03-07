from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, select

from core.config import (
    ACCESS_TOKEN_EXPIRE_DELTA,
    PASSWORD_RESET_CODE_EXPIRE_MINUTES,
    PASSWORD_RESET_RESEND_SECONDS,
)
from core.security import create_access_token, hash_password, verify_password
from db.models import Department, PasswordResetCode, User
from schemas.auth import AuthResponse, UserResponse
from services.email_service import send_password_reset_code

ROLE_ALIASES = {
    "user": "student",
    "student": "student",
    "department": "department",
    "admin": "admin",
}


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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


def request_password_reset_code(*, session: Session, email: str, role: str) -> None:
    normalized_role = normalize_role(role)
    user = session.exec(select(User).where(User.email == email.lower())).first()
    if not user or user.role != normalized_role:
        # Do not reveal whether email exists.
        return

    now = datetime.now(UTC)
    recent_code = session.exec(
        select(PasswordResetCode)
        .where(PasswordResetCode.user_id == user.id)
        .where(PasswordResetCode.role == normalized_role)
        .order_by(PasswordResetCode.created_at.desc())
    ).first()
    if recent_code and (
        now - _as_utc(recent_code.created_at)
    ).total_seconds() < PASSWORD_RESET_RESEND_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting another reset code.",
        )

    code = f"{secrets.randbelow(10**6):06d}"
    reset_entry = PasswordResetCode(
        user_id=user.id,
        role=normalized_role,
        code_hash=hash_password(code),
        expires_at=now + timedelta(minutes=PASSWORD_RESET_CODE_EXPIRE_MINUTES),
        used=False,
        created_at=now,
    )
    session.add(reset_entry)
    session.commit()

    send_password_reset_code(to_email=user.email, code=code)


def reset_password_with_code(
    *,
    session: Session,
    email: str,
    role: str,
    code: str,
    new_password: str,
) -> None:
    normalized_role = normalize_role(role)
    user = session.exec(select(User).where(User.email == email.lower())).first()
    if not user or user.role != normalized_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset request.",
        )

    now = datetime.now(UTC)
    codes = session.exec(
        select(PasswordResetCode)
        .where(PasswordResetCode.user_id == user.id)
        .where(PasswordResetCode.role == normalized_role)
        .where(PasswordResetCode.used == False)  # noqa: E712
        .order_by(PasswordResetCode.created_at.desc())
    ).all()

    if not codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active reset code found. Request a new code.",
        )

    matched_code = None
    for entry in codes:
        if _as_utc(entry.expires_at) < now:
            continue
        if verify_password(code, entry.code_hash):
            matched_code = entry
            break

    if not matched_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code.",
        )

    matched_code.used = True
    user.password_hash = hash_password(new_password)
    user.updated_at = now

    session.add(matched_code)
    session.add(user)
    session.commit()
