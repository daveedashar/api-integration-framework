"""
Tests for HTTP client with retry and circuit breaker.
"""

import pytest
from src.services.http_client import (
    IntegrationHttpClient,
    CircuitBreaker,
    CircuitState,
    RateLimiter,
)


class TestCircuitBreaker:
    
    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True
    
    def test_record_success_resets(self):
        cb = CircuitBreaker()
        cb.failure_count = 3
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED
    
    def test_opens_after_threshold(self):
        cb = CircuitBreaker()
        for _ in range(5):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False


class TestRateLimiter:
    
    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        limiter = RateLimiter(rate=10, window=60)
        assert await limiter.acquire() is True
    
    @pytest.mark.asyncio
    async def test_acquire_exhausts_tokens(self):
        limiter = RateLimiter(rate=2, window=60)
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True
        assert await limiter.acquire() is False
