"""Tests for the task execution engine."""
from __future__ import annotations

import uuid
from sqlalchemy import select

from app.db import SessionLocal, init_db
from app.engine.execution import ExecutionEngine
from app.models.task import Task, TaskStatus
from app.providers.mock import MockProvider


def test_execute_task_success():
    """Engine should execute a PENDING task successfully."""
    init_db()
    with SessionLocal() as db:
        task = Task(name="Success Task", input_payload={"data": "test"})
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id

    provider = MockProvider()
    engine = ExecutionEngine(provider=provider)

    result = engine.execute_task(task_id)

    assert result["status"] == TaskStatus.COMPLETED.value
    assert result["output"] is not None
    assert result["error"] is None
    assert result["duration_ms"] >= 0

    # Verify database state
    with SessionLocal() as db:
        task = db.execute(select(Task).where(Task.id == task_id)).scalar_one()
        assert task.status == TaskStatus.COMPLETED.value
        assert task.output_payload is not None
        assert task.started_at is not None
        assert task.completed_at is not None


def test_execute_task_failure():
    """Engine should mark task as FAILED when provider fails."""
    init_db()
    with SessionLocal() as db:
        task = Task(name="Failure Task", input_payload={"data": "test"})
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id

    provider = MockProvider(fail=True, failure_message="Simulated failure")
    engine = ExecutionEngine(provider=provider)

    result = engine.execute_task(task_id)

    assert result["status"] == TaskStatus.FAILED.value
    assert result["output"] is None
    assert result["error"] == "Simulated failure"

    with SessionLocal() as db:
        task = db.execute(select(Task).where(Task.id == task_id)).scalar_one()
        assert task.status == TaskStatus.FAILED.value
        assert task.error_message == "Simulated failure"


def test_execute_task_timeout():
    """Engine should handle provider timeout gracefully."""
    init_db()
    with SessionLocal() as db:
        task = Task(name="Timeout Task", input_payload={"data": "test"})
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id

    provider = MockProvider(timeout=True)
    engine = ExecutionEngine(provider=provider)

    result = engine.execute_task(task_id)

    assert result["status"] == TaskStatus.FAILED.value
    assert "timed out" in result["error"].lower()


def test_execute_task_not_found():
    """Engine should raise ValueError for non-existent task."""
    init_db()
    engine = ExecutionEngine()

    try:
        engine.execute_task(str(uuid.uuid4()))
        assert False, "Should have raised ValueError"
    except ValueError as exc:
        assert "not found" in str(exc).lower()


def test_execute_task_not_pending():
    """Engine should raise ValueError for non-PENDING task."""
    init_db()
    with SessionLocal() as db:
        task = Task(name="Running Task", status=TaskStatus.RUNNING.value)
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id

    engine = ExecutionEngine()

    try:
        engine.execute_task(task_id)
        assert False, "Should have raised ValueError"
    except ValueError as exc:
        assert "cannot be executed" in str(exc).lower()


def test_cancel_task_pending():
    """Engine should cancel a PENDING task."""
    init_db()
    with SessionLocal() as db:
        task = Task(name="Cancel Task")
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id

    engine = ExecutionEngine()
    result = engine.cancel_task(task_id)

    assert result["status"] == TaskStatus.CANCELLED.value

    with SessionLocal() as db:
        task = db.execute(select(Task).where(Task.id == task_id)).scalar_one()
        assert task.status == TaskStatus.CANCELLED.value


def test_cancel_task_not_pending():
    """Engine should raise ValueError when cancelling non-PENDING task."""
    init_db()
    with SessionLocal() as db:
        task = Task(name="Running Task", status=TaskStatus.RUNNING.value)
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id

    engine = ExecutionEngine()

    try:
        engine.cancel_task(task_id)
        assert False, "Should have raised ValueError"
    except ValueError as exc:
        assert "cannot be cancelled" in str(exc).lower()


def test_duplicate_execution_prevention():
    """Engine should prevent duplicate execution of the same task."""
    init_db()
    with SessionLocal() as db:
        task = Task(name="Duplicate Test", input_payload={"x": 1})
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id

    provider = MockProvider()
    engine = ExecutionEngine(provider=provider)

    # First execution
    result1 = engine.execute_task(task_id)
    assert result1["status"] == TaskStatus.COMPLETED.value

    # Second execution should fail
    try:
        engine.execute_task(task_id)
        assert False, "Should have raised ValueError"
    except ValueError as exc:
        assert "cannot be executed" in str(exc).lower()


def test_execution_timestamps():
    """Engine should record correct execution timestamps."""
    init_db()
    with SessionLocal() as db:
        task = Task(name="Timestamp Task", input_payload={})
        db.add(task)
        db.commit()
        db.refresh(task)
        task_id = task.id

    provider = MockProvider(delay_seconds=0.01)
    engine = ExecutionEngine(provider=provider)

    result = engine.execute_task(task_id)

    assert result["started_at"] is not None
    assert result["completed_at"] is not None
    assert result["completed_at"] >= result["started_at"]

    with SessionLocal() as db:
        task = db.execute(select(Task).where(Task.id == task_id)).scalar_one()
        assert task.started_at is not None
        assert task.completed_at is not None
        assert task.completed_at >= task.started_at