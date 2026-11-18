"""Task status enumeration."""
from enum import Enum


class TaskStatus(str, Enum):
    """Possible states for a task."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"