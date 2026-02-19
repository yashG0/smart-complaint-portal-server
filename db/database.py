from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./complaints.db")

connect_args: dict[str, object] = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def _sqlite_add_department_columns_if_missing() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "departments" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("departments")}

    # Safe dev migration for existing SQLite files.
    additions = [
        ("organization_name", "TEXT"),
        ("organization_code", "TEXT"),
        ("department_code", "TEXT"),
        ("contact_email", "TEXT"),
        ("contact_phone", "TEXT"),
        ("department_user_id", "TEXT"),
        ("created_at", "TEXT"),
        ("updated_at", "TEXT"),
    ]

    with engine.begin() as connection:
        for column_name, column_type in additions:
            if column_name not in columns:
                connection.execute(
                    text(
                        f"ALTER TABLE departments ADD COLUMN {column_name} {column_type}"  # noqa: S608
                    )
                )


def init_db() -> None:
    # Import models so SQLModel registers table metadata before create_all.
    from db import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _sqlite_add_department_columns_if_missing()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
