"""
Authentication API Endpoints
REST API for user authentication and management
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from typing import Optional
import logging

from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    UserResponse,
    UserUpdate,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
    EmailVerification,
    MessageResponse
)
from app.services.auth_service import auth_service
from app.middleware.auth import get_current_user, get_current_active_user, get_current_verified_user
from app.middleware.rate_limit import RateLimiters
from shared.database import postgres_client

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()


# ==========================================
# REGISTRATION
# ==========================================

@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user account with email verification"
)
async def register(
    user_data: UserRegister,
    request: Request
):
    """
    Register a new user account.

    - **email**: Valid email address (will be verified)
    - **username**: Unique username (3-50 characters)
    - **password**: Strong password (min 8 chars, upper, lower, digit, special char)
    - **first_name**: User's first name (optional)
    - **last_name**: User's last name (optional)
    """
    # Apply rate limiting
    await RateLimiters.auth_limiter(request)

    try:
        ip_address = request.client.host if request.client else None

        user, verification_token = await auth_service.register_user(
            user_data,
            ip_address=ip_address
        )

        # Sync user to Neo4j graph database
        try:
            from shared.database.neo4j.operations.graph_ops import GraphOperations
            from datetime import datetime, timezone
            graph_ops = GraphOperations()
            graph_ops.create_node("User", {
                "userId": user.user_id,
                "email": user.email,
                "name": f"{user_data.first_name or ''} {user_data.last_name or ''}".strip() or user.username,
                "createdAt": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"User synced to Neo4j: {user.user_id}")
        except Exception as neo4j_err:
            logger.warning(f"Failed to sync user to Neo4j (non-critical): {neo4j_err}")

        # TODO: Send verification email with token
        # await email_service.send_verification_email(user.email, verification_token)

        logger.info(f"User registered successfully: {user.email}")

        return MessageResponse(
            message="Registration successful! Please check your email to verify your account.",
            success=True
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


# ==========================================
# LOGIN
# ==========================================

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user and receive JWT tokens"
)
async def login(
    login_data: UserLogin,
    request: Request
):
    """
    Authenticate user and return JWT tokens.

    - **email**: User's email address
    - **password**: User's password
    - **remember_me**: Extended session if True (90 days vs 30 days)

    Returns:
    - **access_token**: JWT token for API requests (30 min expiry)
    - **refresh_token**: Token for refreshing access token (30-90 days)
    - **user**: User profile information
    """
    # Apply rate limiting
    await RateLimiters.auth_limiter(request)

    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")

        token_response = await auth_service.login_user(
            login_data,
            ip_address=ip_address,
            user_agent=user_agent
        )

        if not token_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        return token_response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


# ==========================================
# TOKEN REFRESH
# ==========================================

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get a new access token using refresh token"
)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request
):
    """
    Refresh access token using refresh token.

    - **refresh_token**: Valid refresh token

    Returns new access_token and refresh_token (token rotation).
    """
    try:
        ip_address = request.client.host if request.client else None

        token_response = await auth_service.refresh_access_token(
            token_data.refresh_token,
            ip_address=ip_address
        )

        return token_response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


# ==========================================
# LOGOUT
# ==========================================

@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Logout user and revoke tokens"
)
async def logout(
    token_data: Optional[TokenRefresh] = None,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Logout user and revoke refresh token.

    Requires authentication (Bearer token in Authorization header).
    """
    try:
        refresh_token = token_data.refresh_token if token_data else None

        await auth_service.logout_user(
            current_user["user_id"],
            refresh_token=refresh_token
        )

        return MessageResponse(
            message="Logged out successfully",
            success=True
        )

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


# ==========================================
# EMAIL VERIFICATION
# ==========================================

