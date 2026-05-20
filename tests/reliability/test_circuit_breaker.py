import asyncio
import time
import pytest
from utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitState


@pytest.mark.asyncio
async def test_circuit_breaker_flow():
    # 1. Initialize circuit breaker
    cb = CircuitBreaker(name="test_cb", failure_threshold=2, recovery_timeout=0.2)
    assert cb.state == CircuitState.CLOSED

    # 2. Closed state executes successfully
    @cb.protect
    async def success_call():
        return "ok"

    res = await success_call()
    assert res == "ok"
    assert cb.state == CircuitState.CLOSED

    # 3. Failing calls trip the breaker
    @cb.protect
    async def fail_call():
        raise ValueError("simulated error")

    with pytest.raises(ValueError, match="simulated error"):
        await fail_call()
    assert cb.state == CircuitState.CLOSED  # First failure

    with pytest.raises(ValueError, match="simulated error"):
        await fail_call()
    assert cb.state == CircuitState.OPEN  # Second failure -> Trips

    # 4. Calls in OPEN state are rejected immediately
    with pytest.raises(CircuitBreakerOpenError):
        await success_call()

    # 5. Cooldown period passes -> transitions to HALF_OPEN on next call
    await asyncio.sleep(0.25)

    # 6. Successful call in HALF_OPEN resets to CLOSED
    res = await success_call()
    assert res == "ok"
    assert cb.state == CircuitState.CLOSED
