"""
Async retry decorator with exponential backoff and jitter.

Usage:
    @async_retry(max_attempts=3, base_delay=0.5, max_delay=10.0,
                 exceptions=(aiosmtplib.SMTPException,))
    async def send_email(...):
        ...

    # Or with custom on_retry callback:
    result = await retry_with_backoff(my_coro(), max_attempts=3)
"""

import asyncio
import logging
import random
from functools import wraps
from typing import Callable, Optional, Tuple, Type

logger = logging.getLogger(__name__)


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """
    Decorator: retry an async function with exponential backoff.

    Args:
        max_attempts: Total attempts (including first try).
        base_delay:   Initial sleep in seconds (doubles each attempt).
        max_delay:    Cap on sleep duration.
        jitter:       Add ±25% random jitter to avoid thundering herd.
        exceptions:   Exception types that trigger a retry.
        on_retry:     Optional async callback(attempt, exc) called before sleep.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc: Optional[Exception] = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        logger.error(
                            f"[retry] {func.__name__} exhausted {max_attempts} attempts: {exc}"
                        )
                        raise

                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    if jitter:
                        delay *= (0.75 + random.random() * 0.5)  # ±25%

                    logger.warning(
                        f"[retry] {func.__name__} attempt {attempt}/{max_attempts} "
                        f"failed: {exc}. Retrying in {delay:.2f}s"
                    )

                    if on_retry:
                        try:
                            await on_retry(attempt, exc)
                        except Exception:
                            pass

                    await asyncio.sleep(delay)

            raise last_exc  # unreachable but satisfies type checkers

        return wrapper
    return decorator


async def retry_with_backoff(
    coro_factory: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> any:
    """
    Imperative retry helper for coroutines that can't be wrapped as decorators.
    coro_factory must be a zero-arg callable returning a coroutine.
    """
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await coro_factory()
        except exceptions as exc:
            last_exc = exc
            if attempt == max_attempts:
                raise
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.warning(f"[retry] attempt {attempt}/{max_attempts}: {exc}. Sleeping {delay:.2f}s")
            await asyncio.sleep(delay)
    raise last_exc
