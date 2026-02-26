from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from core.dependencies import require_roles
from db.database import get_session
from db.models import User
from schemas.user import UpdateUserProfileRequest, UserMeResponse
from services.user_service import get_user_profile, update_user_profile

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserMeResponse)
def get_me_route(
    current_user: User = Depends(require_roles("student", "department", "admin"))
) -> UserMeResponse:
    return get_user_profile(current_user)


@router.patch("/me", response_model=UserMeResponse)
def update_me_route(
    payload: UpdateUserProfileRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("student", "department", "admin")),
) -> UserMeResponse:
    return update_user_profile(
        session=session,
        current_user=current_user,
        name=payload.name,
    )
