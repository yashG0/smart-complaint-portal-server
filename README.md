# Smart Complaint Portal (Backend)

FastAPI backend for role-based complaint workflow.

## Stack
- FastAPI
- SQLModel
- SQLite
- JWT auth (`python-jose`)
- Password hashing (`passlib`)

## Run
```bash
cd backend
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Health check:
```bash
curl http://127.0.0.1:8000/api/health
```

## Tests
```bash
cd backend
uv run pytest -q
```

Current tests include auth + role guards + complaint assignment + transitions + history.

## Core Endpoints

Auth:
- `POST /api/auth/student/register`
- `POST /api/auth/department/register`
- `POST /api/auth/admin/register`
- `POST /api/auth/student/login`
- `POST /api/auth/department/login`
- `POST /api/auth/admin/login`

Users:
- `GET /api/users/me`
- `PATCH /api/users/me`

Departments:
- `GET /api/departments`

Complaints:
- `POST /api/complaints`
- `GET /api/complaints/my`
- `GET /api/complaints`
- `GET /api/complaints/{complaint_id}`
- `GET /api/complaints/{complaint_id}/history`
- `PATCH /api/complaints/{complaint_id}/assign` (admin)
- `PATCH /api/complaints/{complaint_id}/status` (department/admin)

## Status Rules
Allowed transitions:
- `pending -> assigned/rejected`
- `assigned -> in_progress/resolved/escalated`
- `in_progress -> resolved/escalated`
- `escalated -> in_progress/resolved/rejected`
- `resolved/rejected` are terminal

## Notes
- DB file: `complaints.db`
- CORS allows localhost `5500` and `3000`.
