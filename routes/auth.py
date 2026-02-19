from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from db.database import get_session
from schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from services.auth_service import login_user, register_user

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
def register_department(payload: RegisterRequest, session: Session = Depends(get_session)) -> AuthResponse:
    return register_user(
        session=session,
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role="department",
    )


@router.post("/admin/register", response_model=AuthResponse)
def register_admin(payload: RegisterRequest, session: Session = Depends(get_session)) -> AuthResponse:
    return register_user(
        session=session,
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role="admin",
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
