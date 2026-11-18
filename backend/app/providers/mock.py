"""MockProvider: deterministic provider for testing and development.

This provider never requires an external API key or a local LLM.
It simulates execution with predictable results so the agent engine
can be built and tested without GPU dependencies.
"""
from __future__ import annotations

import time
from typing import Any, Optional

from app.providers.provider import (
    BaseProvider,
    ProviderError,
    ProviderExecutionError,
    ProviderResult,
    ProviderTimeoutError,
)


class MockProvider(BaseProvider):
    """Deterministic provider used for development and testing."""

    name = "mock"

    def __init__(
        self,
        delay_seconds: float = 0.0,
        fail: bool = False,
        timeout: bool = False,
        failure_message: str = "MockProvider simulated failure",
    ) -> None:
        self.delay_seconds = delay_seconds
        self.fail = fail
        self.timeout = timeout
        self.failure_message = failure_message
        self.call_count = 0
        self.last_input: Optional[dict[str, Any]] = None

    def execute(self, task_input: dict[str, Any]) -> ProviderResult:
        """Execute a task using deterministic mock logic.

        Behaviour:
        - If `timeout` is True, raises ProviderTimeoutError.
        - If `fail` is True, returns a failed ProviderResult.
        - Otherwise returns a successful ProviderResult with predictable output.
        """
        start = time.monotonic()
        self.call_count += 1
        self.last_input = task_input

        if self.timeout:
            raise ProviderTimeoutError(
                "MockProvider timed out while executing task"
            )

        if self.delay_seconds > 0:
            time.sleep(self.delay_seconds)

        if self.fail:
            duration_ms = (time.monotonic() - start) * 1000.0
            return ProviderResult(
                success=False,
                error=self.failure_message,
                duration_ms=duration_ms,
            )

        duration_ms = (time.monotonic() - start) * 1000.0
        output = self._build_output(task_input)
        return ProviderResult(
            success=True,
            output=output,
            duration_ms=duration_ms,
        )

    def _build_output(self, task_input: dict[str, Any]) -> dict[str, Any]:
        """Build a deterministic output for a given input."""
        return {
            "provider": self.name,
            "echo": task_input,
            "summary": "Mock execution completed successfully",
            "input_keys": sorted(task_input.keys()) if isinstance(task_input, dict) else [],
            "completed": True,
        }

    def reset(self) -> None:
        """Reset call counters and last input."""
        self.call_count = 0
        self.last_input = None