from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select

from core.security import hash_password
import db.database as database_module
import services.auth_service as auth_service
from db.models import User
from main import app


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "test_complaints.db"
    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    old_engine = database_module.engine
    old_database_url = database_module.DATABASE_URL

    database_module.engine = test_engine
    database_module.DATABASE_URL = f"sqlite:///{db_path}"

    try:
        database_module.init_db()
        with TestClient(app) as test_client:
            yield test_client
    finally:
        database_module.engine = old_engine
        database_module.DATABASE_URL = old_database_url


def _register_student(client: TestClient, email: str = "student@test.com") -> dict:
    response = client.post(
        "/api/auth/student/register",
        json={
            "name": "Student One",
            "email": email,
            "password": "strongpass123",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _bootstrap_admin(client: TestClient, email: str = "admin@test.com") -> dict:
    now = datetime.now(UTC)
    with Session(database_module.engine) as session:
        existing = session.exec(select(User).where(User.email == email.lower())).first()
        if not existing:
            session.add(
                User(
                    name="Admin One",
                    email=email.lower(),
                    password_hash=hash_password("strongpass123"),
                    role="admin",
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()

    response = client.post(
        "/api/auth/admin/login",
        json={
            "email": email,
            "password": "strongpass123",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _register_department(client: TestClient, email: str = "dept@test.com") -> dict:
    response = client.post(
        "/api/auth/department/register",
        json={
            "name": "IT Department",
            "email": email,
            "password": "strongpass123",
            "organization_name": "Demo College",
            "department_description": "Handles IT complaints",
            "organization_code": "DC-01",
            "department_code": "IT-01",
            "contact_email": email,
            "contact_phone": "9999999999",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_student_auth_and_create_complaint(client: TestClient) -> None:
    student = _register_student(client)
    token = student["access_token"]

    create_response = client.post(
        "/api/complaints",
        json={
            "title": "Water leakage in hostel",
            "description": "Hostel A second floor washroom has continuous leakage.",
        },
        headers=_auth_headers(token),
    )
    assert create_response.status_code == 200, create_response.text
    complaint = create_response.json()
    assert complaint["title"] == "Water leakage in hostel"
    assert complaint["status"] == "pending"


def test_role_guard_blocks_student_from_admin_actions(client: TestClient) -> None:
    student = _register_student(client)
    _bootstrap_admin(client)
    _register_department(client)

    student_token = student["access_token"]

    create_response = client.post(
        "/api/complaints",
        json={
            "title": "Lab projector not working",
            "description": "Projector in CS lab is blank during classes.",
        },
        headers=_auth_headers(student_token),
    )
    complaint_id = create_response.json()["id"]

    assign_response = client.patch(
        f"/api/complaints/{complaint_id}/assign",
        json={"department_id": "fake-department-id"},
        headers=_auth_headers(student_token),
    )
    assert assign_response.status_code == 403

    status_response = client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "in_progress"},
        headers=_auth_headers(student_token),
    )
    assert status_response.status_code == 403


def test_complaint_assignment_transitions_and_history(client: TestClient) -> None:
    student = _register_student(client)
    admin = _bootstrap_admin(client)
    department = _register_department(client)

    student_token = student["access_token"]
    admin_token = admin["access_token"]
    department_token = department["access_token"]

    departments_response = client.get(
        "/api/departments",
        headers=_auth_headers(admin_token),
    )
    assert departments_response.status_code == 200
    departments = departments_response.json()
    department_id = departments[0]["id"]

    create_response = client.post(
        "/api/complaints",
        json={
            "title": "Wi-Fi down in block B",
            "description": "No internet in classrooms in block B since morning.",
        },
        headers=_auth_headers(student_token),
    )
    assert create_response.status_code == 200
    complaint_id = create_response.json()["id"]

    assign_response = client.patch(
        f"/api/complaints/{complaint_id}/assign",
        json={"department_id": department_id},
        headers=_auth_headers(admin_token),
    )
    assert assign_response.status_code == 200, assign_response.text
    assert assign_response.json()["status"] == "assigned"

    in_progress_response = client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "in_progress"},
        headers=_auth_headers(department_token),
    )
    assert in_progress_response.status_code == 200
    assert in_progress_response.json()["status"] == "in_progress"

    resolved_response = client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "resolved"},
        headers=_auth_headers(department_token),
    )
    assert resolved_response.status_code == 200
    assert resolved_response.json()["status"] == "resolved"

    invalid_back_transition = client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "in_progress"},
        headers=_auth_headers(department_token),
    )
    assert invalid_back_transition.status_code == 409

    history_response = client.get(
        f"/api/complaints/{complaint_id}/history",
        headers=_auth_headers(student_token),
    )
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) >= 4
    actions = [item["action"] for item in history]
    assert "created" in actions
    assert any(action.startswith("assigned_department:") for action in actions)
    assert "status_updated:in_progress" in actions
    assert "status_updated:resolved" in actions


def test_admin_invalid_transition_pending_to_resolved_fails(client: TestClient) -> None:
    student = _register_student(client)
    admin = _bootstrap_admin(client)

    student_token = student["access_token"]
    admin_token = admin["access_token"]

    create_response = client.post(
        "/api/complaints",
        json={
            "title": "Broken chair in room 204",
            "description": "Chair leg is broken and unsafe for students.",
        },
        headers=_auth_headers(student_token),
    )
    complaint_id = create_response.json()["id"]

    transition_response = client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "resolved"},
        headers=_auth_headers(admin_token),
    )
    assert transition_response.status_code == 409


def test_forgot_password_with_code_flow(client: TestClient, monkeypatch) -> None:
    _register_student(client, email="resetstudent@test.com")
    sent_codes: list[str] = []

    monkeypatch.setattr(auth_service.secrets, "randbelow", lambda _: 123456)
    monkeypatch.setattr(
        auth_service,
        "send_password_reset_code",
        lambda *, to_email, code: sent_codes.append(code),
    )

    forgot_response = client.post(
        "/api/auth/student/forgot-password",
        json={"email": "resetstudent@test.com"},
    )
    assert forgot_response.status_code == 200, forgot_response.text
    assert sent_codes == ["123456"]

    reset_response = client.post(
        "/api/auth/student/reset-password",
        json={
            "email": "resetstudent@test.com",
            "code": "123456",
            "new_password": "newpass123",
        },
    )
    assert reset_response.status_code == 200, reset_response.text

    login_response = client.post(
        "/api/auth/student/login",
        json={
            "email": "resetstudent@test.com",
            "password": "newpass123",
        },
    )
    assert login_response.status_code == 200, login_response.text
