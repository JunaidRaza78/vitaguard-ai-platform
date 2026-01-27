"""
Rate Limiting Middleware
Prevents abuse by limiting requests per IP/user
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Callable
import time
import logging

from shared.database import redis_client

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm with Redis.
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            requests_per_minute: Max requests per minute
            requests_per_hour: Max requests per hour
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and apply rate limiting.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        # Get client identifier (IP address or user ID if authenticated)
        client_id = self._get_client_id(request)

        # Check rate limits
        try:
            is_allowed = await self._check_rate_limit(client_id, request.url.path)

            if not is_allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "retry_after": 60
                    },
                    headers={"Retry-After": "60"}
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            remaining = await self._get_remaining_requests(client_id)
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)

            return response

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # On error, allow request to proceed
            return await call_next(request)

    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier for rate limiting.

        Args:
            request: HTTP request

        Returns:
            Client ID (IP address or user ID)
        """
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    async def _check_rate_limit(self, client_id: str, endpoint: str) -> bool:
        """
        Check if client has exceeded rate limit.

        Args:
            client_id: Client identifier
            endpoint: API endpoint

        Returns:
            True if allowed, False if rate limit exceeded
        """
        current_time = int(time.time())

        # Minute window key
        minute_key = f"rate_limit:minute:{client_id}:{current_time // 60}"

        # Hour window key
        hour_key = f"rate_limit:hour:{client_id}:{current_time // 3600}"

        # Check minute limit
        minute_count = await redis_client.get(minute_key)
        if minute_count and int(minute_count) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded (minute): {client_id}")
            return False

        # Check hour limit
        hour_count = await redis_client.get(hour_key)
        if hour_count and int(hour_count) >= self.requests_per_hour:
            logger.warning(f"Rate limit exceeded (hour): {client_id}")
            return False

        # Increment counters
        pipe = redis_client._redis.pipeline()

        # Minute counter
        await redis_client._redis.incr(minute_key)
        await redis_client._redis.expire(minute_key, 60)

        # Hour counter
        await redis_client._redis.incr(hour_key)
        await redis_client._redis.expire(hour_key, 3600)

        return True

    async def _get_remaining_requests(self, client_id: str) -> int:
        """
        Get remaining requests in current minute window.

        Args:
            client_id: Client identifier

        Returns:
            Number of remaining requests
        """
        current_time = int(time.time())
        minute_key = f"rate_limit:minute:{client_id}:{current_time // 60}"

        count = await redis_client.get(minute_key)
        used = int(count) if count else 0

        return max(0, self.requests_per_minute - used)


class EndpointRateLimiter:
    """
    Decorator for endpoint-specific rate limiting.
    """

    def __init__(
        self,
        requests: int = 10,
        window_seconds: int = 60,
        key_func: Optional[Callable] = None
    ):
        """
        Initialize endpoint rate limiter.

        Args:
            requests: Max requests in window
            window_seconds: Time window in seconds
            key_func: Custom function to generate rate limit key
        """
        self.requests = requests
        self.window_seconds = window_seconds
        self.key_func = key_func

    async def __call__(self, request: Request):
        """
        Apply rate limit to endpoint.

        Args:
            request: HTTP request

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Skip rate limiting if Redis is not available
        if redis_client is None:
            return  # No rate limiting without Redis

        # Generate key
        if self.key_func:
            key = self.key_func(request)
        else:
            client_ip = request.client.host if request.client else "unknown"
            key = f"endpoint_limit:{request.url.path}:{client_ip}"

        current_time = int(time.time())
        window_key = f"{key}:{current_time // self.window_seconds}"

        # Check current count
        count = await redis_client.get(window_key)

        if count and int(count) >= self.requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Max {self.requests} requests per {self.window_seconds} seconds.",
                headers={"Retry-After": str(self.window_seconds)}
            )

        # Increment counter
        await redis_client._redis.incr(window_key)
        await redis_client._redis.expire(window_key, self.window_seconds)


# Pre-configured rate limiters for common use cases
class RateLimiters:
    """Pre-configured rate limiters"""

    # Strict rate limit for authentication endpoints
    auth_limiter = EndpointRateLimiter(
        requests=5,  # 5 requests
        window_seconds=300  # per 5 minutes
    )

    # Moderate rate limit for API endpoints
    api_limiter = EndpointRateLimiter(
        requests=100,  # 100 requests
        window_seconds=60  # per minute
    )

    # Lenient rate limit for read operations
    read_limiter = EndpointRateLimiter(
        requests=300,  # 300 requests
        window_seconds=60  # per minute
    )


# Helper function to get client IP
def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request.

    Args:
        request: HTTP request

    Returns:
        Client IP address
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.client.host if request.client else "unknown"
