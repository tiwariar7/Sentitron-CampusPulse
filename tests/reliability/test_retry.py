import asyncio
import pytest
from utils.retry import async_retry, retry_with_backoff


@pytest.mark.asyncio
async def test_async_retry_decorator():
    call_count = 0

    @async_retry(max_attempts=3, base_delay=0.01, jitter=False)
    async def flappy_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("transient failure")
        return "success"

    res = await flappy_function()
    assert res == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_async_retry_exhausted():
    call_count = 0

    @async_retry(max_attempts=2, base_delay=0.01, jitter=False, exceptions=(ValueError,))
    async def failing_function():
        nonlocal call_count
        call_count += 1
        raise ValueError("permanent failure")

    with pytest.raises(ValueError, match="permanent failure"):
        await failing_function()
    assert call_count == 2
