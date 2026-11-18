"""Task database model (SQLAlchemy 2.x)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, Index, String, Text, func, select
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.task import TaskStatus


def _utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


class Task(Base):
    """Represents an autonomous execution task."""

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TaskStatus.PENDING.value,
    )

    input_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_created_at", "created_at"),
        Index("ix_tasks_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Task(id={self.id!r}, name={self.name!r}, status={self.status!r})>"
        )


def is_task_executable(db, task_id: str) -> bool:
    """Return True if the task is currently PENDING and can be executed."""
    result = db.execute(
        select(Task.status).where(Task.id == task_id)
    ).scalar_one_or_none()
    return result == TaskStatus.PENDING.value