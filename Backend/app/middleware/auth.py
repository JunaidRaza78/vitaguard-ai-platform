"""
Authentication Middleware
Verifies JWT tokens and protects routes
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Callable
from uuid import UUID
import logging

from app.auth.jwt import jwt_service
from shared.database import postgres_client, redis_client

logger = logging.getLogger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer()


class AuthMiddleware:
    """Authentication middleware for FastAPI"""

    @staticmethod
    async def _get_user_from_db(user_id: UUID) -> dict:
        """
        Get user from database.

        Args:
            user_id: User ID

        Returns:
            User data dictionary

        Raises:
            HTTPException: If user not found
        """
        user = await postgres_client.fetchrow(
            "SELECT * FROM users WHERE user_id = $1",
            user_id
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return dict(user)

    @staticmethod
    def require_auth(func: Callable) -> Callable:
        """
        Decorator to require authentication for an endpoint.

        Usage:
            @app.get("/protected")
            @AuthMiddleware.require_auth
            async def protected_route(request: Request):
                user = request.state.user
                return {"user": user}
        """
        async def wrapper(request: Request, *args, **kwargs):
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid Authorization header",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            token = auth_header.split(" ")[1]

            # Verify token
            payload = jwt_service.verify_access_token(token)

            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Get user
            user_id = UUID(payload.get("sub"))
            user = await AuthMiddleware._get_user_from_db(user_id)

            # Store user in request state
            request.state.user = user
            request.state.user_id = user_id

            return await func(request, *args, **kwargs)

        return wrapper


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Get current authenticated user from JWT token.

    This is a FastAPI dependency function suitable for use with Depends().
    """
    token = credentials.credentials

    # Verify token
    payload = jwt_service.verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = UUID(payload.get("sub"))

    # Check if session exists in Redis (fast)
    session_data = await redis_client.get_json(f"session:{user_id}")

    if session_data and session_data.get("access_token") == token:
        # Valid cached session
        user = await AuthMiddleware._get_user_from_db(user_id)
        return user

    # Session not in cache, verify in database
    session = await postgres_client.fetchrow(
        """
        SELECT * FROM sessions
        WHERE user_id = $1 AND access_token = $2 AND is_active = TRUE
        """,
        user_id,
        token,
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if session has expired
    from datetime import datetime

    if session["expires_at"] < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = await AuthMiddleware._get_user_from_db(user_id)

    # Update session cache
    await redis_client.set_json(
        f"session:{user_id}",
        {
            "session_id": str(session["session_id"]),
            "access_token": token,
            "user_id": str(user_id),
        },
        ex=jwt_service.access_token_expire_minutes * 60,
    )

    return user


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get current active user.
    """
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return current_user


async def get_current_verified_user(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    """
    Get current verified user.
    """
    if not current_user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email.",
        )

    return current_user


async def get_current_superuser(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    """
    Get current superuser.
    """
    if not current_user.get("is_superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Superuser access required.",
        )

    return current_user
