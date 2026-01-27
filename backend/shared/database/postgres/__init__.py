"""
Database package for PostgreSQL setup and configuration.
Handles transactional data requiring strong consistency and ACID properties.

Unified Structure:
- config.py: Configuration and connection management
- models.py: SQLAlchemy models for all tables
- postgres_client.py: Unified client with all operations (RECOMMENDED)
"""
from .config import DatabaseConfig, db_config
from .models import (
    Base, User, RefreshToken, LoginAttempt, Conversation, UserSession, Notification, AuditLog,
    DocumentJob, ApiRateLimit, ChatFeedback, ChatMetric,
    ChatMessage
)
from .postgres_client import PostgresClient, get_postgres_client

__all__ = [
    # Configuration
    "DatabaseConfig",
    "db_config",

    # Models
    "Base",
    "User",
    "RefreshToken",
    "LoginAttempt",
    "Conversation",  # Unified conversation model (replaces ChatConversation)
    "UserSession",
    "Notification",
    "AuditLog",
    "DocumentJob",
    "ApiRateLimit",
    "ChatFeedback",
    "ChatMetric",
    "ChatMessage",

    # Client (recommended)
    "PostgresClient",
    "get_postgres_client",
]

