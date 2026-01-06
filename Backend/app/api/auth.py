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
        # Get user
        user = await postgres_client.fetchrow(
            "SELECT user_id, email FROM users WHERE email = $1",
            password_reset.email
        )

        if user:
            # Generate reset token
            from app.auth.jwt import jwt_service
            reset_token = jwt_service.create_password_reset_token(
                user["user_id"],
                user["email"]
            )

            # TODO: Send reset email
            # await email_service.send_password_reset_email(user["email"], reset_token)

            logger.info(f"Password reset requested for: {user['email']}")

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

        # Update password
        await postgres_client.execute(
            """
            UPDATE users
            SET password_hash = $1,
                password_changed_at = $2,
                failed_login_attempts = 0,
                account_locked_until = NULL
            WHERE user_id = $3
            """,
            new_password_hash,
            datetime.utcnow(),
            user_id
        )

        # Revoke all refresh tokens
        await postgres_client.execute(
            "UPDATE refresh_tokens SET revoked = TRUE, revoked_at = $1 WHERE user_id = $2",
            datetime.utcnow(),
            user_id
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
