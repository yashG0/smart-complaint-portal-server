from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from core.config import ACCESS_TOKEN_EXPIRE_DELTA
from core.security import create_access_token, hash_password, verify_password
from db.models import User
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


def register_user(*, session: Session, name: str, email: str, password: str, role: str) -> AuthResponse:
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
