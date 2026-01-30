"""
Google Authentication Service.
Handles OAuth2 flow using Authlib and Starlette.
"""

import logging
from typing import Optional, Dict, Any

from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.responses import RedirectResponse

try:
    from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
except ImportError:
    from .config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

# Configure module-level logger
logger = logging.getLogger(__name__)


class GoogleAuth:
    """
    Manages Google OAuth2 authentication.
    """

    def __init__(self, app: Optional[Any] = None) -> None:
        """
        Initialize the GoogleAuth service.

        Args:
            app: Optional Starlette/FastAPI application instance.
        """
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            raise RuntimeError("Google Client ID or Secret is missing in configuration.")

        # Correct Authlib OAuth setup
        self.oauth = OAuth()

        self.oauth.register(
            name="google",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={
                "scope": "openid email profile"
            },
        )

        logger.info("✅ GoogleAuth service initialized successfully")

    def get_oauth(self) -> OAuth:
        """
        Retrieve the OAuth instance.
        """
        return self.oauth

    async def login(self, request: Request, redirect_uri: str) -> RedirectResponse:
        """
        Start Google OAuth login flow.
        """
        return await self.oauth.google.authorize_redirect(
            request,
            redirect_uri
        )

    async def authorize(self, request: Request) -> Dict[str, Any]:
        """
        Handle Google OAuth callback and return user info.
        """
        token = await self.oauth.google.authorize_access_token(request)
        user = token.get("userinfo")

        if not user:
            logger.error("❌ Google OAuth failed: No user info received")
            return {}

        # Avoid logging PII in production
        logger.info("✅ User authenticated via Google OAuth")

        return user
