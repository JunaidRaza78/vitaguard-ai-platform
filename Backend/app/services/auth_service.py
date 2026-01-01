"""
Authentication Service
Handles user registration, login, and authentication business logic
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
import logging

from app.models.user import User, RefreshToken, LoginAttempt, Session
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.auth.password import password_service
from app.auth.jwt import jwt_service
from shared.database import postgres_client, redis_client

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Service for user authentication operations"""

    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_MINUTES = 30

    async def register_user(
        self,
        user_data: UserRegister,
        ip_address: Optional[str] = None
    ) -> Tuple[User, str]:
        """
        Register a new user.

        Args:
            user_data: User registration data
            ip_address: User's IP address

        Returns:
            Tuple of (User, verification_token)

        Raises:
            ValueError: If user already exists
        """
        # Check if email already exists
        existing_user = await postgres_client.fetchrow(
            "SELECT user_id FROM users WHERE email = $1",
            user_data.email
        )

        if existing_user:
            raise ValueError("Email already registered")

        # Check if username already exists
        existing_username = await postgres_client.fetchrow(
            "SELECT user_id FROM users WHERE username = $1",
            user_data.username
        )

        if existing_username:
            raise ValueError("Username already taken")

        # Hash password
        password_hash = password_service.hash_password(user_data.password)

        # Create user
        user_id = uuid4()
        now = datetime.utcnow()

        user_record = await postgres_client.fetchrow(
            """
            INSERT INTO users (
                user_id, email, username, password_hash,
                first_name, last_name, phone_number, date_of_birth, gender,
                timezone, language, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING *
            """,
            user_id, user_data.email, user_data.username, password_hash,
            user_data.first_name, user_data.last_name, user_data.phone_number,
            user_data.date_of_birth, user_data.gender,
            user_data.timezone, user_data.language, now, now
        )

        user = User(**dict(user_record))

        # Generate email verification token
        verification_token = jwt_service.create_email_verification_token(
            user_id, user_data.email
        )

        # Store verification token in Redis (24 hours)
        await redis_client.set(
            f"email_verification:{user_id}",
            verification_token,
            ex=86400
        )

        logger.info(f"User registered: {user.email} from IP {ip_address}")

        # Create user node in Neo4j
        from shared.database import neo4j_client
        await neo4j_client.create_node(
            "User",
            {
                "userId": str(user_id),
                "email": user_data.email,
                "username": user_data.username,
                "createdAt": now.isoformat()
            }
        )

        return user, verification_token

    async def login_user(
        self,
        login_data: UserLogin,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[TokenResponse]:
        """
        Authenticate user and create session.

        Args:
            login_data: Login credentials
            ip_address: User's IP address
            user_agent: User's browser/device info

        Returns:
            TokenResponse if successful, None otherwise

        Raises:
            ValueError: If account is locked or credentials are invalid
        """
        # Get user from database
        user_record = await postgres_client.fetchrow(
            "SELECT * FROM users WHERE email = $1",
            login_data.email
        )

        # Track login attempt
        await self._record_login_attempt(
            login_data.email,
            ip_address,
            user_agent,
            success=False
        )

        if not user_record:
            raise ValueError("Invalid email or password")

        user = User(**dict(user_record))

        # Check if account is locked
        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            remaining = (user.account_locked_until - datetime.utcnow()).seconds // 60
            raise ValueError(f"Account is locked. Try again in {remaining} minutes.")

        # Check if account is active
        if not user.is_active:
            raise ValueError("Account is deactivated. Contact support.")

        # Verify password
        if not password_service.verify_password(login_data.password, user.password_hash):
            # Increment failed attempts
            failed_attempts = user.failed_login_attempts + 1

            if failed_attempts >= self.MAX_LOGIN_ATTEMPTS:
                # Lock account
                lockout_until = datetime.utcnow() + timedelta(minutes=self.ACCOUNT_LOCKOUT_MINUTES)
                await postgres_client.execute(
                    """
                    UPDATE users
                    SET failed_login_attempts = $1, account_locked_until = $2
                    WHERE user_id = $3
                    """,
                    failed_attempts, lockout_until, user.user_id
                )
                raise ValueError(
                    f"Too many failed attempts. Account locked for {self.ACCOUNT_LOCKOUT_MINUTES} minutes."
                )
            else:
                # Update failed attempts
                await postgres_client.execute(
                    "UPDATE users SET failed_login_attempts = $1 WHERE user_id = $2",
                    failed_attempts, user.user_id
                )
                remaining_attempts = self.MAX_LOGIN_ATTEMPTS - failed_attempts
                raise ValueError(
                    f"Invalid email or password. {remaining_attempts} attempts remaining."
                )

        # Reset failed attempts on successful login
        await postgres_client.execute(
            """
            UPDATE users
            SET failed_login_attempts = 0,
                account_locked_until = NULL,
                last_login = $1
            WHERE user_id = $2
            """,
            datetime.utcnow(), user.user_id
        )

        # Record successful login
        await self._record_login_attempt(
            login_data.email,
            ip_address,
            user_agent,
            success=True
        )

        # Create tokens
        access_token = jwt_service.create_access_token(
            user.user_id,
            user.email,
            user.username,
            user.is_superuser
        )

        refresh_token = jwt_service.create_refresh_token(
            user.user_id,
            remember_me=login_data.remember_me
        )

        # Store refresh token in database
        refresh_token_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(days=30 if not login_data.remember_me else 90)

        await postgres_client.execute(
            """
            INSERT INTO refresh_tokens (
                token_id, user_id, token, expires_at, device_info, ip_address
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            refresh_token_id, user.user_id, refresh_token, expires_at, user_agent, ip_address
        )

        # Create session
        session_id = await self._create_session(
            user.user_id,
            access_token,
            refresh_token,
            ip_address,
            user_agent
        )

        logger.info(f"User logged in: {user.email} from IP {ip_address}")

        # Create response
        user_response = UserResponse(**dict(user_record))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=jwt_service.access_token_expire_minutes * 60,
            user=user_response
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None
    ) -> Optional[TokenResponse]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token
            ip_address: User's IP address

        Returns:
            New TokenResponse or None if invalid

        Raises:
            ValueError: If refresh token is invalid or revoked
        """
        # Verify refresh token
        payload = jwt_service.verify_refresh_token(refresh_token)

        if not payload:
            raise ValueError("Invalid refresh token")

        user_id = UUID(payload.get("sub"))

        # Check if refresh token exists and is not revoked
        token_record = await postgres_client.fetchrow(
            """
            SELECT * FROM refresh_tokens
            WHERE user_id = $1 AND token = $2 AND revoked = FALSE
            """,
            user_id, refresh_token
        )

        if not token_record:
            raise ValueError("Refresh token not found or has been revoked")

        # Check if token has expired
        if token_record['expires_at'] < datetime.utcnow():
            raise ValueError("Refresh token has expired")

        # Get user
        user_record = await postgres_client.fetchrow(
            "SELECT * FROM users WHERE user_id = $1",
            user_id
        )

        if not user_record:
            raise ValueError("User not found")

        user = User(**dict(user_record))

        # Create new access token
        access_token = jwt_service.create_access_token(
            user.user_id,
            user.email,
            user.username,
            user.is_superuser
        )

        # Optionally rotate refresh token (recommended for security)
        new_refresh_token = jwt_service.create_refresh_token(user.user_id)

        # Revoke old refresh token
        await postgres_client.execute(
            "UPDATE refresh_tokens SET revoked = TRUE, revoked_at = $1 WHERE token_id = $2",
            datetime.utcnow(), token_record['token_id']
        )

        # Store new refresh token
        refresh_token_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(days=30)

        await postgres_client.execute(
            """
            INSERT INTO refresh_tokens (token_id, user_id, token, expires_at, ip_address)
            VALUES ($1, $2, $3, $4, $5)
            """,
            refresh_token_id, user_id, new_refresh_token, expires_at, ip_address
        )

        user_response = UserResponse(**dict(user_record))

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=jwt_service.access_token_expire_minutes * 60,
            user=user_response
        )

    async def logout_user(
        self,
        user_id: UUID,
        refresh_token: Optional[str] = None
    ) -> bool:
        """
        Logout user and revoke tokens.

        Args:
            user_id: User ID
            refresh_token: Refresh token to revoke

        Returns:
            True if successful
        """
        # Revoke refresh token
        if refresh_token:
            await postgres_client.execute(
                """
                UPDATE refresh_tokens
                SET revoked = TRUE, revoked_at = $1
                WHERE user_id = $2 AND token = $3
                """,
                datetime.utcnow(), user_id, refresh_token
            )

        # Deactivate sessions
        await postgres_client.execute(
            "UPDATE sessions SET is_active = FALSE WHERE user_id = $1",
            user_id
        )

        # Clear session cache from Redis
        await redis_client.delete(f"session:{user_id}")

        logger.info(f"User logged out: {user_id}")

        return True

    async def verify_email(self, token: str) -> bool:
        """
        Verify user email with token.

        Args:
            token: Email verification token

        Returns:
            True if successful

        Raises:
            ValueError: If token is invalid
        """
        payload = jwt_service.verify_email_verification_token(token)

        if not payload:
            raise ValueError("Invalid or expired verification token")

        user_id = UUID(payload.get("sub"))

        # Update user as verified
        await postgres_client.execute(
            "UPDATE users SET is_verified = TRUE WHERE user_id = $1",
            user_id
        )

        # Remove verification token from Redis
        await redis_client.delete(f"email_verification:{user_id}")

        logger.info(f"Email verified for user: {user_id}")

        return True

    async def _record_login_attempt(
        self,
        email: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        success: bool,
        failure_reason: Optional[str] = None
    ) -> None:
        """Record login attempt for security tracking."""
        attempt_id = uuid4()

        await postgres_client.execute(
            """
            INSERT INTO login_attempts (
                attempt_id, email, ip_address, user_agent, success, failure_reason
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            attempt_id, email, ip_address, user_agent, success, failure_reason
        )

    async def _create_session(
        self,
        user_id: UUID,
        access_token: str,
        refresh_token: str,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> UUID:
        """Create user session."""
        session_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(minutes=jwt_service.access_token_expire_minutes)

        await postgres_client.execute(
            """
            INSERT INTO sessions (
                session_id, user_id, access_token, refresh_token,
                expires_at, ip_address, user_agent
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            session_id, user_id, access_token, refresh_token,
            expires_at, ip_address, user_agent
        )

        # Cache session in Redis (expires with access token)
        await redis_client.set_json(
            f"session:{user_id}",
            {
                "session_id": str(session_id),
                "access_token": access_token,
                "user_id": str(user_id)
            },
            ex=jwt_service.access_token_expire_minutes * 60
        )

        return session_id


# Global instance
auth_service = AuthenticationService()
