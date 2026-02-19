from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DepartmentResponse(BaseModel):
    id: str
    name: str
    description: str
    organization_name: str
    organization_code: str | None = None
    department_code: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    created_at: datetime
    updated_at: datetime
