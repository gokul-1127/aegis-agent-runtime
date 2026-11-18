"""Pydantic schemas for Task requests and responses."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.task import TaskStatus


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    name: str = Field(..., min_length=1, max_length=255, description="Task name")
    description: Optional[str] = Field(None, description="Optional task description")
    input_payload: Optional[dict[str, Any]] = Field(
        None, description="Structured input data for the task"
    )


class TaskUpdate(BaseModel):
    """Schema for updating a task (used internally by the engine)."""

    status: Optional[TaskStatus] = None
    output_payload: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskResponse(BaseModel):
    """Schema for task responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    status: TaskStatus
    input_payload: Optional[dict[str, Any]] = None
    output_payload: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskResultResponse(BaseModel):
    """Schema for the result of a task execution."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: TaskStatus
    output_payload: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskListResponse(BaseModel):
    """Schema for paginated task listing."""

    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


def validate_uuid(value: str) -> str:
    """Validate that a string is a well-formed UUID."""
    try:
        uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError(f"Invalid UUID: {value!r}") from exc
    return str(value)