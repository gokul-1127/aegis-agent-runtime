"""Unit tests for MockProvider."""
from __future__ import annotations

from app.providers.mock import MockProvider
from app.providers.provider import ProviderTimeoutError


def test_mock_provider_success():
    """MockProvider should return successful result by default."""
    provider = MockProvider()
    result = provider.execute({"input": "test"})

    assert result.success is True
    assert result.error is None
    assert result.output is not None
    assert result.output["provider"] == "mock"
    assert result.output["completed"] is True
    assert result.duration_ms >= 0


def test_mock_provider_failure():
    """MockProvider should return failed result when fail=True."""
    provider = MockProvider(fail=True, failure_message="Custom error")
    result = provider.execute({"input": "test"})

    assert result.success is False
    assert result.error == "Custom error"
    assert result.output is None
    assert result.duration_ms >= 0


def test_mock_provider_timeout():
    """MockProvider should raise ProviderTimeoutError when timeout=True."""
    provider = MockProvider(timeout=True)

    try:
        provider.execute({"input": "test"})
        assert False, "Should have raised ProviderTimeoutError"
    except ProviderTimeoutError:
        pass


def test_mock_provider_delay():
    """MockProvider should delay execution when delay_seconds > 0."""
    import time

    provider = MockProvider(delay_seconds=0.1)
    start = time.monotonic()
    result = provider.execute({"input": "test"})
    elapsed = time.monotonic() - start

    assert result.success is True
    assert elapsed >= 0.09  # Allow some tolerance


def test_mock_provider_deterministic_output():
    """MockProvider should return deterministic output for same input."""
    provider = MockProvider()
    input_data = {"key": "value", "number": 42}

    result1 = provider.execute(input_data)
    result2 = provider.execute(input_data)

    assert result1.output == result2.output
    assert result1.output["echo"] == input_data


def test_mock_provider_call_tracking():
    """MockProvider should track call count and last input."""
    provider = MockProvider()
    provider.execute({"a": 1})
    provider.execute({"b": 2})

    assert provider.call_count == 2
    assert provider.last_input == {"b": 2}


def test_mock_provider_reset():
    """MockProvider reset should clear call count and last input."""
    provider = MockProvider()
    provider.execute({"a": 1})
    provider.reset()

    assert provider.call_count == 0
    assert provider.last_input is None