"""Provider abstraction for AI/LLM execution.

This module defines the interface that all providers (MockProvider,
OllamaProvider, etc.) must implement. It is intentionally lightweight
so it can run on resource-constrained hardware.
"""
from __future__ import annotations

import abc
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional


class ProviderError(Exception):
    """Base error raised by providers."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider operation times out."""


class ProviderExecutionError(ProviderError):
    """Raised when a provider fails to execute a task."""


class ProviderResult:
    """Structured result returned by a provider."""

    def __init__(
        self,
        success: bool,
        output: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> None:
        self.success = success
        self.output = output
        self.error = error
        self.duration_ms = duration_ms

    def __repr__(self) -> str:
        return (
            f"ProviderResult(success={self.success!r}, "
            f"error={self.error!r}, duration_ms={self.duration_ms!r})"
        )


class BaseProvider(abc.ABC):
    """Abstract base class for all task execution providers."""

    name: str = "base"

    @abc.abstractmethod
    def execute(self, task_input: dict[str, Any]) -> ProviderResult:
        """Execute a task and return a ProviderResult.

        Subclasses must implement this method.
        """
        raise NotImplementedError

    def health(self) -> bool:
        """Return True if the provider is ready to accept tasks."""
        return True


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _simulate_delay(seconds: float) -> None:
    """Sleep for the given number of seconds (used for delay simulation)."""
    if seconds > 0:
        time.sleep(seconds)