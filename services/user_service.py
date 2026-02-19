from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Session

from db.models import User
from schemas.user import UserMeResponse


def get_user_profile(current_user: User) -> UserMeResponse:
    return UserMeResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


def update_user_profile(*, session: Session, current_user: User, name: str) -> UserMeResponse:
    current_user.name = name.strip()
    current_user.updated_at = datetime.now(UTC)

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return get_user_profile(current_user)
