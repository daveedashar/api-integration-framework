"""
HTTP client with retry, circuit breaker, and rate limiting.
"""

import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import httpx
from datetime import datetime, timedelta

from src.core.config import settings


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker for API calls."""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: CircuitState = CircuitState.CLOSED
    
    def record_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= settings.circuit_breaker_threshold:
            self.state = CircuitState.OPEN
    
    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                timeout = timedelta(seconds=settings.circuit_breaker_timeout)
                if datetime.utcnow() - self.last_failure_time > timeout:
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False
        
        return True  # HALF_OPEN


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, rate: int, window: int):
        self.rate = rate
        self.window = window
        self.tokens = rate
        self.last_update = datetime.utcnow()
    
    async def acquire(self) -> bool:
        now = datetime.utcnow()
        elapsed = (now - self.last_update).total_seconds()
        
        self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.window))
        self.last_update = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class IntegrationHttpClient:
    """HTTP client with retry, circuit breaker, and rate limiting."""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
    
    def _get_circuit_breaker(self, connector_id: str) -> CircuitBreaker:
        if connector_id not in self.circuit_breakers:
            self.circuit_breakers[connector_id] = CircuitBreaker()
        return self.circuit_breakers[connector_id]
    
    def _get_rate_limiter(self, connector_id: str, rate: int = None) -> RateLimiter:
        if connector_id not in self.rate_limiters:
            self.rate_limiters[connector_id] = RateLimiter(
                rate or settings.default_rate_limit,
                settings.rate_limit_window
            )
        return self.rate_limiters[connector_id]
    
    async def request(
        self,
        connector_id: str,
        method: str,
        url: str,
        headers: Dict[str, str] = None,
        data: Any = None,
        json: Any = None,
        timeout: int = 30,
        retries: int = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with retry, circuit breaker, and rate limiting.
        """
        circuit_breaker = self._get_circuit_breaker(connector_id)
        rate_limiter = self._get_rate_limiter(connector_id)
        
        if not circuit_breaker.can_execute():
            raise Exception(f"Circuit breaker open for connector {connector_id}")
        
        if not await rate_limiter.acquire():
            raise Exception(f"Rate limit exceeded for connector {connector_id}")
        
        max_retries = retries or settings.default_max_retries
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        data=data,
                        json=json,
                        timeout=timeout,
                    )
                    response.raise_for_status()
                    
                    circuit_breaker.record_success()
                    
                    return {
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "body": response.json() if response.content else None,
                    }
            
            except Exception as e:
                last_exception = e
                circuit_breaker.record_failure()
                
                if attempt < max_retries:
                    delay = settings.default_retry_delay
                    if settings.exponential_backoff:
                        delay = delay * (2 ** attempt)
                    await asyncio.sleep(delay)
        
        raise last_exception


http_client = IntegrationHttpClient()
