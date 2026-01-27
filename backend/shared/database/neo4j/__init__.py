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
from .config import Neo4jConfig, neo4j_config
from .neo4j_client import Neo4jClient

# Simple implementation of get_neo4j_client
def get_neo4j_client():
    return Neo4jClient()

# Simplified - skip advanced operations for now
GraphOperations = None
UserOperations = None
FamilyOperations = None

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

