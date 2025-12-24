import asyncio

import pytest

from secbrain.core.context import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_basic():
    """Test basic token acquisition."""
    limiter = RateLimiter(tokens=5.0, max_tokens=10.0, refill_rate=2.0)

    # Should succeed immediately
    await limiter.acquire(3.0)
    assert limiter.tokens == pytest.approx(2.0, abs=0.1)

    # Should succeed after brief wait
    await limiter.acquire(3.0)
    assert limiter.tokens < 2.0


@pytest.mark.asyncio
async def test_rate_limiter_concurrency():
    """Test rate limiter under concurrent load."""
    limiter = RateLimiter(tokens=10.0, max_tokens=10.0, refill_rate=5.0)

    async def acquire_tokens():
        await limiter.acquire(1.0)
        return True

    # Run 20 concurrent acquisitions
    results = await asyncio.gather(*[acquire_tokens() for _ in range(20)])
    assert all(results)


@pytest.mark.asyncio
async def test_rate_limiter_initialization():
    """Test rate limiter initializes properly without event loop."""
    # Should not raise even without running loop
    limiter = RateLimiter(tokens=5.0, max_tokens=10.0, refill_rate=2.0)
    assert limiter.last_refill == 0.0

    # Should work correctly once loop starts
    await limiter.acquire(1.0)
    assert limiter.last_refill > 0.0
