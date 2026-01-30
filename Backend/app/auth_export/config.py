"""
Configuration management for the Auth Export module.
Handles loading of secrets from keys/.env using python-dotenv.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure module-level logger
logger = logging.getLogger(__name__)

# Define paths
BASE_DIR = Path(__file__).parent.resolve()
KEYS_DIR = BASE_DIR / 'keys'
ENV_PATH = KEYS_DIR / '.env'

# Load environment variables explicitly from the keys/.env file
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
    logger.info(f"Loaded configuration from {ENV_PATH}")
else:
    logger.warning(f"Configuration file not found at {ENV_PATH}. Using environment variables or defaults.")

# ------------------------------------------------------------------------------
# Configuration Accessors
# ------------------------------------------------------------------------------

def _get_required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value

# Google Authentication
GOOGLE_CLIENT_ID: str = _get_required_env("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET: str = _get_required_env("GOOGLE_CLIENT_SECRET")

# Email Service
SMTP_USERNAME: str = _get_required_env("SMTP_USERNAME")
SMTP_PASSWORD: str = _get_required_env("SMTP_PASSWORD")
