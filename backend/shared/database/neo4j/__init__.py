"""
Neo4j package for graph database operations.
Handles relationships, knowledge graphs, and complex connections.

Unified Structure:
- config.py: Configuration and connection management
- neo4j_client.py: Unified client with all operations (RECOMMENDED)
- operations/: Domain-specific operation modules
  - graph_ops.py: Generic node/relationship operations
  - user_ops.py: User CRUD operations
  - family_ops.py: Family CRUD and relationship operations
"""
from backend.shared.database.neo4j.config import Neo4jConfig, neo4j_config
from backend.shared.database.neo4j.neo4j_client import Neo4jClient, get_neo4j_client

# Also export individual operation classes for advanced use cases
from backend.shared.database.neo4j.operations import (
    GraphOperations,
    UserOperations,
    FamilyOperations,
)

__all__ = [
    # Configuration
    "Neo4jConfig",
    "neo4j_config",

    # Main client (recommended)
    "Neo4jClient",
    "get_neo4j_client",

    # Individual operation classes (advanced)
    "GraphOperations",
    "UserOperations",
    "FamilyOperations",
]

