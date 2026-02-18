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
import shared.database as db_module

logger = logging.getLogger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer()


class AuthMiddleware:
    """Authentication middleware for FastAPI"""

    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """
        Get current authenticated user from JWT token.

        Args:
            credentials: HTTP Bearer credentials

        Returns:
            User data dictionary

        Raises:
            HTTPException: If token is invalid or user not found
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
        session_data = None
        if db_module.redis_client:
            try:
                session_data = db_module.redis_client.cache_get(f"session:{user_id}")
            except Exception as e:
                logger.warning(f"Redis session lookup failed: {e}")

        if session_data and session_data.get("access_token") == token:
            # Valid cached session
            user = await AuthMiddleware._get_user_from_db(user_id)
            return user

        # Session not in Redis cache, get user directly from DB
        user = await AuthMiddleware._get_user_from_db(user_id)

        # Cache session in Redis for future requests
        if db_module.redis_client:
            try:
                db_module.redis_client.cache_set(
                    f"session:{user_id}",
                    {
                        "access_token": token,
                        "user_id": str(user_id)
                    },
                    ttl=jwt_service.access_token_expire_minutes * 60
                )
            except Exception as e:
                logger.warning(f"Redis session cache failed: {e}")

        return user

    @staticmethod
    async def get_current_active_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """
        Get current active user.

        Args:
            credentials: HTTP Bearer credentials

        Returns:
            User data dictionary

        Raises:
            HTTPException: If user is inactive
        """
        current_user = await AuthMiddleware.get_current_user(credentials)
        if not current_user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user account"
            )

        return current_user

    @staticmethod
    async def get_current_verified_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """
        Get current verified user.

        Args:
            credentials: Current active user

        Returns:
            User data dictionary

        Raises:
            HTTPException: If user is not verified
        """
        current_user = await AuthMiddleware.get_current_active_user(credentials)
        if not current_user.get("is_verified"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please verify your email."
            )

        return current_user

    @staticmethod
    async def get_current_superuser(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """
        Get current superuser.

        Args:
            current_user: Current active user

        Returns:
            User data dictionary

        Raises:
            HTTPException: If user is not a superuser
        """
        current_user = await AuthMiddleware.get_current_active_user(credentials)
        if not current_user.get("is_superuser"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions. Superuser access required."
            )

        return current_user

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
        from shared.database.postgres.postgres_client import PostgresClient
        with PostgresClient() as client:
            user = client.get_user_by_id(str(user_id))
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            # Extract data while session is still open
            user_data = {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
                "date_of_birth": user.date_of_birth,
                "gender": user.gender,
                "avatar_url": user.avatar_url,
                "timezone": user.timezone,
                "language": user.language,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "is_superuser": user.is_superuser,
                "created_at": str(user.created_at),
                "updated_at": str(user.updated_at),
                "last_login": str(user.last_login) if user.last_login else None,
            }
        return user_data

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


# Export commonly used dependencies
get_current_user = AuthMiddleware.get_current_user
get_current_active_user = AuthMiddleware.get_current_active_user
get_current_verified_user = AuthMiddleware.get_current_verified_user
get_current_superuser = AuthMiddleware.get_current_superuser
