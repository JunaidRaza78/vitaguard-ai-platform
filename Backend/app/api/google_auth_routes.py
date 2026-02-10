"""
Google OAuth Routes
Handles Google Sign-In authentication
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
import logging

try:
    from app.auth_export.google_auth import GoogleAuth
    google_auth = GoogleAuth()
except Exception as e:
    google_auth = None
    logging.warning(f"Google Auth not available: {e}")

router = APIRouter(prefix="/api/v1/auth/google", tags=["Google OAuth"])

@router.get("/login")
async def google_login(request: Request):
    """
    Initiate Google OAuth login flow.
    Redirects user to Google's login page.
    """
    if not google_auth:
        raise HTTPException(status_code=503, detail="Google Auth not configured")

    redirect_uri = request.url_for("google_callback")
    return await google_auth.login(request, str(redirect_uri))


@router.get("/callback", name="google_callback")
async def google_callback(request: Request):
    """
    Handle Google OAuth callback.
    Google redirects here after user authenticates.
    """
    if not google_auth:
        raise HTTPException(status_code=503, detail="Google Auth not configured")

    try:
        user_info = await google_auth.authorize(request)

        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")

        # User info contains: email, name, picture, etc.
        return {
            "success": True,
            "message": "Google login successful",
            "user": {
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "email_verified": user_info.get("email_verified")
            }
        }

    except Exception as e:
        logging.error(f"Google callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def google_auth_status():
    """Check if Google OAuth is configured"""
    return {
        "google_auth_enabled": google_auth is not None,
        "login_url": "/api/v1/auth/google/login"
    }
