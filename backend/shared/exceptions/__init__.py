"""
Custom exceptions for the application.
"""


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class PostgreSQLError(DatabaseError):
    """Exception for PostgreSQL operations."""
    pass


class RedisError(DatabaseError):
    """Exception for Redis operations."""
    pass


class Neo4jError(DatabaseError):
    """Exception for Neo4j operations."""
    pass


class ConnectionError(DatabaseError):
    """Exception for database connection failures."""
    pass


class QueryError(DatabaseError):
    """Exception for query execution failures."""
    pass


class ValidationError(Exception):
    """Exception for data validation failures."""
    pass


class AuthenticationError(Exception):
    """Exception for authentication failures."""
    pass


class RateLimitError(Exception):
    """Exception for rate limit exceeded."""
    pass


class ConversationNotFoundError(DatabaseError):
    """Exception for conversation not found."""
    pass


class UserNotFoundError(DatabaseError):
    """Exception for user not found."""
    pass


__all__ = [
    "DatabaseError",
    "PostgreSQLError",
    "RedisError",
    "Neo4jError",
    "ConnectionError",
    "QueryError",
    "ValidationError",
    "AuthenticationError",
    "RateLimitError",
    "ConversationNotFoundError",
    "UserNotFoundError",
]
