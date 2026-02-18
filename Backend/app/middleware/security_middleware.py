"""
Security Middleware
Audit trail logging, request sanitization, and rate limiting helpers.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


class AuditLogger:
    """Logs API requests for audit trail compliance (HIPAA/GDPR)."""

    def __init__(self):
        self.log_file = "audit_trail.log"
        self._audit_logger = logging.getLogger("audit")
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(message)s"
        ))
        self._audit_logger.addHandler(handler)
        self._audit_logger.setLevel(logging.INFO)

    def log(
        self,
        user_id: str,
        action: str,
        resource: str,
        method: str,
        ip_address: str,
        status_code: int,
        duration_ms: float,
        details: Optional[str] = None,
    ):
        """Write an audit log entry."""
        entry = (
            f"user={user_id} | action={action} | resource={resource} | "
            f"method={method} | ip={ip_address} | status={status_code} | "
            f"duration={duration_ms:.0f}ms"
        )
        if details:
            entry += f" | details={details}"
        self._audit_logger.info(entry)


class RateLimiter:
    """Simple in-memory rate limiter (per-user, per-minute)."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed under the rate limit."""
        now = time.time()
        window_start = now - self.window

        # Clean old entries
        self._requests[key] = [t for t in self._requests[key] if t > window_start]

        if len(self._requests[key]) >= self.max_requests:
            return False

        self._requests[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        """Get remaining requests in window."""
        now = time.time()
        window_start = now - self.window
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        return max(0, self.max_requests - len(self._requests[key]))


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging, rate limiting, and security headers."""

    def __init__(self, app, enable_audit: bool = True, enable_rate_limit: bool = True):
        super().__init__(app)
        self.audit = AuditLogger() if enable_audit else None
        self.rate_limiter = RateLimiter() if enable_rate_limit else None

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()
        request_id = str(uuid.uuid4())[:8]

        # Rate limiting
        client_ip = request.client.host if request.client else "unknown"
        if self.rate_limiter:
            if not self.rate_limiter.is_allowed(client_ip):
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please try again later."},
                )

        # Process request
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Security headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

        # Audit logging
        if self.audit:
            # Extract user_id from state if available
            user_id = getattr(request.state, "user_id", "anonymous")
            path = request.url.path
            method = request.method

            # Skip health check endpoints
            if path not in ["/health", "/docs", "/openapi.json", "/favicon.ico"]:
                self.audit.log(
                    user_id=user_id,
                    action=f"{method}:{path}",
                    resource=path,
                    method=method,
                    ip_address=client_ip,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )

        return response


# Instances
audit_logger = AuditLogger()
rate_limiter = RateLimiter()
