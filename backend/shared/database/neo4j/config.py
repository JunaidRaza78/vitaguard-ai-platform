"""
Neo4j configuration for graph database operations.
Handles relationships, knowledge graphs, and complex connections.
"""
import os
from pathlib import Path
from typing import Optional
from neo4j import GraphDatabase
import logging

# Initialize logger for Neo4j operations
logger = logging.getLogger('neo4j')

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    # Load .env file from project root (4 levels up: neo4j -> database -> shared -> backend -> root)
    env_path = Path(__file__).parent.parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.debug(f"Loaded .env file from {env_path}")
except ImportError:
    # python-dotenv not installed, skip loading .env file
    logger.warning("python-dotenv not installed, skipping .env file loading")
    pass


class Neo4jConfig:
    """Neo4j configuration and connection management."""

    def __init__(self):
        self.uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user: str = os.getenv("NEO4J_USER", "neo4j")
        self.password: str = os.getenv("NEO4J_PASSWORD", "neo4j")
        self.database: str = os.getenv("NEO4J_DATABASE", "neo4j")
        self.max_connection_lifetime: int = int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600"))
        self.max_connection_pool_size: int = int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50"))
        self.connection_acquisition_timeout: int = int(os.getenv("NEO4J_CONNECTION_ACQUISITION_TIMEOUT", "60"))

        logger.debug(f"Neo4j config initialized: URI={self.uri}, database={self.database}, pool_size={self.max_connection_pool_size}")

        # Driver instance
        self._driver: Optional[GraphDatabase.driver] = None

    def get_driver(self) -> GraphDatabase.driver:
        """
        Get Neo4j driver instance.

        Returns:
            Neo4j driver instance
        """
        if self._driver is None:
            logger.info(f"Creating Neo4j driver connection to {self.uri}")
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=self.max_connection_lifetime,
                max_connection_pool_size=self.max_connection_pool_size,
                connection_acquisition_timeout=self.connection_acquisition_timeout
            )
        return self._driver

    def verify_connectivity(self) -> bool:
        """Verify Neo4j connection."""
        try:
            logger.debug("Verifying Neo4j connectivity...")
            driver = self.get_driver()
            driver.verify_connectivity()
            logger.info("Neo4j health check: PASSED")
            return True
        except Exception as e:
            logger.error(f"Neo4j health check: FAILED - {type(e).__name__}: {str(e)}")
            return False

    def close(self):
        """Close Neo4j driver connection."""
        if self._driver:
            logger.info("Closing Neo4j driver connection")
            self._driver.close()
            self._driver = None


# Global Neo4j configuration instance
neo4j_config = Neo4jConfig()

