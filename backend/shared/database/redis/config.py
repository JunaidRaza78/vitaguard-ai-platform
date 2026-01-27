"""
Redis configuration for cache and session store.
Provides in-memory speed, data structure support, and pub/sub capabilities.
"""
import os
from pathlib import Path
from typing import Optional
import redis
from redis import Redis, ConnectionPool
import logging

# Initialize logger
logger = logging.getLogger('redis.config')

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    # Load .env file from project root (4 levels up: redis -> database -> shared -> backend -> root)
    env_path = Path(__file__).parent.parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.debug(f"Loaded Redis environment variables from {env_path}")
except ImportError:
    # python-dotenv not installed, skip loading .env file
    logger.warning("python-dotenv not installed, skipping .env file loading")
    pass


class RedisConfig:
    """Redis configuration and connection management."""
    
    def __init__(self):
        self.host: str = os.getenv("REDIS_HOST", "localhost")
        self.port: int = int(os.getenv("REDIS_PORT", "6379"))
        self.password: Optional[str] = os.getenv("REDIS_PASSWORD", None)
        self.db: int = int(os.getenv("REDIS_DB", "0"))
        self.decode_responses: bool = os.getenv("REDIS_DECODE_RESPONSES", "true").lower() == "true"
        self.socket_timeout: int = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
        self.socket_connect_timeout: int = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5"))
        self.max_connections: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
        self.retry_on_timeout: bool = os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true"

        logger.debug(f"Redis configuration initialized: {self.host}:{self.port} (db={self.db})")

        # Connection pool
        self._pool: Optional[ConnectionPool] = None
    
    @property
    def connection_pool(self) -> ConnectionPool:
        """Get or create connection pool."""
        if self._pool is None:
            logger.debug(f"Creating Redis connection pool (max_connections={self.max_connections})")
            self._pool = ConnectionPool(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=self.decode_responses,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                max_connections=self.max_connections,
                retry_on_timeout=self.retry_on_timeout
            )
        return self._pool
    
    def get_client(self) -> Redis:
        """
        Get a Redis client instance.

        Returns:
            Redis client instance
        """
        logger.debug("Getting Redis client from connection pool")
        return Redis(connection_pool=self.connection_pool)
    
    def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            logger.debug("Performing Redis health check")
            client = self.get_client()
            client.ping()
            logger.info("Redis health check passed")
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {type(e).__name__}: {str(e)}")
            return False


# Global Redis configuration instance
redis_config = RedisConfig()

