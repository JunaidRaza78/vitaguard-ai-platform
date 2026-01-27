"""
Database Clients Module
Centralized database access for the Family Health Manager
"""

from .postgres.postgres_client import PostgresClient, get_postgres_client
from .neo4j.neo4j_client import Neo4jClient
from .redis.redis_client import RedisClient

# Storage client - import only if needed (requires azure package)
try:
    from .storage_client import StorageClient
    storage_client = StorageClient()
except ImportError:
    StorageClient = None
    storage_client = None

# Create singleton instances for convenience
postgres_client = get_postgres_client()
neo4j_client = None  # Initialize when needed
redis_client = None  # Initialize when needed

# Helper functions
async def init_postgres(**config):
    """Initialize PostgreSQL client"""
    return postgres_client

async def close_postgres():
    """Close PostgreSQL connection"""
    await postgres_client.disconnect()

async def init_neo4j(**config):
    """Initialize Neo4j client"""
    global neo4j_client
    neo4j_client = Neo4jClient(**config)
    return neo4j_client

async def close_neo4j():
    """Close Neo4j connection"""
    if neo4j_client:
        await neo4j_client.close()

async def init_storage(**config):
    """Initialize storage client"""
    return storage_client

async def close_storage():
    """Close storage connection"""
    pass  # Storage client doesn't need explicit close

async def init_redis(**config):
    """Initialize Redis client"""
    global redis_client
    redis_client = RedisClient(**config)
    return redis_client

async def close_redis():
    """Close Redis connection"""
    if redis_client:
        await redis_client.close()

__all__ = [
    # PostgreSQL
    "PostgresClient",
    "postgres_client",
    "init_postgres",
    "close_postgres",
    # Neo4j
    "Neo4jClient",
    "neo4j_client",
    "init_neo4j",
    "close_neo4j",
    # Azure Storage (Buckets)
    "StorageClient",
    "storage_client",
    "init_storage",
    "close_storage",
    # Redis
    "RedisClient",
    "redis_client",
    "init_redis",
    "close_redis",
]


# Convenience function to initialize all databases
async def init_all_databases(config: dict) -> dict:
    """
    Initialize all database clients.

    Args:
        config: Configuration dictionary containing connection details

    Returns:
        Dictionary of initialized clients

    Example:
        config = {
            "postgres": {
                "host": "localhost",
                "port": 5432,
                "database": "health_manager",
                "user": "postgres",
                "password": "password"
            },
            "neo4j": {
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "password": "password",
                "database": "neo4j"
            },
            "storage": {
                "connection_string": "DefaultEndpointsProtocol=https;..."
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "password": None,
                "db": 0
            }
        }
        clients = await init_all_databases(config)
    """
    clients = {}

    if "postgres" in config:
        clients["postgres"] = await init_postgres(**config["postgres"])

    if "neo4j" in config:
        clients["neo4j"] = await init_neo4j(**config["neo4j"])

    if "storage" in config:
        clients["storage"] = await init_storage(**config["storage"])

    if "redis" in config:
        clients["redis"] = await init_redis(**config["redis"])

    return clients


async def close_all_databases() -> None:
    """
    Close all database connections.
    Should be called on application shutdown.
    """
    await close_postgres()
    await close_neo4j()
    await close_storage()
    await close_redis()


async def check_all_connections() -> dict:
    """
    Check health of all database connections.

    Returns:
        Dictionary with connection status for each database
    """
    return {
        "postgres": await postgres_client.check_connection(),
        "neo4j": await neo4j_client.check_connection(),
        "storage": await storage_client.check_connection(),
        "redis": await redis_client.check_connection(),
    }
