# Smart Complaint Portal (Backend)

FastAPI backend for role-based complaint management.

## Tech Stack
- FastAPI
- SQLModel
- SQLite (`complaints.db`)
- JWT (`python-jose`)
- Password hashing (`passlib`)
- SMTP email notifications (OTP + complaint updates)

## Run
```bash
cd backend
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Health:
```bash
curl http://127.0.0.1:8000/api/health
```

## Environment
Configure in `backend/.env`:
- `DATABASE_URL=sqlite:///./complaints.db`
- `JWT_SECRET_KEY=...`
- `JWT_ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`
- `PASSWORD_RESET_CODE_EXPIRE_MINUTES=10`
- `PASSWORD_RESET_RESEND_SECONDS=60`
- `SMTP_HOST=...`
- `SMTP_PORT=587`
- `SMTP_USERNAME=...`
- `SMTP_PASSWORD=...`
- `SMTP_FROM_EMAIL=...`
- `SMTP_USE_TLS=true`

## API Summary

Auth:
- `POST /api/auth/student/register`
- `POST /api/auth/department/register`
- `POST /api/auth/admin/register` (disabled by design, returns 403)
- `POST /api/auth/student/login`
- `POST /api/auth/department/login`
- `POST /api/auth/admin/login`
- `POST /api/auth/student/forgot-password`
- `POST /api/auth/department/forgot-password`
- `POST /api/auth/admin/forgot-password`
- `POST /api/auth/student/reset-password`
- `POST /api/auth/department/reset-password`
- `POST /api/auth/admin/reset-password`

Users:
- `GET /api/users/me`
- `PATCH /api/users/me`

Departments:
- `GET /api/departments`

Complaints:
- `POST /api/complaints` (student)
- `GET /api/complaints/my` (student/department/admin scoped)
- `GET /api/complaints`
- `GET /api/complaints/{complaint_id}`
- `GET /api/complaints/{complaint_id}/history`
- `PATCH /api/complaints/{complaint_id}/assign` (admin)
- `PATCH /api/complaints/{complaint_id}/status` (department/admin)

## Complaint Workflow Rules
- Allowed transitions:
  - `pending -> assigned/rejected`
  - `assigned -> in_progress/resolved/escalated`
  - `in_progress -> resolved/escalated`
  - `escalated -> in_progress/resolved/rejected`
  - `resolved` and `rejected` are terminal
- `assigned` status requires a valid `department_id`.

## Email Notifications
- OTP email for forgot-password flow.
- Student receives email when:
  - complaint is assigned
  - complaint status is updated
- Complaint notification emails run via FastAPI background tasks.

## Tests
```bash
cd backend
uv run pytest -q
```
Current suite covers auth, role guards, complaint assignment, transitions, history, and reset flow.

## Notes
- CORS currently includes localhost dev origins and configured GitHub Pages domain.
- Rotate secrets before public deployment.
