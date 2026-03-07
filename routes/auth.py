from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from db.database import get_session
from schemas.auth import (
    AuthResponse,
    DepartmentRegisterRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordWithCodeRequest,
    RegisterRequest,
)
from services.auth_service import (
    login_user,
    register_user,
    request_password_reset_code,
    reset_password_with_code,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/student/register", response_model=AuthResponse)
def register_student(payload: RegisterRequest, session: Session = Depends(get_session)) -> AuthResponse:
    return register_user(
        session=session,
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role="student",
    )


@router.post("/department/register", response_model=AuthResponse)
def register_department(
    payload: DepartmentRegisterRequest,
    session: Session = Depends(get_session),
) -> AuthResponse:
    return register_user(
        session=session,
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role="department",
        organization_name=payload.organization_name,
        department_description=payload.department_description,
        organization_code=payload.organization_code,
        department_code=payload.department_code,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
    )


@router.post("/admin/register", response_model=AuthResponse)
def register_admin(payload: RegisterRequest, session: Session = Depends(get_session)) -> AuthResponse:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin self-registration is disabled.",
    )


@router.post("/user/register", response_model=AuthResponse)
def register_user_alias(payload: RegisterRequest, session: Session = Depends(get_session)) -> AuthResponse:
    return register_user(
        session=session,
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role="student",
    )


@router.post("/register", response_model=AuthResponse)
def register_generic(payload: RegisterRequest, session: Session = Depends(get_session)) -> AuthResponse:
    return register_user(
        session=session,
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role="student",
    )


@router.post("/student/login", response_model=AuthResponse)
def login_student(payload: LoginRequest, session: Session = Depends(get_session)) -> AuthResponse:
    return login_user(
        session=session,
        email=payload.email,
        password=payload.password,
        role="student",
    )


@router.post("/department/login", response_model=AuthResponse)
def login_department(payload: LoginRequest, session: Session = Depends(get_session)) -> AuthResponse:
    return login_user(
        session=session,
        email=payload.email,
        password=payload.password,
        role="department",
    )


@router.post("/admin/login", response_model=AuthResponse)
def login_admin(payload: LoginRequest, session: Session = Depends(get_session)) -> AuthResponse:
    return login_user(
        session=session,
        email=payload.email,
        password=payload.password,
        role="admin",
    )


@router.post("/user/login", response_model=AuthResponse)
def login_user_alias(payload: LoginRequest, session: Session = Depends(get_session)) -> AuthResponse:
    return login_user(
        session=session,
        email=payload.email,
        password=payload.password,
        role="student",
    )


@router.post("/login", response_model=AuthResponse)
def login_generic(payload: LoginRequest, session: Session = Depends(get_session)) -> AuthResponse:
    return login_user(
        session=session,
        email=payload.email,
        password=payload.password,
    )


@router.post("/student/forgot-password")
def student_forgot_password(
    payload: ForgotPasswordRequest,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    request_password_reset_code(
        session=session,
        email=payload.email,
        role="student",
    )
    return {"message": "If account exists, reset code has been sent to email."}


@router.post("/department/forgot-password")
def department_forgot_password(
    payload: ForgotPasswordRequest,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    request_password_reset_code(
        session=session,
        email=payload.email,
        role="department",
    )
    return {"message": "If account exists, reset code has been sent to email."}


@router.post("/admin/forgot-password")
def admin_forgot_password(
    payload: ForgotPasswordRequest,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    request_password_reset_code(
        session=session,
        email=payload.email,
        role="admin",
    )
    return {"message": "If account exists, reset code has been sent to email."}


@router.post("/student/reset-password")
def student_reset_password(
    payload: ResetPasswordWithCodeRequest,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    reset_password_with_code(
        session=session,
        email=payload.email,
        role="student",
        code=payload.code,
        new_password=payload.new_password,
    )
    return {"message": "Password reset successful."}


@router.post("/department/reset-password")
def department_reset_password(
    payload: ResetPasswordWithCodeRequest,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    reset_password_with_code(
        session=session,
        email=payload.email,
        role="department",
        code=payload.code,
        new_password=payload.new_password,
    )
    return {"message": "Password reset successful."}


@router.post("/admin/reset-password")
def admin_reset_password(
    payload: ResetPasswordWithCodeRequest,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    reset_password_with_code(
        session=session,
        email=payload.email,
        role="admin",
        code=payload.code,
        new_password=payload.new_password,
    )
    return {"message": "Password reset successful."}
