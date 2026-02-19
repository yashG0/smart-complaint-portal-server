from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserMeResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: datetime
    updated_at: datetime


class UpdateUserProfileRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
