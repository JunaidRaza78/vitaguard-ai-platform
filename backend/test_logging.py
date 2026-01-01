"""
Test script to verify logging system works with all databases.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.shared.logging import get_logger
from backend.shared.database.postgres import SimpleConversationClient
from backend.shared.database.redis import RedisClient
from backend.shared.database.neo4j import Neo4jClient

# Get logger
logger = get_logger('test')


def test_postgres_logging():
    """Test PostgreSQL client with logging."""
    logger.info("=" * 70)
    logger.info("Testing PostgreSQL Logging")
    logger.info("=" * 70)

    try:
        with SimpleConversationClient() as client:
            # Test health check
            health = client.health_check()
            logger.info(f"PostgreSQL health check result: {health}")

            if health:
                logger.info("✅ PostgreSQL logging working correctly!")
            else:
                logger.warning("⚠️  PostgreSQL connection failed, but logging is working")

    except Exception as e:
        logger.error(f"PostgreSQL test failed: {type(e).__name__}: {str(e)}", exc_info=True)


def test_redis_logging():
    """Test Redis client with logging."""
    logger.info("=" * 70)
    logger.info("Testing Redis Logging")
    logger.info("=" * 70)

    try:
        with RedisClient() as client:
            # Test cache operations
            test_key = "test:logging:key"
            test_value = {"message": "logging test", "timestamp": "2025-12-29"}

            # Set cache
            client.cache_set(test_key, test_value, ttl=60)
            logger.info(f"Set cache: {test_key}")

            # Get cache
            retrieved = client.cache_get(test_key)
            logger.info(f"Retrieved cache: {retrieved}")

            # Delete cache
            client.cache_delete(test_key)
            logger.info(f"Deleted cache: {test_key}")

            logger.info("✅ Redis logging working correctly!")

    except Exception as e:
        logger.error(f"Redis test failed: {type(e).__name__}: {str(e)}", exc_info=True)


def test_neo4j_logging():
    """Test Neo4j client with logging."""
    logger.info("=" * 70)
    logger.info("Testing Neo4j Logging")
    logger.info("=" * 70)

    try:
        client = Neo4jClient()
        health = client.health_check()
        logger.info(f"Neo4j health check result: {health}")

        if health:
            logger.info("✅ Neo4j logging working correctly!")
        else:
            logger.warning("⚠️  Neo4j connection failed, but logging is working")

    except Exception as e:
        logger.error(f"Neo4j test failed: {type(e).__name__}: {str(e)}", exc_info=True)


def main():
    """Run all logging tests."""
    logger.info("")
    logger.info("╔" + "═" * 68 + "╗")
    logger.info("║" + " " * 15 + "Database Logging System Test" + " " * 25 + "║")
    logger.info("╚" + "═" * 68 + "╝")
    logger.info("")

    # Test all databases
    test_postgres_logging()
    print()
    test_redis_logging()
    print()
    test_neo4j_logging()

    logger.info("")
    logger.info("=" * 70)
    logger.info("Logging Test Complete!")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Check the following log files:")
    logger.info("  - logs/debug.log       (All debug messages)")
    logger.info("  - logs/database.log    (Database operations)")
    logger.info("  - logs/error.log       (Errors and exceptions)")
    logger.info("  - logs/performance.log (Performance metrics)")
    logger.info("")


if __name__ == "__main__":
    main()