@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email address",
    description="Verify user's email with verification token"
)
async def verify_email(verification: EmailVerification):
    """
    Verify user's email address.

    - **token**: Email verification token (sent via email)
    """
    try:
        await auth_service.verify_email(verification.token)

        return MessageResponse(
            message="Email verified successfully! You can now login.",
            success=True
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


# ==========================================
# USER PROFILE
# ==========================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get authenticated user's profile"
)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get current authenticated user's profile.

    Requires authentication (Bearer token in Authorization header).
    """
    return UserResponse(**current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update user profile",
    description="Update authenticated user's profile information"
)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update user profile.

    Only provided fields will be updated.
    Requires authentication.
    """
    try:
        # Build update query dynamically
        update_fields = []
        update_values = []
        param_count = 1

        for field, value in user_update.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = ${param_count}")
                update_values.append(value)
                param_count += 1

        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Add updated_at
        from datetime import datetime
        update_fields.append(f"updated_at = ${param_count}")
        update_values.append(datetime.utcnow())
        param_count += 1

        # Add user_id
        update_values.append(current_user["user_id"])

        query = f"""
            UPDATE users
            SET {', '.join(update_fields)}
            WHERE user_id = ${param_count}
            RETURNING *
        """

        updated_user = await postgres_client.fetchrow(query, *update_values)

        return UserResponse(**dict(updated_user))

    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change user's password (requires current password)"
)
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Change user's password.

    Requires:
    - Current password for verification
    - New password meeting strength requirements
    - Confirmation of new password
    """
    try:
        from app.auth.password import password_service
        from datetime import datetime

        # Verify current password
        user_record = await postgres_client.fetchrow(
            "SELECT password_hash FROM users WHERE user_id = $1",
            current_user["user_id"]
        )

        if not password_service.verify_password(
            password_data.current_password,
            user_record["password_hash"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Hash new password
        new_password_hash = password_service.hash_password(password_data.new_password)

        # Update password
        await postgres_client.execute(
            """
            UPDATE users
            SET password_hash = $1, password_changed_at = $2
            WHERE user_id = $3
            """,
            new_password_hash,
            datetime.utcnow(),
            current_user["user_id"]
        )

        # Revoke all refresh tokens (force re-login on all devices)
        await postgres_client.execute(
            """
            UPDATE refresh_tokens
            SET revoked = TRUE, revoked_at = $1
            WHERE user_id = $2
            """,
            datetime.utcnow(),
            current_user["user_id"]
        )

        logger.info(f"Password changed for user: {current_user['email']}")

        return MessageResponse(
            message="Password changed successfully. Please login again.",
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


# ==========================================
# PASSWORD RESET (TODO: Implement email sending)
# ==========================================

@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset",
    description="Request password reset link via email"
)
async def forgot_password(password_reset: PasswordReset):
    """
    Request password reset.

    Sends password reset link to user's email (if exists).
    Always returns success to prevent email enumeration.
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from pathlib import Path
        from dotenv import dotenv_values
        from shared.database.postgres.postgres_client import PostgresClient
        from app.auth.jwt import jwt_service

        # Get user from PostgreSQL — read attributes inside session context
        user_id_val = None
        user_email_val = None
        with PostgresClient() as db:
            user_obj = db.get_user_by_email(password_reset.email)
            if user_obj:
                user_id_val = str(user_obj.user_id)
                user_email_val = str(user_obj.email)

        if user_id_val and user_email_val:
            # Generate reset token
            reset_token = jwt_service.create_password_reset_token(
                user_id_val,
                user_email_val
            )

            # Send reset email via SMTP
            try:
                env_path = Path(__file__).parent.parent / "auth_export" / "keys" / ".env"
                smtp_cfg = dotenv_values(env_path)
                smtp_user = smtp_cfg.get("SMTP_USERNAME", "")
                smtp_pass = smtp_cfg.get("SMTP_PASSWORD", "")

                if smtp_user and smtp_pass:
                    reset_body = f"""
                    <html><body>
                    <h2>Password Reset Request</h2>
                    <p>You requested a password reset for your Family Health Manager account.</p>
                    <p>Use the token below to reset your password:</p>
                    <p style="background:#f0f0f0;padding:12px;font-family:monospace;word-break:break-all;">
                        {reset_token}
                    </p>
                    <p>Enter this token in the "Reset Password" section on the login page.</p>
                    <p>This token expires in 1 hour. If you did not request this, ignore this email.</p>
                    </body></html>
                    """
                    msg = MIMEText(reset_body, 'html')
                    msg['Subject'] = "Family Health Manager - Password Reset"
                    msg['From'] = smtp_user
                    msg['To'] = user_email_val
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as smtp:
                        smtp.login(smtp_user, smtp_pass)
                        smtp.sendmail(smtp_user, user_email_val, msg.as_string())
                    logger.info(f"Reset email sent to: {user_email_val}")
                else:
                    logger.warning("SMTP credentials not found, cannot send reset email")
            except Exception as email_err:
                logger.warning(f"Failed to send reset email: {email_err}")

            logger.info(f"Password reset requested for: {user_email_val}")

        # Always return success (prevent email enumeration)
        return MessageResponse(
            message="If the email exists, a password reset link has been sent.",
            success=True
        )

    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        # Still return success to prevent enumeration
        return MessageResponse(
            message="If the email exists, a password reset link has been sent.",
            success=True
        )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password",
    description="Reset password using reset token"
)
async def reset_password(reset_data: PasswordResetConfirm):
    """
    Reset password using reset token.

    - **token**: Password reset token (from email)
    - **new_password**: New password
    - **confirm_password**: Password confirmation
    """
    try:
        from app.auth.jwt import jwt_service
        from app.auth.password import password_service
        from shared.database.postgres.postgres_client import PostgresClient
        from datetime import datetime

        # Verify reset token
        payload = jwt_service.verify_password_reset_token(reset_data.token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        user_id = payload.get("sub")

        # Hash new password
        new_password_hash = password_service.hash_password(reset_data.new_password)

        now = datetime.utcnow()

        from sqlalchemy import text as sa_text
        with PostgresClient() as db:
            session = db.get_session()
            # Update password and reset lockout
            session.execute(
                sa_text("""
                UPDATE users
                SET password_hash = :pw_hash,
                    password_changed_at = :now,
                    failed_login_attempts = 0,
                    account_locked_until = NULL
                WHERE user_id = :user_id
                """),
                {"pw_hash": new_password_hash, "now": now, "user_id": user_id}
            )
            # Revoke all refresh tokens
            session.execute(
                sa_text("UPDATE refresh_tokens SET revoked = TRUE, revoked_at = :now WHERE user_id = :user_id"),
                {"now": now, "user_id": user_id}
            )

        logger.info(f"Password reset completed for user: {user_id}")

        return MessageResponse(
            message="Password reset successful. Please login with your new password.",
            success=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )
