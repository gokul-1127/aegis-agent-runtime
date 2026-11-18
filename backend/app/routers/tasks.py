"""Task API endpoints."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.engine.execution import (
    ExecutionEngine,
    TaskNotFoundError,
    TaskNotExecutableError,
)
from app.models.task import Task, TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskResultResponse,
    validate_uuid,
)

router = APIRouter()

# Global execution engine instance (created once, reused)
_execution_engine: ExecutionEngine | None = None


def get_engine() -> ExecutionEngine:
    """Get or create the execution engine."""
    global _execution_engine
    if _execution_engine is None:
        _execution_engine = ExecutionEngine()
        _execution_engine.create_tables()
    return _execution_engine


def _task_to_response(task: Task) -> TaskResponse:
    """Convert a Task ORM model to a TaskResponse schema."""
    return TaskResponse.model_validate(task)


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Create a new task with PENDING status.",
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Create a new task."""
    task = Task(
        name=payload.name,
        description=payload.description,
        input_payload=payload.input_payload,
        status=TaskStatus.PENDING.value,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _task_to_response(task)


@router.get(
    "/tasks",
    response_model=TaskListResponse,
    summary="List tasks",
    description="List tasks with pagination. Default page size is 20, max 100.",
)
def list_tasks(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    status_filter: TaskStatus | None = Query(
        None, description="Filter by task status", alias="status"
    ),
    db: Session = Depends(get_db),
) -> TaskListResponse:
    """List tasks with pagination and optional status filter."""
    query = select(Task).order_by(Task.created_at.desc())

    if status_filter:
        query = query.where(Task.status == status_filter.value)

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

    items = db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    return TaskListResponse(
        items=[_task_to_response(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get a task by ID",
    description="Retrieve a single task by its UUID.",
)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Retrieve a single task by ID."""
    try:
        validated_id = validate_uuid(task_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    task = db.execute(
        select(Task).where(Task.id == validated_id)
    ).scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    return _task_to_response(task)


@router.post(
    "/tasks/{task_id}/execute",
    response_model=TaskResultResponse,
    summary="Execute a task",
    description="Execute a PENDING task. Changes status to RUNNING, then COMPLETED or FAILED.",
)
def execute_task(
    task_id: str,
    engine: ExecutionEngine = Depends(get_engine),
) -> TaskResultResponse:
    """Execute a pending task."""
    try:
        validated_id = validate_uuid(task_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    try:
        result = engine.execute_task(validated_id)
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except TaskNotExecutableError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return TaskResultResponse(
        id=result["task_id"],
        name=result.get("name", ""),  # Will be populated from DB in a real impl
        status=result["status"],
        output_payload=result["output"],
        error_message=result["error"],
        started_at=(
            None
            if result["started_at"] is None
            else datetime.fromisoformat(result["started_at"])
        ),
        completed_at=(
            None
            if result["completed_at"] is None
            else datetime.fromisoformat(result["completed_at"])
        ),
    )


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=TaskResponse,
    summary="Cancel a task",
    description="Cancel a PENDING task. Safe cancellation only.",
)
def cancel_task(
    task_id: str,
    engine: ExecutionEngine = Depends(get_engine),
) -> TaskResponse:
    """Cancel a pending task."""
    try:
        validated_id = validate_uuid(task_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    try:
        result = engine.cancel_task(validated_id)
    except TaskNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except TaskNotExecutableError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    # Return the cancelled task
    with next(get_db()) as db:
        task = db.execute(
            select(Task).where(Task.id == validated_id)
        ).scalar_one()
        return _task_to_response(task)


@router.get(
    "/tasks/{task_id}/result",
    response_model=TaskResultResponse,
    summary="Get task execution result",
    description="Retrieve the output of a completed or failed task execution.",
)
def get_task_result(
    task_id: str,
    db: Session = Depends(get_db),
) -> TaskResultResponse:
    """Get the execution result of a task."""
    try:
        validated_id = validate_uuid(task_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    task = db.execute(
        select(Task).where(Task.id == validated_id)
    ).scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    return TaskResultResponse(
        id=task.id,
        name=task.name,
        status=TaskStatus(task.status),
        output_payload=task.output_payload,
        error_message=task.error_message,
        started_at=task.started_at,
        completed_at=task.completed_at,
    )