"""
Async circuit breaker implementation.

States:
  CLOSED     — Normal operation. Failures are counted.
  OPEN       — Service considered unavailable. Calls fail immediately.
  HALF_OPEN  — Probe phase. One call is allowed through to test recovery.

Usage:
    cb = CircuitBreaker(name="qdrant", failure_threshold=5, recovery_timeout=30)

    @cb.protect
    async def my_call():
        ...

    # Or as context manager:
    async with cb:
        result = await some_service.call()
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Optional, Type

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED    = "CLOSED"
    OPEN      = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpenError(Exception):
    """Raised when a call is rejected because the circuit is OPEN."""
    def __init__(self, name: str, retry_after: float):
        self.retry_after = retry_after
        super().__init__(
            f"Circuit '{name}' is OPEN. Retry after {retry_after:.1f}s."
        )


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
        expected_exceptions: tuple[Type[Exception], ...] = (Exception,),
    ):
        self.name               = name
        self.failure_threshold  = failure_threshold
        self.recovery_timeout   = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.expected_exceptions = expected_exceptions

        self._state         : CircuitState = CircuitState.CLOSED
        self._failure_count : int          = 0
        self._last_failure  : float        = 0.0
        self._half_open_calls: int         = 0
        self._lock          : asyncio.Lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    def _should_attempt_reset(self) -> bool:
        return (time.monotonic() - self._last_failure) >= self.recovery_timeout

    async def _transition(self, new_state: CircuitState) -> None:
        old_state = self._state
        self._state = new_state
        if old_state != new_state:
            logger.info(
                f"CircuitBreaker[{self.name}]: {old_state.value} → {new_state.value}"
            )

    async def __aenter__(self):
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    await self._transition(CircuitState.HALF_OPEN)
                    self._half_open_calls = 0
                else:
                    retry_after = self.recovery_timeout - (
                        time.monotonic() - self._last_failure
                    )
                    raise CircuitBreakerOpenError(self.name, retry_after)

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpenError(self.name, 0.0)
                self._half_open_calls += 1

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        async with self._lock:
            if exc_type and issubclass(exc_type, self.expected_exceptions):
                # Failure
                self._failure_count += 1
                self._last_failure   = time.monotonic()
                if self._state == CircuitState.HALF_OPEN:
                    await self._transition(CircuitState.OPEN)
                elif self._failure_count >= self.failure_threshold:
                    await self._transition(CircuitState.OPEN)
                logger.warning(
                    f"CircuitBreaker[{self.name}]: failure {self._failure_count}/{self.failure_threshold}"
                )
                return False  # re-raise exception
            else:
                # Success
                if self._state == CircuitState.HALF_OPEN:
                    await self._transition(CircuitState.CLOSED)
                self._failure_count = 0
                return False

    def protect(self, func: Callable):
        """Decorator shorthand."""
        async def wrapper(*args, **kwargs):
            async with self:
                return await func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper

    def reset(self):
        """Manually reset circuit (for testing / ops override)."""
        self._state          = CircuitState.CLOSED
        self._failure_count  = 0
        self._half_open_calls = 0


# ── Pre-built breakers for each external dependency ────────────
qdrant_breaker  = CircuitBreaker(name="qdrant",  failure_threshold=5, recovery_timeout=30)
kafka_breaker   = CircuitBreaker(name="kafka",   failure_threshold=5, recovery_timeout=20)
redis_breaker   = CircuitBreaker(name="redis",   failure_threshold=3, recovery_timeout=15)
email_breaker   = CircuitBreaker(name="email",   failure_threshold=3, recovery_timeout=60)
