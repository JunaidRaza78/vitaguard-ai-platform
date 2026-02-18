"""
Authentication Service
Handles user registration, login, and authentication business logic
Uses SQLAlchemy ORM for database operations
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import uuid4
import logging

from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.auth.password import password_service
from app.auth.jwt import jwt_service
from shared.database.postgres import PostgresClient, User, RefreshToken, LoginAttempt, UserSession

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Service for user authentication operations"""

    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_MINUTES = 30

    def __init__(self):
        self.db = PostgresClient()

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
        with self.db as db:
            session = db.get_session()

            # Check if email already exists
            existing_email = session.query(User).filter(User.email == user_data.email).first()
            if existing_email:
                raise ValueError("Email already registered")

            # Check if username already exists
            existing_username = session.query(User).filter(User.username == user_data.username).first()
            if existing_username:
                raise ValueError("Username already taken")

            # Hash password
            password_hash = password_service.hash_password(user_data.password)

            # Create user
            user_id = str(uuid4())
            now = datetime.now(timezone.utc)

            user = User(
                user_id=user_id,
                email=user_data.email,
                username=user_data.username,
                password_hash=password_hash,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                phone_number=user_data.phone_number,
                date_of_birth=user_data.date_of_birth,
                gender=user_data.gender,
                timezone=user_data.timezone or "UTC",
                language=user_data.language or "en",
                created_at=now,
                updated_at=now,
                is_active=True,
                is_verified=False,
                is_superuser=False,
                failed_login_attempts=0
            )

            session.add(user)
            session.commit()
            session.refresh(user)

            # Detach user from session to use outside context manager
            session.expunge(user)

            logger.info(f"User registered: {user.email} from IP {ip_address}")

        # Generate email verification token (outside context manager)
        verification_token = jwt_service.create_email_verification_token(
            user_id, user_data.email
        )

        # Store verification token in Redis if available
        try:
            from shared.database import redis_client
            if redis_client:
                await redis_client.set(
                    f"email_verification:{user_id}",
                    verification_token,
                    ex=86400
                )
        except Exception as e:
            logger.warning(f"Could not store verification token in Redis: {e}")

        # Create user node in Neo4j if available
        try:
            from shared.database import neo4j_client
            if neo4j_client:
                await neo4j_client.create_node(
                    "User",
                    {
                        "userId": user_id,
                        "email": user_data.email,
                        "username": user_data.username,
                        "createdAt": now.isoformat()
                    }
                )
        except Exception as e:
            logger.warning(f"Could not create user node in Neo4j: {e}")

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
        with self.db as db:
            session = db.get_session()

            # Get user from database
            user = session.query(User).filter(User.email == login_data.email).first()

            if not user:
                # Record failed login attempt
                await self._record_login_attempt(
                    email=login_data.email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    failure_reason="User not found"
                )
                raise ValueError("Invalid email or password")

            # Check if account is locked
            if user.account_locked_until and user.account_locked_until > datetime.now(timezone.utc):
                remaining = (user.account_locked_until - datetime.now(timezone.utc)).seconds // 60
                raise ValueError(f"Account is locked. Try again in {remaining} minutes.")

            # Check if account is active
            if not user.is_active:
                raise ValueError("Account is deactivated. Contact support.")

            # Verify password
            if not password_service.verify_password(login_data.password, user.password_hash):
                # Increment failed attempts
                user.failed_login_attempts += 1

                if user.failed_login_attempts >= self.MAX_LOGIN_ATTEMPTS:
                    # Lock account
                    user.account_locked_until = datetime.now(timezone.utc) + timedelta(minutes=self.ACCOUNT_LOCKOUT_MINUTES)
                    session.commit()

                    await self._record_login_attempt(
                        email=login_data.email,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        failure_reason="Account locked due to too many failed attempts",
                        user_id=user.user_id
                    )
                    raise ValueError(
                        f"Too many failed attempts. Account locked for {self.ACCOUNT_LOCKOUT_MINUTES} minutes."
                    )
                else:
                    session.commit()
                    remaining_attempts = self.MAX_LOGIN_ATTEMPTS - user.failed_login_attempts

                    await self._record_login_attempt(
                        email=login_data.email,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False,
                        failure_reason="Invalid password",
                        user_id=user.user_id
                    )
                    raise ValueError(
                        f"Invalid email or password. {remaining_attempts} attempts remaining."
                    )

            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.account_locked_until = None
            user.last_login = datetime.now(timezone.utc)
            session.commit()

            # Record successful login
            await self._record_login_attempt(
                email=login_data.email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
                user_id=user.user_id
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
            expires_at = datetime.now(timezone.utc) + timedelta(days=30 if not login_data.remember_me else 90)

            refresh_token_record = RefreshToken(
                token_id=str(uuid4()),
                user_id=user.user_id,
                token=refresh_token,
                expires_at=expires_at,
                device_info=user_agent,
                ip_address=ip_address
            )
            session.add(refresh_token_record)

            # Create session
            session_record = UserSession(
                session_id=str(uuid4()),
                user_id=user.user_id,
                token=access_token,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=jwt_service.access_token_expire_minutes),
                ip_address=ip_address,
                user_agent=user_agent
            )
            session.add(session_record)
            session.commit()

            logger.info(f"User logged in: {user.email} from IP {ip_address}")

            # Create response
            user_response = UserResponse(
                user_id=user.user_id,
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                last_login=user.last_login,
                timezone=user.timezone or "UTC",
                language=user.language or "en"
            )

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

        user_id = payload.get("sub")

        with self.db as db:
            session = db.get_session()

            # Check if refresh token exists and is not revoked
            token_record = session.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.token == refresh_token,
                RefreshToken.revoked == False
            ).first()

            if not token_record:
                raise ValueError("Refresh token not found or has been revoked")

            # Check if token has expired
            if token_record.expires_at < datetime.now(timezone.utc):
                raise ValueError("Refresh token has expired")

            # Get user
            user = session.query(User).filter(User.user_id == user_id).first()

            if not user:
                raise ValueError("User not found")

            # Create new access token
            access_token = jwt_service.create_access_token(
                user.user_id,
                user.email,
                user.username,
                user.is_superuser
            )

            # Rotate refresh token
            new_refresh_token = jwt_service.create_refresh_token(user.user_id)

            # Revoke old refresh token
            token_record.revoked = True
            token_record.revoked_at = datetime.now(timezone.utc)

            # Store new refresh token
            new_token_record = RefreshToken(
                token_id=str(uuid4()),
                user_id=user.user_id,
                token=new_refresh_token,
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                ip_address=ip_address
            )
            session.add(new_token_record)
            session.commit()

            user_response = UserResponse(
                user_id=user.user_id,
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                is_verified=user.is_verified,
                created_at=user.created_at,
                last_login=user.last_login,
                timezone=user.timezone or "UTC",
                language=user.language or "en"
            )

            return TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_in=jwt_service.access_token_expire_minutes * 60,
                user=user_response
            )

    async def logout_user(
        self,
        user_id: str,
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
        with self.db as db:
            session = db.get_session()

            # Revoke refresh token
            if refresh_token:
                token_record = session.query(RefreshToken).filter(
                    RefreshToken.user_id == user_id,
                    RefreshToken.token == refresh_token
                ).first()

                if token_record:
                    token_record.revoked = True
                    token_record.revoked_at = datetime.now(timezone.utc)

            # Deactivate sessions - UserSession doesn't have is_active, so we delete
            session.query(UserSession).filter(UserSession.user_id == user_id).delete()
            session.commit()

            # Clear session cache from Redis if available
            try:
                from shared.database import redis_client
                if redis_client:
                    await redis_client.delete(f"session:{user_id}")
            except Exception as e:
                logger.warning(f"Could not clear Redis session: {e}")

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

        user_id = payload.get("sub")

        with self.db as db:
            session = db.get_session()

            # Update user as verified
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                user.is_verified = True
                session.commit()

            # Remove verification token from Redis if available
            try:
                from shared.database import redis_client
                if redis_client:
                    await redis_client.delete(f"email_verification:{user_id}")
            except Exception as e:
                logger.warning(f"Could not delete Redis verification token: {e}")

            logger.info(f"Email verified for user: {user_id}")

            return True

    async def _record_login_attempt(
        self,
        email: str,
        ip_address: Optional[str],
        user_agent: Optional[str],
        success: bool,
        failure_reason: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Record login attempt for security tracking."""
        try:
            with PostgresClient() as db:
                session = db.get_session()

                attempt = LoginAttempt(
                    attempt_id=str(uuid4()),
                    user_id=user_id,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=success,
                    failure_reason=failure_reason,
                    attempted_at=datetime.now(timezone.utc)
                )
                session.add(attempt)
                session.commit()
        except Exception as e:
            logger.warning(f"Could not record login attempt: {e}")


# Global instance
auth_service = AuthenticationService()
