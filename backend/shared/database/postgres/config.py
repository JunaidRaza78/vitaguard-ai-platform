"""
Database configuration for PostgreSQL connection.
Handles transactional data requiring strong consistency and ACID properties.
"""
import os
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import logging

# Initialize logger
logger = logging.getLogger('postgres.config')

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    # Load .env file from project root (4 levels up: postgres -> database -> shared -> backend -> root)
    env_path = Path(__file__).parent.parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.debug(f"Loaded PostgreSQL environment variables from {env_path}")
except ImportError:
    # python-dotenv not installed, skip loading .env file
    logger.warning("python-dotenv not installed, skipping .env file loading")
    pass


class DatabaseConfig:
    """PostgreSQL database configuration and connection management."""

    def __init__(self):
        self.host: str = os.getenv("DB_HOST", "localhost")
        self.port: int = int(os.getenv("DB_PORT", "5432"))
        self.database: str = os.getenv("DB_NAME", "family_health_db")
        self.user: str = os.getenv("DB_USER", os.getenv("USER", "postgres"))  # Default to current system user
        self.password: str = os.getenv("DB_PASSWORD", "")
        self.pool_size: int = int(os.getenv("DB_POOL_SIZE", "5"))
        self.max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))

        # Singleton engine instance (CRITICAL FIX: reuse engine to prevent connection leaks)
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

        logger.debug(f"PostgreSQL configuration initialized: {self.host}:{self.port}/{self.database} (user={self.user})")
        
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )
    
    def create_engine(self, echo: bool = False) -> Engine:
        """
        Create SQLAlchemy engine with PostgreSQL-specific settings.

        Args:
            echo: If True, log all SQL statements (useful for debugging)

        Returns:
            SQLAlchemy Engine instance configured for PostgreSQL
        """
        logger.debug(f"Creating PostgreSQL engine (pool_size={self.pool_size}, max_overflow={self.max_overflow}, echo={echo})")
        engine = create_engine(
            self.database_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            echo=echo,
            # PostgreSQL-specific settings for ACID compliance
            isolation_level="READ COMMITTED",
            connect_args={
                "connect_timeout": 10,
                "application_name": "family_health_manager"
            }
        )
        logger.info(f"PostgreSQL engine created for {self.database}")
        return engine
    
    def get_engine(self) -> Engine:
        """
        Get or create the singleton engine instance.
        CRITICAL: Reuses the same engine to prevent connection pool exhaustion.
        """
        if self._engine is None:
            logger.debug("Creating singleton PostgreSQL engine")
            self._engine = self.create_engine()
        return self._engine

    def get_session_factory(self, engine: Optional[Engine] = None) -> sessionmaker:
        """
        Get or create session factory for database operations.

        Args:
            engine: Optional engine instance. If not provided, uses singleton engine.

        Returns:
            Session factory
        """
        if self._session_factory is None:
            logger.debug("Creating PostgreSQL session factory")
            eng = engine if engine is not None else self.get_engine()
            self._session_factory = sessionmaker(bind=eng, autocommit=False, autoflush=False)
        return self._session_factory

    def get_session(self, engine: Optional[Engine] = None) -> Session:
        """
        Get a database session from the singleton engine.

        Args:
            engine: Optional engine instance. If not provided, uses singleton engine.

        Returns:
            Database session
        """
        session_factory = self.get_session_factory(engine)
        return session_factory()

    def dispose_engine(self):
        """Dispose of the engine and close all connections (for cleanup)."""
        if self._engine is not None:
            logger.info("Disposing PostgreSQL engine and closing all connections")
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


# Global database configuration instance
db_config = DatabaseConfig()

