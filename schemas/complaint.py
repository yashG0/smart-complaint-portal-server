from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ComplaintCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5, max_length=2000)


class ComplaintAssignRequest(BaseModel):
    department_id: str = Field(min_length=1)


class ComplaintStatusUpdateRequest(BaseModel):
    status: str = Field(min_length=2, max_length=50)


class ComplaintHistoryResponse(BaseModel):
    id: str
    complaint_id: str
    action: str
    changed_by: str
    timestamp: datetime


class ComplaintResponse(BaseModel):
    id: str
    user_id: str
    department_id: str | None
    title: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    history: list[ComplaintHistoryResponse] = []
