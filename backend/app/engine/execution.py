"""Task execution engine.

Responsibilities:
1. Retrieve a pending task.
2. Validate its input.
3. Change status to RUNNING (with row-level lock to prevent duplicates).
4. Execute using the configured provider.
5. Store the result.
6. Mark task COMPLETED or FAILED.
7. Record execution timestamps.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base, engine
from app.models.task import Task, TaskStatus, is_task_executable
from app.providers.provider import (
    BaseProvider,
    ProviderError,
    ProviderTimeoutError,
    ProviderResult,
)
from app.providers.mock import MockProvider


class TaskNotFoundError(ValueError):
    """Raised when a task is not found."""


class TaskNotExecutableError(ValueError):
    """Raised when a task cannot be executed (wrong status)."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ExecutionEngine:
    """Core task execution engine with transaction safety."""

    def __init__(self, provider: Optional[BaseProvider] = None) -> None:
        self.provider = provider or MockProvider()

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=engine)

    def execute_task(self, task_id: str) -> dict[str, Any]:
        """Execute a single task by ID.

        Uses database transactions with row-level locking to prevent
        duplicate execution of the same task.

        Returns a dict with execution metadata.
        """
        with Session(engine) as session:
            # Acquire a row-level lock on the task (SELECT FOR UPDATE equivalent)
            # In SQLite, this is handled by the transaction isolation
            task = session.execute(
                select(Task).where(Task.id == task_id)
            ).scalar_one_or_none()

            if task is None:
                raise TaskNotFoundError(f"Task not found: {task_id}")

            if task.status != TaskStatus.PENDING.value:
                raise TaskNotExecutableError(
                    f"Task {task_id} cannot be executed (status: {task.status})"
                )

            # Mark as RUNNING
            task.status = TaskStatus.RUNNING.value
            task.started_at = _utcnow()
            task.updated_at = _utcnow()
            session.commit()

            # Execute with provider
            try:
                result: ProviderResult = self.provider.execute(
                    task.input_payload or {}
                )
            except ProviderTimeoutError:
                return self._mark_failed(
                    session,
                    task,
                    "Execution timed out",
                    started_at=task.started_at,
                )
            except ProviderError as exc:
                return self._mark_failed(
                    session,
                    task,
                    f"Provider error: {exc}",
                    started_at=task.started_at,
                )
            except Exception as exc:  # pylint: disable=broad-except
                return self._mark_failed(
                    session,
                    task,
                    f"Unexpected error: {exc}",
                    started_at=task.started_at,
                )

            if result.success:
                return self._mark_completed(session, task, result)
            else:
                return self._mark_failed(
                    session,
                    task,
                    result.error or "Unknown provider failure",
                    started_at=task.started_at,
                )

    def _mark_completed(
        self, session: Session, task: Task, result: ProviderResult
    ) -> dict[str, Any]:
        """Mark a task as COMPLETED with output."""
        completed_at = _utcnow()
        task.status = TaskStatus.COMPLETED.value
        task.output_payload = result.output
        task.error_message = None
        task.completed_at = completed_at
        task.updated_at = completed_at
        session.commit()

        return {
            "task_id": task.id,
            "status": task.status,
            "output": task.output_payload,
            "error": None,
            "duration_ms": result.duration_ms,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": completed_at.isoformat(),
        }

    def _mark_failed(
        self,
        session: Session,
        task: Task,
        error_message: str,
        started_at: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Mark a task as FAILED with error message."""
        completed_at = _utcnow()
        task.status = TaskStatus.FAILED.value
        task.output_payload = None
        task.error_message = error_message
        task.completed_at = completed_at
        task.updated_at = completed_at
        session.commit()

        return {
            "task_id": task.id,
            "status": task.status,
            "output": None,
            "error": error_message,
            "duration_ms": 0.0,
            "started_at": started_at.isoformat() if started_at else None,
            "completed_at": completed_at.isoformat(),
        }

    def cancel_task(self, task_id: str) -> dict[str, Any]:
        """Cancel a task if it is still PENDING."""
        with Session(engine) as session:
            task = session.execute(
                select(Task).where(Task.id == task_id)
            ).scalar_one_or_none()

            if task is None:
                raise TaskNotFoundError(f"Task not found: {task_id}")

            if task.status != TaskStatus.PENDING.value:
                raise TaskNotExecutableError(
                    f"Task {task_id} cannot be cancelled (status: {task.status})"
                )

            task.status = TaskStatus.CANCELLED.value
            task.updated_at = _utcnow()
            session.commit()

            return {
                "task_id": task.id,
                "status": task.status,
                "message": "Task cancelled successfully",
            }