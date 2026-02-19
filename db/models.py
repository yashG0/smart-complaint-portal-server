from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: str = Field(index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    complaints: list["Complaint"] = Relationship(back_populates="user")
    complaint_history_entries: list["ComplaintHistory"] = Relationship(
        back_populates="changed_by_user"
    )


class Department(SQLModel, table=True):
    __tablename__ = "departments"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str

    complaints: list["Complaint"] = Relationship(back_populates="department")


class Complaint(SQLModel, table=True):
    __tablename__ = "complaints"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    department_id: Optional[str] = Field(default=None, foreign_key="departments.id", index=True)
    title: str
    description: str
    status: str = Field(default="pending", index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user: Optional[User] = Relationship(back_populates="complaints")
    department: Optional[Department] = Relationship(back_populates="complaints")
    history: list["ComplaintHistory"] = Relationship(back_populates="complaint")


class ComplaintHistory(SQLModel, table=True):
    __tablename__ = "complaint_history"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    complaint_id: str = Field(foreign_key="complaints.id", index=True)
    action: str
    changed_by: str = Field(foreign_key="users.id", index=True)
    timestamp: datetime = Field(default_factory=utc_now, index=True)

    complaint: Optional[Complaint] = Relationship(back_populates="history")
    changed_by_user: Optional[User] = Relationship(back_populates="complaint_history_entries")
