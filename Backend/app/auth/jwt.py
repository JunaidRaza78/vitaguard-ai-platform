"""
JWT Token Service
Handles JWT token creation, validation, and refresh
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
import os
import logging

logger = logging.getLogger(__name__)


class JWTService:
    """Service for JWT token operations"""

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 30
    ):
        """
        Initialize JWT service.

        Args:
            secret_key: Secret key for signing tokens
            algorithm: JWT algorithm (default: HS256)
            access_token_expire_minutes: Access token expiration in minutes
            refresh_token_expire_days: Refresh token expiration in days
        """
        self.secret_key = secret_key or os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_minutes = refresh_token_expire_days * 24 * 60

        if self.secret_key == "your-secret-key-change-in-production":
            logger.warning(
                "Using default SECRET_KEY! This is insecure. "
                "Set SECRET_KEY environment variable in production."
            )

    def create_access_token(
        self,
        user_id: UUID,
        email: str,
        username: str,
        is_superuser: bool = False,
        extra_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User ID
            email: User email
            username: Username
            is_superuser: Is user a superuser
            extra_claims: Additional claims to include

        Returns:
            JWT access token
        """
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "email": email,
            "username": username,
            "is_superuser": is_superuser,
            "type": "access",
            "iat": now,  # Issued at
            "exp": expires,  # Expiration
            "nbf": now,  # Not before
        }

        if extra_claims:
            payload.update(extra_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def create_refresh_token(
        self,
        user_id: UUID,
        remember_me: bool = False
    ) -> str:
        """
        Create JWT refresh token.

        Args:
            user_id: User ID
            remember_me: Extended expiration if True

        Returns:
            JWT refresh token
        """
        now = datetime.utcnow()

        # Extended expiration for "remember me"
        if remember_me:
            expires = now + timedelta(days=90)  # 90 days
        else:
            expires = now + timedelta(minutes=self.refresh_token_expire_minutes)

        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": expires,
            "nbf": now,
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token to decode

        Returns:
            Token payload

        Raises:
            InvalidTokenError: If token is invalid
            ExpiredSignatureError: If token is expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except ExpiredSignatureError:
            logger.warning("Token has expired")
            raise
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise

    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify access token and return payload.

        Args:
            token: JWT access token

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = self.decode_token(token)

            # Verify token type
            if payload.get("type") != "access":
                logger.warning("Token is not an access token")
                return None

            return payload

        except (InvalidTokenError, ExpiredSignatureError):
            return None

    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify refresh token and return payload.

        Args:
            token: JWT refresh token

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = self.decode_token(token)

            # Verify token type
            if payload.get("type") != "refresh":
                logger.warning("Token is not a refresh token")
                return None

            return payload

        except (InvalidTokenError, ExpiredSignatureError):
            return None

    def get_token_expiration(self, token: str) -> Optional[datetime]:
        """
        Get token expiration time.

        Args:
            token: JWT token

        Returns:
            Expiration datetime or None
        """
        try:
            payload = self.decode_token(token)
            exp_timestamp = payload.get("exp")

            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)

            return None

        except (InvalidTokenError, ExpiredSignatureError):
            return None

    def get_user_id_from_token(self, token: str) -> Optional[UUID]:
        """
        Extract user ID from token.

        Args:
            token: JWT token

        Returns:
            User ID or None
        """
        payload = self.verify_access_token(token)

        if payload:
            try:
                return UUID(payload.get("sub"))
            except (ValueError, TypeError):
                return None

        return None

    def create_email_verification_token(self, user_id: UUID, email: str) -> str:
        """
        Create email verification token.

        Args:
            user_id: User ID
            email: Email to verify

        Returns:
            JWT verification token
        """
        now = datetime.utcnow()
        expires = now + timedelta(hours=24)  # 24 hours

        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "email_verification",
            "iat": now,
            "exp": expires,
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_email_verification_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify email verification token.

        Args:
            token: Email verification token

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = self.decode_token(token)

            if payload.get("type") != "email_verification":
                return None

            return payload

        except (InvalidTokenError, ExpiredSignatureError):
            return None

    def create_password_reset_token(self, user_id: UUID, email: str) -> str:
        """
        Create password reset token.

        Args:
            user_id: User ID
            email: User email

        Returns:
            JWT reset token
        """
        now = datetime.utcnow()
        expires = now + timedelta(hours=1)  # 1 hour

        payload = {
            "sub": str(user_id),
            "email": email,
            "type": "password_reset",
            "iat": now,
            "exp": expires,
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_password_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify password reset token.

        Args:
            token: Password reset token

        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = self.decode_token(token)

            if payload.get("type") != "password_reset":
                return None

            return payload

        except (InvalidTokenError, ExpiredSignatureError):
            return None


# Create global instance
jwt_service = JWTService(
    access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
)
