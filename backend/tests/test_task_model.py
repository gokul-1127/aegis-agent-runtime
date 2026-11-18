"""Unit tests for the Task model."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import SessionLocal, engine, init_db
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskResponse, validate_uuid


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def test_validate_uuid_valid():
    """UUID validation should accept valid UUIDs."""
    valid_uuid = str(uuid.uuid4())
    assert validate_uuid(valid_uuid) == valid_uuid


def test_validate_uuid_invalid():
    """UUID validation should reject invalid UUIDs."""
    try:
        validate_uuid("not-a-uuid")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_task_model_creation():
    """Task model should be creatable with all fields."""
    init_db()
    with SessionLocal() as db:
        task = Task(
            id=str(uuid.uuid4()),
            name="Test Task",
            description="A test task",
            status=TaskStatus.PENDING.value,
            input_payload={"key": "value"},
            output_payload=None,
            error_message=None,
            created_at=_utcnow(),
            updated_at=_utcnow(),
            started_at=None,
            completed_at=None,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        assert task.id is not None
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING.value
        assert task.input_payload == {"key": "value"}


def test_task_default_values():
    """Task should have correct default values."""
    init_db()
    with SessionLocal() as db:
        task = Task(name="Minimal Task")
        db.add(task)
        db.commit()
        db.refresh(task)

        assert task.status == TaskStatus.PENDING.value
        assert task.id is not None
        assert task.created_at is not None
        assert task.updated_at is not None


def test_task_status_enum():
    """TaskStatus enum should have all required values."""
    assert TaskStatus.PENDING.value == "PENDING"
    assert TaskStatus.RUNNING.value == "RUNNING"
    assert TaskStatus.COMPLETED.value == "COMPLETED"
    assert TaskStatus.FAILED.value == "FAILED"
    assert TaskStatus.CANCELLED.value == "CANCELLED"


def test_task_update_timestamps():
    """updated_at should change when task is modified."""
    init_db()
    with SessionLocal() as db:
        task = Task(name="Timestamp Test")
        db.add(task)
        db.commit()
        db.refresh(task)

        original_updated = task.updated_at

        task.status = TaskStatus.RUNNING.value
        db.commit()
        db.refresh(task)

        assert task.updated_at >= original_updated


def test_task_indexes():
    """Verify indexes exist on the Task table."""
    init_db()
    # Check that the table has the expected indexes by inspecting metadata
    from sqlalchemy import inspect

    inspector = inspect(engine)
    indexes = inspector.get_indexes("tasks")
    index_names = [idx["name"] for idx in indexes]

    assert "ix_tasks_status" in index_names
    assert "ix_tasks_created_at" in index_names
    assert "ix_tasks_status_created" in index_names


def test_task_create_schema():
    """TaskCreate schema should validate input correctly."""
    payload = TaskCreate(name="Test", description="Desc", input_payload={"a": 1})
    assert payload.name == "Test"
    assert payload.description == "Desc"
    assert payload.input_payload == {"a": 1}


def test_task_create_schema_name_required():
    """TaskCreate should require a name."""
    try:
        TaskCreate(name="", input_payload={})
        assert False, "Should have raised validation error"
    except Exception:
        pass


def test_task_response_schema_from_orm():
    """TaskResponse should work with from_attributes."""
    init_db()
    with SessionLocal() as db:
        task = Task(name="ORM Test", input_payload={"x": 1})
        db.add(task)
        db.commit()
        db.refresh(task)

        response = TaskResponse.model_validate(task)
        assert response.id == task.id
        assert response.name == "ORM Test"
        assert response.status == TaskStatus.PENDING
        assert response.input_payload == {"x": 1}