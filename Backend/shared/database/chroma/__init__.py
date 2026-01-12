"""
Chroma Vector Database Module
Medical knowledge embeddings and semantic search
"""

from .client import ChromaClient, get_client, get_chroma_client
from .config import chroma_config, ChromaConfig
from .embeddings import EmbeddingService, get_embedding_service
from .operations.vector_ops import VectorStoreOperations, get_vector_operations

__all__ = [
    # Client
    "ChromaClient",
    "get_client",
    "get_chroma_client",

    # Config
    "chroma_config",
    "ChromaConfig",

    # Embeddings
    "EmbeddingService",
    "get_embedding_service",

    # Operations
    "VectorStoreOperations",
    "get_vector_operations",
]
